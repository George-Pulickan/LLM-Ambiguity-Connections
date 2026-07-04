"""Solver evaluation harness: measure LLM solve rates on Connections puzzles.

Evaluates a chat model with one of three prompting strategies (direct, CoT,
ToT — prompts in prompts/solver_*.txt) on either real NYT puzzles
(Real_Data.json + Real_Data_Ans.json) or generated puzzles
(Training_Data.json / Testing_Data.json format).

Metrics per (model, strategy):
  - puzzle solve rate: all 4 groups exactly correct
  - group accuracy: fraction of the 4 groups correct (partial credit)
  - per-difficulty-level group accuracy (real puzzles only, NYT levels 0-3)

This regenerates the solve-rate tables of the paper from scratch with a fully
specified protocol. Requires OPENAI_API_KEY.

Usage:
    python experiments/solve_puzzles.py --dataset real --model gpt-4o --strategy cot --limit 100
    python experiments/solve_puzzles.py --dataset generated --file Testing_Data.json --strategy tot
"""

import argparse
import json
import os
import re
import time
from pathlib import Path

from openai import OpenAI

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def load_real(words_file, answers_file, limit=None):
    boards = json.load(open(words_file))
    answers = {str(a["id"]): a for a in json.load(open(answers_file))}
    puzzles = []
    for pid, words in boards.items():
        if pid not in answers:
            continue
        gold = {frozenset(w.upper() for w in ans["members"]): ans["level"]
                for ans in answers[pid]["answers"]}
        puzzles.append({"id": pid, "words": words, "gold": gold})
        if limit and len(puzzles) >= limit:
            break
    return puzzles


def load_generated(file, limit=None):
    puzzles = []
    for p in json.load(open(file)):
        groups = p.get("final_groups") or p.get("word_groups") or {}
        gold = {frozenset(str(w).upper() for w in words): None for words in groups.values()}
        words = p.get("final_puzzle") or [w for ws in groups.values() for w in ws]
        puzzles.append({"id": p.get("puzzle_id"), "words": words, "gold": gold})
        if limit and len(puzzles) >= limit:
            break
    return puzzles


def parse_solution(text):
    """Extract the last JSON object with a 'groups' key from the response."""
    candidates = re.findall(r"\{.*\}", text, re.DOTALL)
    for cand in reversed(candidates):
        try:
            obj = json.loads(cand)
            if "groups" in obj:
                return [frozenset(str(w).upper() for w in g.get("words", [])) for g in obj["groups"]]
        except json.JSONDecodeError:
            continue
    return []


def solve(puzzle, model, strategy, temperature):
    template = (PROMPTS_DIR / f"solver_{strategy}.txt").read_text()
    prompt = template.format(words=", ".join(str(w) for w in puzzle["words"]))
    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=2000,
    )
    return response.choices[0].message.content


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", choices=["real", "generated"], default="real")
    parser.add_argument("--file", default="Testing_Data.json", help="Puzzle file for --dataset generated")
    parser.add_argument("--words", default="Real_Data.json")
    parser.add_argument("--answers", default="Real_Data_Ans.json")
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--strategy", choices=["direct", "cot", "tot"], default="cot")
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--limit", type=int, default=None)
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--out-dir", default="results/solver")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set the OPENAI_API_KEY environment variable first.")

    if args.dataset == "real":
        puzzles = load_real(args.words, args.answers, args.limit)
    else:
        puzzles = load_generated(args.file, args.limit)

    records = []
    solved = 0
    group_correct = group_total = 0
    level_correct, level_total = {}, {}

    for i, puzzle in enumerate(puzzles):
        try:
            raw = solve(puzzle, args.model, args.strategy, args.temperature)
        except Exception as e:
            print(f"[{puzzle['id']}] API error: {e}")
            records.append({"id": puzzle["id"], "error": str(e)})
            time.sleep(args.delay)
            continue

        predicted = parse_solution(raw)
        gold = puzzle["gold"]
        hits = [g for g in predicted if g in gold]
        n_correct = len(set(hits))
        is_solved = n_correct == len(gold) == 4

        solved += is_solved
        group_correct += n_correct
        group_total += len(gold)
        for gset, level in gold.items():
            if level is None:
                continue
            level_total[level] = level_total.get(level, 0) + 1
            if gset in predicted:
                level_correct[level] = level_correct.get(level, 0) + 1

        records.append({
            "id": puzzle["id"],
            "solved": is_solved,
            "groups_correct": n_correct,
            "predicted": [sorted(g) for g in predicted],
            "raw_response": raw,
        })
        print(f"[{i+1}/{len(puzzles)}] puzzle {puzzle['id']}: {n_correct}/4 groups"
              + (" SOLVED" if is_solved else ""))
        time.sleep(args.delay)

    n = len([r for r in records if "error" not in r])
    summary = {
        "model": args.model,
        "strategy": args.strategy,
        "dataset": args.dataset if args.dataset == "real" else args.file,
        "temperature": args.temperature,
        "n_puzzles": n,
        "solve_rate": solved / n if n else None,
        "group_accuracy": group_correct / group_total if group_total else None,
        "per_level_accuracy": {
            str(lv): level_correct.get(lv, 0) / level_total[lv] for lv in sorted(level_total)
        },
    }

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    tag = f"{args.model}_{args.strategy}_{args.dataset}".replace("/", "-")
    (out_dir / f"{tag}_summary.json").write_text(json.dumps(summary, indent=2))
    (out_dir / f"{tag}_records.json").write_text(json.dumps(records, indent=2))
    print("\n" + json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
