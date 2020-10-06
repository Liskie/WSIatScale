# pylint: disable=no-member
import numpy as np
from collections import Counter, defaultdict

from scipy.cluster.hierarchy import linkage, fcluster
from scipy.spatial.distance import pdist, cdist

from sklearn import cluster as sk_cluster
from sklearn.feature_extraction import DictVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.metrics import pairwise_distances

from sklearn_extra.cluster import KMedoids

SEED = 111
class Jaccard:
    def __init__(self):
        self.matrix = None

    def init_matrix(self, length):
        self.matrix = np.zeros((length, length), dtype=np.float16)

    def pairwise_distance(self, X):
        length = len(X)
        self.init_matrix(length)
        for i in range(length):
            for j in range(i+1, length):
                distance = self.distance(X[i], X[j])
                self.matrix[i, j] = distance
                self.matrix[j, i] = distance

        return self.matrix

    def distance(self, x, y):
        return 1 - self.similarity(x, y)

    def similarity(self, x, y):
        x, y = set(x), set(y)
        intersection = len(x.intersection(y))
        union = len(x) + len(y) - intersection
        return float(intersection) / union

class ClusterFactory():
    @staticmethod
    def make(alg_name, *args, **kwargs):
        alg_name = alg_name.lower()
        if alg_name == 'kmeans': return MyKMeans(*args, **kwargs)
        if alg_name == 'kmedoids': return MyKMedoids(*args, **kwargs)
        if alg_name == 'agglomerative_clustering': return MyAgglomerativeClustering(*args, **kwargs)
        if alg_name == 'dbscan': return MyDBSCAN(*args, **kwargs)
        if alg_name == 'bow hierarchical': return MyBOWHierarchicalLinkage(*args, **kwargs)

    def reps_to_their_clusters(self, clusters, sorted_reps_to_instances_data):
        clustered_reps = {i: [] for i in self.clusters_range(clusters)}
        for c, rep_with_examples in zip(clusters, sorted_reps_to_instances_data):
            clustered_reps[c].append(rep_with_examples)

        return clustered_reps

    @staticmethod
    def group_for_display(args, tokenizer, clustered_reps, cluster_sents):
        show_top_n_clusters = args.show_top_n_clusters
        show_top_n_words_per_cluster = args.show_top_n_words_per_cluster
        sorted_zipped = sorted(zip(clustered_reps.values(), cluster_sents), key = lambda x: sum(len(reps['examples']) for reps in x[0]), reverse=True)

        sorted_clustered_reps, sorted_average_sents = zip(*sorted_zipped)
        top_clustered_reps = sorted_clustered_reps[:show_top_n_clusters]
        for i, cluster_reps in enumerate(top_clustered_reps):
            words_in_cluster = Counter()
            for reps in cluster_reps:
                for rep in reps['reps']:
                    words_in_cluster[rep] += len(reps['examples'])
            msg = {'header': f"Cluster {i}",
                   'found': f"Found total {sum(len(reps['examples']) for reps in cluster_reps)} matches"}
            words_in_cluster = words_in_cluster.most_common(show_top_n_words_per_cluster)
            words_in_cluster = [(tokenizer.decode([t]), c) for t, c in words_in_cluster]

            yield words_in_cluster, sorted_average_sents[i], msg

        if show_top_n_clusters < len(sorted_clustered_reps):
            msg = {'header': f"There are additional {len(sorted_clustered_reps) - show_top_n_clusters} that are not displayed.",
                   'found': ''}
            yield None, None, msg

class MyKMeans(sk_cluster.KMeans, ClusterFactory):
    def __init__(self, args):
        self.n_clusters = args.n_clusters
        super().__init__(n_clusters=self.n_clusters, random_state=SEED)

    def representative_sents(self, clusters, sorted_reps_to_instances_data, distance_matrix, n_sents_to_print):
        cluster_sents = [[] for _ in self.clusters_range(clusters)]
        closest_centers = np.argsort(pairwise_distances(self.cluster_centers_, distance_matrix))
        for i, closest_sents in enumerate(closest_centers):
            for c in closest_sents:
                if clusters[c] == i:
                    cluster_sents[i].append(sorted_reps_to_instances_data[c]['examples'][0])
                if len(cluster_sents[i]) == n_sents_to_print:
                    break
        return cluster_sents

    def clusters_range(self, clusters):
        return range(self.n_clusters)

    def fit_predict(self, X):
        X = 1 - X #Kmeans expects similarity and not distsance matrix
        return super().fit_predict(X)

