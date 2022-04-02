 # pylint: disable=import-error
import argparse
import json
import os

import numpy as np
import torch
from tqdm import tqdm

from torch.utils.data.dataloader import DataLoader
from torch.utils.data.distributed import DistributedSampler
from torch.utils.data.sampler import RandomSampler
from transformers.data.data_collator import default_data_collator
from transformers import AutoTokenizer, BertForMaskedLM, RobertaForMaskedLM

from adaptive_sampler import MaxTokensBatchSampler, data_collator_for_adaptive_sampler

# Debug: possible wrong imports
from data_processors.cord import CORDDataset
from data_processors.wiki import WikiDataset
from data_processors.SemEval2010 import SemEval2010Dataset
from data_processors.SemEval2013 import SemEval2013Dataset

REPS_DIR = 'replacements'

TOP_N_WORDS = 100 + 1 #removing identity replacement
PAD_ID = 0
dataset_params = {'cord': {'dataset_class': CORDDataset},
    'wiki': {'dataset_class': WikiDataset},
    'SemEval2010': {'dataset_class': SemEval2010Dataset}, # Should be write_specific_replacements as well
    'SemEval2013': {'dataset_class': SemEval2013Dataset}, # Should be write_specific_replacements as well
    }
model_params = {'bert-large-cased-whole-word-masking': {'model_class': BertForMaskedLM, 'model_hf_path': 'bert-large-cased-whole-word-masking'},
    'bert-large-uncased' : {'model_class': BertForMaskedLM, 'model_hf_path': 'bert-large-uncased'},
    'RoBERTa': {'model_class': RobertaForMaskedLM, 'model_hf_path': 'roberta-large'},
    'scibert': {'model_class': BertForMaskedLM, 'model_hf_path': 'allenai/scibert_scivocab_uncased'}}

def main(args):
    device = torch.device("cuda:0" if torch.cuda.is_available() and not args.cpu else "cpu")
    tokenizer, model = initialize_models(device, args)
    dataset_class = dataset_params[args.dataset]['dataset_class']

    i = 0
    files = read_files_with_conditions(args)
    for input_file in tqdm(files):
        dataset = dataset_class(args, input_file, tokenizer, cache_dir='/tmp/')
        dataloader = simple_dataloader(args, dataset) if args.simple_sampler else adaptive_dataloader(args, dataset)

        for inputs in tqdm(dataloader):
            with torch.no_grad():
                dict_to_device(inputs, device)
                doc_ids = inputs.pop('guid')
                last_hidden_states = model(**inputs)[0]
                normalized = last_hidden_states.softmax(-1)
                probs, indices = normalized.topk(TOP_N_WORDS)

                if args.write_specific_replacements:
                    write_specific_replacements_to_files(args.out_dir, doc_ids, inputs, indices, probs)
                else:
                    write_replacements_to_file(os.path.join(args.out_dir, REPS_DIR, f"{input_file.split('.')[0]}-{i}.npz"), doc_ids, inputs, indices, probs)
            i += 1

def read_files_with_conditions(args):
    def files_in_range(f, files_range):
        min_id, max_id = files_range.split('-')
        id = int(''.join(x for x in f if x.isdigit()))
        return int(min_id) <= id <= int(max_id)

    if args.no_input_file:
        return [args.dataset]

    files = os.listdir(args.data_dir)
    if args.starts_with:
        files = sorted([f for f in files if f.startswith(args.starts_with)])
    if args.files_range:
        files = sorted([f for f in files if files_in_range(f, args.files_range)])
    return files


def initialize_models(device, args):
    model_hf_path = model_params[args.model]['model_hf_path']
    model_class = model_params[args.model]['model_class']
    tokenizer = AutoTokenizer.from_pretrained(model_hf_path, use_fast=True)
    model = model_class.from_pretrained(model_hf_path)
    model.to(device)
    # Debug: stop using half-precision floats
    # if args.fp16:
    #     from apex import amp # pylint: disable=import-error
    #     model = amp.initialize(model, opt_level="O2")

    assert tokenizer.vocab_size < 65535 # Saving pred_ids as np.uint16
    return tokenizer, model

def adaptive_dataloader(args, dataset):
    sampler = MaxTokensBatchSampler(dataset, max_tokens=args.max_tokens_per_batch, padding_noise=0.0)
    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        sampler=sampler,
        collate_fn=data_collator_for_adaptive_sampler,
    )
    return dataloader

