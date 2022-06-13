# pylint: disable=no-name-in-module
# pylint: disable=import-error
import argparse
import os
import numpy as np
from functools import partial
from operator import itemgetter
from collections import defaultdict
from multiprocessing import Pool, cpu_count
from tqdm import tqdm

from transformers import AutoTokenizer

from WSIatScale.analyze import npy_file_path, REPS_DIR, RepInstances
from WSIatScale.cluster_reps_per_token import read_clustering_data
from utils.utils import tokenizer_params, jaccard_score_between_elements
from utils.special_tokens import SpecialTokens

SENTS_BY_CLUSTER = 'sents_by_cluster'
ALIGNED_SENSE_IDX_FOLDER = 'aligned_sense_idx'

TOP_REPS_TO_LOOK_ON = 10

def main(args):
    # THIS DOESN'T REQUIRE TO STORE THE SAME DATA IN TWO DIFFERET
    # STYLES LIKE I'M DOING, SHOULD BE CHANGED.
    model_hf_path = tokenizer_params[args.dataset]
    special_tokens = SpecialTokens(model_hf_path)
    replacements_dir = os.path.join(args.data_dir, REPS_DIR)

    files = data_files(replacements_dir)
    print(f"total {len(files)} files.")
    partial_find_and_write = partial(find_and_write,
        args=args,
        special_tokens=special_tokens,
        replacements_dir=replacements_dir)
    with Pool(cpu_count()) as p:
        list(tqdm(p.imap(partial_find_and_write, files), total=len(files)))

def find_and_write(filename, args, special_tokens, replacements_dir):
    if os.path.exists(os.path.join(args.data_dir, ALIGNED_SENSE_IDX_FOLDER, f"{filename}.npy")):
        return
    tokens_to_clusters, positions_to_clusters = find_clusters(os.path.join(replacements_dir, filename), args.data_dir, special_tokens, args.run_specific_method, args.run_specific_n_reps)
    if args.write_index_by_word:
        write_tokens_to_clusters(args.data_dir, filename, tokens_to_clusters)
    if args.write_aligned_sense_idx:
        write_positions_to_clusters(args.data_dir, filename, positions_to_clusters)

def data_files(replacements_dir):
    files = set()
    for file in os.listdir(replacements_dir):
        splits = file.split('-')
        files.add(f"{splits[0]}-{splits[1]}")
    
    return files

def find_clusters(filename, data_dir, special_tokens, run_specific_method, run_specific_n_reps):
    tokens_to_clusters = defaultdict(lambda: defaultdict(lambda: defaultdict(lambda: defaultdict(list))))
    positions_to_clusters = {}
    all_tokens = np.load(npy_file_path(data_dir, filename, 'tokens'), mmap_mode='r')
    all_reps = np.load(npy_file_path(data_dir, filename, 'reps'), mmap_mode='r')
    for pos, (token, token_reps) in enumerate(zip(all_tokens, all_reps)):
        positions_to_clusters[pos] = -1 #Assuming specific method and n_reps
        if special_tokens.valid_token(token) and next_token_validator(special_tokens, all_tokens, pos):
            lemmatized_token = special_tokens.lemmatize(token)
            if not special_tokens.valid_token(lemmatized_token): continue
            rep_inst = RepInstances(lemmatized_vocab=special_tokens.lemmatized_vocab)
            rep_inst.clean_and_populate_reps(reps=token_reps, special_tokens=special_tokens)
            rep_inst.populate_specific_size(TOP_REPS_TO_LOOK_ON)
            top_token_reps = rep_inst.data[0].reps
            clustering_data = read_clustering_data(data_dir, lemmatized_token)

            # Debug: ignore empty clustering data
            if not clustering_data:
                continue

            for method in clustering_data.keys():
                if not(run_specific_method is None or method == run_specific_method): continue
                for n_reps in clustering_data[method]:
                    if not(run_specific_n_reps is None or n_reps == run_specific_n_reps): continue
                    token_precomputed_clusters = clustering_data[method][n_reps]
                    jaccard_scores = []
                    for pre_computed_cluster in token_precomputed_clusters:
                        pre_computed_cluster_set = set([d[0] for d in pre_computed_cluster])
                        similarity = jaccard_score_between_elements(pre_computed_cluster_set, top_token_reps)
                        jaccard_scores.append(similarity)

                    if len(jaccard_scores) > 0:
                        cluster_id, best_jaccard_score = max(enumerate(jaccard_scores), key=itemgetter(1))
                        if best_jaccard_score > 0:
                            tokens_to_clusters[lemmatized_token][method][n_reps][cluster_id].append((pos, best_jaccard_score))
                            positions_to_clusters[pos] = cluster_id #Assuming specific method and n_reps

    return tokens_to_clusters, positions_to_clusters

def write_tokens_to_clusters(data_dir, reps_file, tokens_to_clusters):
    for token in tokens_to_clusters:
        for method in tokens_to_clusters[token]:
            for n_reps in tokens_to_clusters[token][method]:
                for cluster_id in tokens_to_clusters[token][method][n_reps]:
                    positions_and_confidence = tokens_to_clusters[token][method][n_reps][cluster_id]
                    token_cluster_file = os.path.join(data_dir, SENTS_BY_CLUSTER, f"{token}-{method}-{n_reps}.{cluster_id}")
                    with open(token_cluster_file, 'a+') as f:
                        stringed_positions_and_confidence = ' '.join([f"{p},{round(c, 2)}" for p, c in positions_and_confidence])
                        f.write(f"{reps_file}\t{stringed_positions_and_confidence}\n")

def write_positions_to_clusters(data_dir, filename, positions_to_clusters):
    outfile = os.path.join(data_dir, ALIGNED_SENSE_IDX_FOLDER, f"{filename}.txt")
    # numpied_positions_to_clusters = np.array(list(positions_to_clusters.values()))
    # np.save(outfile, numpied_positions_to_clusters)
    with open(outfile, 'w') as out:
        for key, value in positions_to_clusters.items():
            out.write(f'{key}: {value}\n')

def next_token_validator(special_tokens, tokens, pos):
    if pos + 1 == len(tokens):
        return True
    if tokens[pos + 1] in special_tokens.half_words_list:
        return False
    return True


if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--data_dir", type=str, default="replacements")
    parser.add_argument("--dataset", type=str, choices=['CORD-19', 'Wikipedia-roberta', 'Wikipedia-BERT', 'Wikipedia-ZH-BERT'])
    parser.add_argument("--write_index_by_word", action='store_true')
    parser.add_argument("--write_aligned_sense_idx", action='store_true')
    parser.add_argument("--run_specific_method", type=str, choices=['community_detection', 'clustering'], help="Only if we want specific method")
    parser.add_argument("--run_specific_n_reps", type=str, choices=['5', '20', '50'], help="Only if we want specific n_reps")
    args = parser.parse_args()

    assert args.write_index_by_word != args.write_aligned_sense_idx, "Choose one of --write_index_by_word --write_aligned_sense_idx"

    if args.write_index_by_word:
        outdir = os.path.join(args.data_dir, SENTS_BY_CLUSTER)
        assert len(os.listdir(outdir)) == 0, f"Sents by cluster already available, should delete first {outdir}"
    else:
        outdir = os.path.join(args.data_dir, ALIGNED_SENSE_IDX_FOLDER)
        assert os.path.isdir(outdir), f"{outdir} needs to be created first"



    main(args)