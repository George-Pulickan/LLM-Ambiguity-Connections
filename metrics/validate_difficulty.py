"""Validate the embedding-similarity difficulty metric against official NYT levels.

Reviewer question (cmRe): "How accurate is the difficulty assessment method?"

The NYT assigns every Connections group an official difficulty level 0-3
(yellow=0 easiest ... purple=3 hardest). If mean intra-group embedding
similarity is a sound difficulty proxy, similarity should DECREASE as the
official level increases. This script measures:

  1. Spearman rank correlation between official level and group similarity
     (expected: negative).
  2. Mean similarity per official level.
  3. Within-puzzle pairwise ordering accuracy: for each pair of groups in the
     same puzzle with different official levels, how often does the metric
     rank them in the same order as the NYT?

Outputs results/metric_validation.json.

Usage:
    python metrics/validate_difficulty.py [--answers Real_Data_Ans.json]
"""

import argparse
import itertools
import json
from collections import defaultdict
from pathlib import Path

import numpy as np
from scipy import stats

from difficulty import DEFAULT_MODEL, batch_group_similarity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--answers", default="Real_Data_Ans.json")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--out", default="results/metric_validation.json")
    args = parser.parse_args()

    answers = json.load(open(args.answers))
    # The archive stopped recording official levels on 2025-09-20; those
    # groups carry level -1 and must be excluded from level-based validation.
    groups, levels, puzzle_ids = [], [], []
    skipped = 0
    for puzzle in answers:
        if any(ans["level"] not in (0, 1, 2, 3) for ans in puzzle["answers"]):
            skipped += 1
            continue
        for ans in puzzle["answers"]:
            groups.append(ans["members"])
            levels.append(ans["level"])
            puzzle_ids.append(puzzle["id"])
    if skipped:
        print(f"Excluded {skipped} puzzles without official difficulty labels")

    print(f"Scoring {len(groups)} groups from {len(answers)} puzzles with {args.model}...")
    sims = batch_group_similarity(groups, args.model)
    sims = np.array(sims)
    levels = np.array(levels)
    puzzle_ids = np.array(puzzle_ids)
    ok = ~np.isnan(sims)
    sims, levels, puzzle_ids = sims[ok], levels[ok], puzzle_ids[ok]

    rho, pval = stats.spearmanr(levels, sims)

    per_level = {
        int(lv): {
            "mean_similarity": float(np.mean(sims[levels == lv])),
            "std": float(np.std(sims[levels == lv])),
            "n": int(np.sum(levels == lv)),
        }
        for lv in sorted(set(levels.tolist()))
    }

    # Within-puzzle pairwise ordering accuracy
    by_puzzle = defaultdict(list)
    for pid, lv, s in zip(puzzle_ids, levels, sims):
        by_puzzle[int(pid)].append((int(lv), float(s)))
    correct = total = 0
    for entries in by_puzzle.values():
        for (l1, s1), (l2, s2) in itertools.combinations(entries, 2):
            if l1 == l2 or s1 == s2:
                continue
            total += 1
            # harder official level should have lower similarity
            if (l1 < l2) == (s1 > s2):
                correct += 1
    ordering_acc = correct / total if total else float("nan")

    results = {
        "model": args.model,
        "n_puzzles": len(by_puzzle),
        "n_groups": int(len(sims)),
        "spearman_rho": float(rho),
        "spearman_p": float(pval),
        "per_level": per_level,
        "pairwise_ordering_accuracy": ordering_acc,
        "pairwise_comparisons": total,
        "per_group_scores": [
            {"puzzle_id": int(p), "level": int(l), "similarity": float(s)}
            for p, l, s in zip(puzzle_ids, levels, sims)
        ],
    }

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2))

    print(f"\nSpearman rho(level, similarity) = {rho:.3f} (p = {pval:.2e})")
    for lv, d in per_level.items():
        print(f"  level {lv}: mean sim = {d['mean_similarity']:.4f} ± {d['std']:.4f} (n={d['n']})")
    print(f"Within-puzzle pairwise ordering accuracy: {ordering_acc:.3f} ({correct}/{total})")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
