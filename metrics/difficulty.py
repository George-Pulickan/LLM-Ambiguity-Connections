"""Embedding-based difficulty scoring for Connections-style word groups.

Difficulty proxy: mean pairwise cosine similarity of the words in a group,
computed with a SentenceTransformer (default: all-mpnet-base-v2, as in the
paper). LOWER similarity = semantically more diverse group = HARDER.

This module is imported by validate_difficulty.py and compare_datasets.py;
it can also score an arbitrary JSON dataset from the command line.
"""

import argparse
import itertools
import json
from functools import lru_cache

import numpy as np

DEFAULT_MODEL = "all-mpnet-base-v2"


@lru_cache(maxsize=2)
def _get_model(name: str = DEFAULT_MODEL):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(name)


def group_similarity(words, model_name: str = DEFAULT_MODEL) -> float:
    """Mean pairwise cosine similarity across all distinct word pairs."""
    words = [str(w) for w in words if str(w).strip()]
    if len(words) < 2:
        return float("nan")
    emb = _get_model(model_name).encode(words, normalize_embeddings=True)
    sims = [float(np.dot(emb[i], emb[j])) for i, j in itertools.combinations(range(len(emb)), 2)]
    return float(np.mean(sims))


def batch_group_similarity(groups, model_name: str = DEFAULT_MODEL):
    """Score many groups with one encode() call. groups: list[list[str]]."""
    flat, offsets = [], []
    for g in groups:
        ws = [str(w) for w in g if str(w).strip()]
        offsets.append((len(flat), len(ws)))
        flat.extend(ws)
    emb = _get_model(model_name).encode(flat, normalize_embeddings=True, show_progress_bar=False)
    scores = []
    for start, n in offsets:
        if n < 2:
            scores.append(float("nan"))
            continue
        e = emb[start:start + n]
        sims = [float(np.dot(e[i], e[j])) for i, j in itertools.combinations(range(n), 2)]
        scores.append(float(np.mean(sims)))
    return scores


def puzzle_difficulty(group_scores) -> float:
    """Puzzle-level score = mean of its group scores (ignoring NaNs)."""
    arr = np.array(group_scores, dtype=float)
    return float(np.nanmean(arr)) if len(arr) else float("nan")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("json_file", help="JSON file: list of puzzles with 'final_groups' (Training_Data.json format)")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    args = parser.parse_args()

    puzzles = json.load(open(args.json_file))
    all_groups, index = [], []
    for p in puzzles:
        for name, words in p.get("final_groups", p.get("word_groups", {})).items():
            all_groups.append(words)
            index.append((p.get("puzzle_id"), name))

    scores = batch_group_similarity(all_groups, args.model)
    for (pid, name), s in zip(index, scores):
        print(f"puzzle {pid}\t{name}\t{s:.4f}")
    print(f"\nOverall mean group similarity: {np.nanmean(scores):.4f}")
