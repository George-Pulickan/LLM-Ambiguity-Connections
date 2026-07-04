"""Compare intra-group semantic similarity: real NYT vs LLM-generated puzzles.

Replaces the unsourced difficulty numbers in the original draft with fully
reproducible statistics computed from the datasets in this repository:

  - Real NYT groups (Real_Data_Ans.json)
  - GPT-4o synthetic training puzzles (Training_Data.json, final_groups)
  - Three-stage ambiguity pipeline outputs (data/gpt4o/json_files, stage 2)

Reports mean/std of group similarity per source plus a Mann-Whitney U test
between real and each generated source. Outputs results/dataset_comparison.json.

Usage:
    python metrics/compare_datasets.py
"""

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import stats

from difficulty import DEFAULT_MODEL, batch_group_similarity


def collect_real(answers_file):
    groups = []
    for puzzle in json.load(open(answers_file)):
        for ans in puzzle["answers"]:
            groups.append(ans["members"])
    return groups


def collect_synthetic(training_file):
    groups = []
    for p in json.load(open(training_file)):
        for words in p.get("final_groups", {}).values():
            groups.append(words)
    return groups


def collect_pipeline(stage_dir):
    groups = []
    for f in sorted(Path(stage_dir).glob("puzzle_*_stage2_react_output.json")):
        for g in json.load(open(f)):
            if len(g["words"]) >= 2:
                groups.append(g["words"])
    return groups


def summarize(scores):
    arr = np.array([s for s in scores if not np.isnan(s)])
    return {
        "n_groups": int(len(arr)),
        "mean_similarity": float(arr.mean()),
        "std": float(arr.std()),
        "median": float(np.median(arr)),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", default="Real_Data_Ans.json")
    parser.add_argument("--training", default="Training_Data.json")
    parser.add_argument("--stage-dir", default="data/gpt4o/json_files")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", default="results/dataset_comparison.json")
    args = parser.parse_args()

    sources = {
        "real_nyt": collect_real(args.answers),
        "gpt4o_synthetic": collect_synthetic(args.training),
        "ambiguity_pipeline": collect_pipeline(args.stage_dir),
    }

    results, raw = {}, {}
    for name, groups in sources.items():
        print(f"Scoring {len(groups)} groups from {name}...")
        raw[name] = batch_group_similarity(groups, args.model)
        results[name] = summarize(raw[name])

    real = np.array([s for s in raw["real_nyt"] if not np.isnan(s)])
    for name in ("gpt4o_synthetic", "ambiguity_pipeline"):
        gen = np.array([s for s in raw[name] if not np.isnan(s)])
        u, p = stats.mannwhitneyu(real, gen, alternative="two-sided")
        results[name]["mannwhitney_u_vs_real"] = float(u)
        results[name]["mannwhitney_p_vs_real"] = float(p)

    results["model"] = args.model
    results["raw_scores"] = {k: [None if np.isnan(s) else round(float(s), 6) for s in v] for k, v in raw.items()}

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))

    for name in sources:
        r = results[name]
        print(f"{name}: mean {r['mean_similarity']:.4f} ± {r['std']:.4f} (n={r['n_groups']})")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