class MyKMedoids(KMedoids, ClusterFactory):
    def __init__(self, args):
        self.n_clusters = args.n_clusters
        super().__init__(n_clusters=self.n_clusters, random_state=SEED)

    def representative_sents(self, clusters, sorted_reps_to_instances_data, distance_matrix, n_sents_to_print):
        cluster_sents = [[] for _ in self.clusters_range(clusters)]
        closest_centers = np.argsort(pairwise_distances(self.cluster_centers_, distance_matrix))
        for i, closest_sents in enumerate(closest_centers):
            for c in closest_sents:
                if clusters[c] == i:
                    cluster_sents[i].append(sorted_reps_to_instances_data[c]['examples'][0])
                if len(cluster_sents[i]) == n_sents_to_print:
                    break
        return cluster_sents

    def clusters_range(self, clusters):
        return range(self.n_clusters)

    def fit_predict(self, X):
        X = 1 - X
        return super().fit_predict(X)

class MyAgglomerativeClustering(sk_cluster.AgglomerativeClustering, ClusterFactory):
    def __init__(self, args):
        self.n_clusters = args.n_clusters
        self.affinity = args.affinity
        super().__init__(n_clusters=self.n_clusters,
                         distance_threshold=args.distance_threshold,
                         affinity=args.affinity,
                         linkage=args.linkage)

    def representative_sents(self, clusters, sorted_reps_to_instances_data, _, n_sents_to_print):
        cluster_sents = [[] for _ in self.clusters_range(clusters)]
        for i, c in enumerate(clusters):
            if len(cluster_sents[c]) == n_sents_to_print:
                continue
            cluster_sents[c].append(sorted_reps_to_instances_data[i]['examples'][0])

        return cluster_sents

    def clusters_range(self, clusters):
        return range(0, max(clusters)+1)

    def fit_predict(self, X):
        if self.affinity != 'precomputed':
            #"If "precomputed", a distance matrix (instead of a similarity matrix) is needed as input for the fit method."
            X = 1 - X
        return super().fit_predict(X)

class MyDBSCAN(sk_cluster.DBSCAN, ClusterFactory):
    def __init__(self, args):
        super().__init__(eps=args.eps, min_samples=args.min_samples)

    def representative_sents(self, clusters, sorted_reps_to_instances_data, _, n_sents_to_print):
        #TODO can I find a way to get the central ones!?
        cluster_sents = {i:[] for i in self.clusters_range(clusters)}
        for i, c in enumerate(clusters):
            if len(cluster_sents[c]) == n_sents_to_print:
                continue
            cluster_sents[c].append(sorted_reps_to_instances_data[i]['examples'][0])

        return cluster_sents

    def clusters_range(self, clusters):
        return range(min(clusters), max(clusters)+1)

    @staticmethod
    def group_for_display(args, tokenizer, clustered_reps, cluster_sents):
        num_classes_without_outliers = max(clustered_reps.keys()) + 1
        non_outlier_clustered_reps = {i: clustered_reps[i] for i in range(num_classes_without_outliers)}
        non_outlier_cluster_sents = [cluster_sents[i] for i in range(num_classes_without_outliers)]
        if len(non_outlier_clustered_reps) > 0:
            generator = ClusterFactory.group_for_display(args, tokenizer, non_outlier_clustered_reps, non_outlier_cluster_sents)
            for (words_in_cluster, sents, msg) in generator:
                yield (words_in_cluster, sents, msg)

        if -1 in clustered_reps:
            outlier_clustered_reps = {0: clustered_reps[-1]}
            outlier_cluster_sents = [cluster_sents[-1]]
            generator = ClusterFactory.group_for_display(args, tokenizer, outlier_clustered_reps, outlier_cluster_sents)

            for (words_in_cluster, sents, msg) in generator:
                msg['header'] = "Outliers Cluster"
                yield (words_in_cluster, sents, msg)

