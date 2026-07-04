"""Ambiguity metrics over the three-stage pipeline outputs.

For every generated group (stage 2 files, which contain the extracted word
lists and WordNet verification) compute:

  - mean WordNet sense count per word (single words only; phrases have no synsets)
  - ambiguous-word ratio: fraction of single words with >= 2 senses
  - highly-ambiguous ratio: fraction with >= 5 senses
  - phrase ratio: fraction of items that are multi-word (idiomatic candidates)
  - distribution of stage-2 ambiguity-type labels

Aggregated by group level 1-4 (the pipeline's least-to-most ambiguity ladder),
and compared against the real NYT groups from Real_Data_Ans.json.

Outputs results/ambiguity_metrics.json.

Usage:
    python metrics/ambiguity_metrics.py [--stage-dir data/gpt4o/json_files]
"""

import argparse
import json
from collections import Counter, defaultdict
from pathlib import Path

import nltk
import numpy as np
from nltk.corpus import wordnet as wn


def word_stats(words):
    """Sense-count statistics for a list of words/phrases."""
    sense_counts, phrases = [], 0
    for w in words:
        w = str(w).strip()
        if not w:
            continue
        if len(w.split()) > 1:
            phrases += 1
        else:
            sense_counts.append(len(wn.synsets(w)))
    n_single = len(sense_counts)
    n_total = n_single + phrases
    return {
        "mean_senses": float(np.mean(sense_counts)) if sense_counts else 0.0,
        "ambiguous_ratio": sum(c >= 2 for c in sense_counts) / n_single if n_single else 0.0,
        "highly_ambiguous_ratio": sum(c >= 5 for c in sense_counts) / n_single if n_single else 0.0,
        "phrase_ratio": phrases / n_total if n_total else 0.0,
        "n_single": n_single,
        "n_phrases": phrases,
    }


def aggregate(records):
    """Average a list of word_stats dicts, weighting words equally within keys."""
    if not records:
        return {}
    return {
        "mean_senses": float(np.mean([r["mean_senses"] for r in records if r["n_single"]])),
        "ambiguous_ratio": float(np.mean([r["ambiguous_ratio"] for r in records if r["n_single"]])),
        "highly_ambiguous_ratio": float(np.mean([r["highly_ambiguous_ratio"] for r in records if r["n_single"]])),
        "phrase_ratio": float(np.mean([r["phrase_ratio"] for r in records])),
        "n_groups": len(records),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage-dir", default="data/gpt4o/json_files")
    parser.add_argument("--answers", default="Real_Data_Ans.json")
    parser.add_argument("--out", default="results/ambiguity_metrics.json")
    args = parser.parse_args()

    nltk.download("wordnet", quiet=True)

    # --- Generated puzzles (stage 2 outputs) ---
    by_level = defaultdict(list)
    type_counts = defaultdict(Counter)
    stage2_files = sorted(Path(args.stage_dir).glob("puzzle_*_stage2_react_output.json"))
    for f in stage2_files:
        for group in json.load(open(f)):
            level = group["group_number"]
            by_level[level].append(word_stats(group["words"]))
            for v in group.get("verification", []):
                type_counts[level][v["ambiguity_type"]] += 1

    generated = {
        f"group_{lv}": {**aggregate(by_level[lv]), "ambiguity_type_counts": dict(type_counts[lv])}
        for lv in sorted(by_level)
    }

    # --- Real NYT groups, by official difficulty level ---
    answers = json.load(open(args.answers))
    real_by_level = defaultdict(list)
    for puzzle in answers:
        for ans in puzzle["answers"]:
            real_by_level[ans["level"]].append(word_stats(ans["members"]))
    real = {f"level_{lv}": aggregate(real_by_level[lv]) for lv in sorted(real_by_level)}

    all_gen = [r for recs in by_level.values() for r in recs]
    all_real = [r for recs in real_by_level.values() for r in recs]
    results = {
        "n_stage2_files": len(stage2_files),
        "generated_by_group_level": generated,
        "generated_overall": aggregate(all_gen),
        "real_nyt_by_level": real,
        "real_nyt_overall": aggregate(all_real),
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))

    print(f"Generated puzzles ({len(stage2_files)} stage-2 files):")
    for lv in sorted(by_level):
        a = aggregate(by_level[lv])
        print(f"  group {lv}: mean senses {a['mean_senses']:.2f}, ambiguous ratio {a['ambiguous_ratio']:.2f}, "
              f"phrase ratio {a['phrase_ratio']:.2f} (n={a['n_groups']})")
    print("Real NYT groups:")
    for lv in sorted(real_by_level):
        a = aggregate(real_by_level[lv])
        print(f"  level {lv}: mean senses {a['mean_senses']:.2f}, ambiguous ratio {a['ambiguous_ratio']:.2f} "
              f"(n={a['n_groups']})")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
