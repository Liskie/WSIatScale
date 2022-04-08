CUDA_VISIBLE_DEVICES=6 python write_mask_preds/write_mask_preds.py \
    --data_dir /home/wyj2021/real/data/enwiki/small_text_json/AA/ \
    --starts_with wiki \
    --out_dir /home/wyj2021/real/projects/WSIatScale/datasets/processed_for_WSI/wiki/small_text/ \
    --dataset wiki \
    --max_tokens_per_batch 16384 \
    --files_range 00-99 \
    --model bert-large-cased-whole-word-masking

python WSIatScale/create_lemmatized_vocab.py \
    --model bert-large-cased-whole-word-masking \
    --outdir /home/wyj2021/real/projects/WSIatScale/WSIatScale/lemmatized_vocabs

python -m WSIatScale.create_inverted_index \
    --replacements_dir /home/wyj2021/real/projects/WSIatScale/datasets/processed_for_WSI/wiki/small_text/replacements/ \
    --outdir /home/wyj2021/real/projects/WSIatScale/datasets/processed_for_WSI/wiki/small_text/inverted_index/ \
    --dataset Wikipedia-BERT

python -m WSIatScale.cluster_reps_per_token \
    --data_dir /home/wyj2021/real/projects/WSIatScale/datasets/processed_for_WSI/wiki/small_text/ \
    --dataset Wikipedia-BERT

python -m WSIatScale.assign_clusters_to_tokens \
    --data_dir /home/wyj2021/real/projects/WSIatScale/datasets/processed_for_WSI/wiki/small_text/ \
    --dataset Wikipedia-BERT \
    --write_index_by_word  \
    --run_specific_method community_detection \
    --run_specific_n_reps 5

python -m WSIatScale.look_for_similar_communities \
    --data_dir /home/wyj2021/real/projects/WSIatScale/datasets/processed_for_WSI/wiki/small_text/ \
    --dataset Wikipedia-BERT