class MyBOWHierarchicalLinkage(ClusterFactory):
    #This can possibly have a rewrite. Too many loops.
    def __init__(self):
        self.use_tfidf = True
        self.metric = 'cosine'
        self.method = 'average'
        self.max_number_senses = 7
        self.min_sense_instances = 2

    def fit_predict(self, reps_and_instances):
        labels, doc_ids, rep_mat = self.get_initial_labels(reps_and_instances)
        n_senses = np.max(labels) + 1

        big_senses, doc_id_to_cluster = self.populate_doc_id_to_clusters(doc_ids, labels)

        sense_means = self.find_sense_means(n_senses, rep_mat, labels)

        sense_remapping, labels = self.merge_small_senses(sense_means, n_senses, big_senses, labels)

        senses = self.new_senses_mapping(doc_id_to_cluster, sense_remapping)
        return senses

    def get_initial_labels(self, reps_and_instances):
        reps_and_sent_data = [(reps_and_sents_data['reps'], sent_data) for reps_and_sents_data in reps_and_instances for sent_data in reps_and_sents_data['examples']]
        reps = [{r:1 for r in reps} for reps, _ in reps_and_sent_data]
        doc_ids = [sent_data.doc_id for _, sent_data in reps_and_sent_data]
        dict_vectorizer = DictVectorizer(sparse=False)
        rep_mat = dict_vectorizer.fit_transform(reps)
        if self.use_tfidf:
            rep_mat = TfidfTransformer(norm=None).fit_transform(rep_mat).todense()

        condensed_distance_mat = pdist(rep_mat, metric=self.metric)
        hierarchical_linkage = linkage(condensed_distance_mat, method=self.method, metric=self.metric)
        distance_threshold = hierarchical_linkage[-self.max_number_senses, 2]
        labels = fcluster(hierarchical_linkage, distance_threshold, 'distance') - 1
        return labels, doc_ids, rep_mat

    def merge_small_senses(self, sense_means, n_senses, big_senses, labels):
        if self.min_sense_instances > 0:
            sense_remapping = {}
            distance_mat = cdist(sense_means, sense_means, metric='cosine')
            closest_senses = np.argsort(distance_mat, )[:, ]

            for sense_idx in range(n_senses):
                for closest_sense in closest_senses[sense_idx]:
                    if closest_sense in big_senses:
                        sense_remapping[sense_idx] = closest_sense
                        break
            new_order_of_senses = list(set(sense_remapping.values()))
            sense_remapping = dict((k, new_order_of_senses.index(v)) for k, v in sense_remapping.items())

            labels = np.array([sense_remapping[x] for x in labels])
        return sense_remapping, labels

    def populate_doc_id_to_clusters(self, doc_ids, labels):
        senses_n_domminates = defaultdict(int)
        doc_id_to_cluster = {}
        for i, doc_id in enumerate(doc_ids):
            doc_id_clusters = labels[i]
            doc_id_to_cluster[doc_id] = doc_id_clusters
            senses_n_domminates[doc_id_clusters] += 1

        big_senses = [x for x in senses_n_domminates if senses_n_domminates[x] >= self.min_sense_instances]
        return big_senses, doc_id_to_cluster

    @staticmethod
    def new_senses_mapping(doc_id_to_cluster, sense_remapping):
        senses = {}
        for doc_id, sense_idx in doc_id_to_cluster.items():
            if sense_remapping:
                sense_idx = sense_remapping[sense_idx]
            senses[doc_id] = sense_idx
        return senses

    @staticmethod
    def find_sense_means(n_senses, transformed, labels):
        sense_means = np.zeros((n_senses, transformed.shape[1]))
        for sense_idx in range(n_senses):
            instances_in_sense = np.where(labels == sense_idx)
            cluster_center = np.mean(np.array(transformed)[instances_in_sense], 0)
            sense_means[sense_idx] = cluster_center
        return sense_means

# Deprecated
def cluster(args, reps_to_instances, tokenizer):
    sorted_reps_to_instances_data = [{'reps': k, 'examples': v} for k, v in sorted(reps_to_instances.data.items(), key=lambda kv: len(kv[1]), reverse=True)]
    jaccard_matrix = Jaccard().pairwise_distance([x['reps'] for x in sorted_reps_to_instances_data])

    clustering = ClusterFactory.make(args.cluster_alg, args)
    clusters = clustering.fit_predict(jaccard_matrix)

    clustered_reps = clustering.reps_to_their_clusters(clusters, sorted_reps_to_instances_data)

    representative_sents = clustering.representative_sents(clusters, sorted_reps_to_instances_data, jaccard_matrix, args.n_sents_to_print)
    clustering.group_for_display(args, tokenizer, clustered_reps, representative_sents)

# Deprecated
def cluster_words(args, reps_to_instances, tokenizer):
    sorted_reps_to_instances_data = [{'reps': k, 'examples': v} for k, v in sorted(reps_to_instances.data.items(), key=lambda kv: len(kv[1]), reverse=True)]
    jaccard_matrix = Jaccard().pairwise_distance([x['reps'] for x in sorted_reps_to_instances_data])

    clustering = ClusterFactory.make(args.cluster_alg, args)
    clusters = clustering.fit_predict(jaccard_matrix)

    clustered_reps = clustering.reps_to_their_clusters(clusters, sorted_reps_to_instances_data)

    representative_sents = clustering.representative_sents(clusters, sorted_reps_to_instances_data, jaccard_matrix, args.n_sents_to_print)
    clustering.group_for_display(args, tokenizer, clustered_reps, representative_sents)