def simple_dataloader(args, dataset):
    sampler = (
        RandomSampler(dataset)
        if args.local_rank == -1
        else DistributedSampler(dataset)
    )

    dataloader = DataLoader(
        dataset,
        batch_size=args.batch_size,
        sampler=sampler,
        collate_fn=default_data_collator,
    )
    return dataloader

def write_specific_replacements_to_files(out_dir, doc_ids, inputs, replacements, probs):
    instance_id_to_target_pos = json.load(open(os.path.join(out_dir, "instance_id_to_target_pos.json"), 'r'))
    for doc_id, reps in zip(doc_ids, replacements):
        relevant_index = instance_id_to_target_pos[str(doc_id.item())]
        relevant_reps = reps[relevant_index][:TOP_N_WORDS-1]

        outfile = os.path.join(out_dir, REPS_DIR, f"{doc_id}-reps.npy")
        np.save(outfile, relevant_reps.cpu().numpy().astype(np.uint16))

def write_replacements_to_file(outfile, doc_ids, inputs, replacements, probs):
    attention_mask = inputs['attention_mask'].bool()

    sent_lengths = inputs['attention_mask'].sum(1)
    tokens = inputs['input_ids'].masked_select(attention_mask)
    replacements = replacements.masked_select(attention_mask.unsqueeze(2)).view(-1, TOP_N_WORDS)
    probs = probs.masked_select(attention_mask.unsqueeze(2)).view(-1, TOP_N_WORDS)

    identity_replacements = replacements == tokens.unsqueeze(1)
    has_identity_replacements = identity_replacements.sum(1) == 0
    identity_replacements[has_identity_replacements, TOP_N_WORDS-1] = True
    reps_without_identity = replacements.masked_select(~identity_replacements).view(-1, TOP_N_WORDS-1)
    probs_without_identity = probs.masked_select(~identity_replacements).view(-1, TOP_N_WORDS-1)
    normalized_probs_without_identity = probs_without_identity/probs_without_identity.sum(1).unsqueeze(1)

    np.save(f"{outfile}-tokens.npy", tokens.cpu().numpy().astype(np.uint16))
    np.save(f"{outfile}-lengths.npy", sent_lengths.cpu().numpy().astype(np.int16))
    np.save(f"{outfile}-reps.npy", reps_without_identity.cpu().numpy().astype(np.uint16))
    np.save(f"{outfile}-probs.npy", normalized_probs_without_identity.cpu().numpy().astype(np.float16))
    np.save(f"{outfile}-doc_ids.npy", doc_ids.cpu().numpy().astype(np.int32))

def dict_to_device(inputs, device):
    if device.type == 'cpu': return
    for k, v in inputs.items():
        if isinstance(v, torch.Tensor):
            inputs[k] = v.to(device)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("--data_dir", type=str, required=True)
    parser.add_argument("--starts_with", type=str)
    parser.add_argument("--files_range", type=str, help="should be splited with `-`")
    parser.add_argument("--out_dir", type=str, default="replacements")
    parser.add_argument("--dataset", type=str, required=True, choices=['cord', 'wiki', 'SemEval2010', 'SemEval2013'])
    parser.add_argument("--model", type=str, required=True, choices=['bert-large-cased-whole-word-masking', 'bert-large-uncased', 'RoBERTa', 'scibert'])
    parser.add_argument("--local_rank", type=int, default=-1, help="Not Maintained")
    parser.add_argument("--batch_size", type=int, default=1)
    parser.add_argument("--max_seq_length", type=int, default=512)
    parser.add_argument("--max_tokens_per_batch", type=int, default=-1)
    parser.add_argument("--no_input_file", action="store_true", help="Go over all files in one batch")
    parser.add_argument("--overwrite_cache", action="store_true")
    parser.add_argument("--simple_sampler", action="store_true")
    parser.add_argument("--cpu", action="store_true")
    parser.add_argument("--write_specific_replacements", action="store_true")
    parser.add_argument("--fp16", action="store_true")

    args = parser.parse_args()
    if args.simple_sampler:
        assert args.max_tokens_per_batch == -1 and \
            args.max_seq_length > -1, \
            "Expecting arguments for simple sampler"
    else:
        assert args.max_tokens_per_batch > 0 and \
            args.batch_size == 1 and \
            "Expecting arguments for adaptive sampler"

    if not os.path.exists(args.out_dir):
        os.makedirs(args.out_dir)
        os.makedirs(os.path.join(args.out_dir, REPS_DIR))

    main(args)