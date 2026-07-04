"""Three-stage ambiguity-amplifying Connections puzzle generator.

Stage 1: Least-to-Most CoT generation (4 groups, escalating ambiguity).
Stage 2: ReAct-style external validation against WordNet.
Stage 3: Reverse Chain-of-Thought (RCoT) audit of each group.

All prompts are loaded verbatim from the prompts/ directory so that the
exact text used in the paper is versioned and reproducible.

Usage:
    export OPENAI_API_KEY=sk-...
    python pipeline/generate_puzzles.py --num-puzzles 50 --out-dir data/gpt4o/json_files
"""

import argparse
import ast
import json
import os
import re
import time
from pathlib import Path

import nltk
from nltk.corpus import wordnet as wn
from openai import OpenAI

PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))


def load_prompt(name: str) -> str:
    return (PROMPTS_DIR / name).read_text().strip()


# --- Stage 1: Puzzle Generation with Least-to-Most Reasoning and Taxonomy ---

def build_prompt(level: int) -> str:
    return load_prompt(f"stage1_group{level}.txt")


def get_response(prompt: str, model: str, temperature: float = 0.7) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": load_prompt("stage1_system.txt")},
                {"role": "user", "content": prompt},
            ],
            temperature=temperature,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in API call: {e}")
        return ""


def extract_word_list_from_response(response_text: str) -> list:
    """Extracts the final 4-item word list, falling back to numbered lines."""
    match = re.search(r"\['.*?'\]", response_text, re.DOTALL)
    if match:
        try:
            return ast.literal_eval(match.group())
        except (ValueError, SyntaxError):
            print(f"Failed to parse word list from: {match.group()}")

    words = []
    for line in response_text.split("\n"):
        m = re.match(r"\d+\.\s*([^\s].*?)(?=\s*\-|\s*$)", line.strip())
        if m:
            word = m.group(1).strip().strip("\"'").replace("**", "")
            if word and len(word.split()) <= 3:
                words.append(word)
    return words[:4]


def extract_ambiguity_types(response: str) -> dict:
    """Heuristic extraction of per-word ambiguity-type labels from the CoT trace."""
    types = {}
    words = extract_word_list_from_response(response)
    response_lower = response.lower()
    for word in words:
        w = word.lower()
        if any(
            f"{t} for {w}" in response_lower or f"{w} is {t}" in response_lower or f"{w} ({t}" in response_lower
            for t in ["polysemy", "homonymy"]
        ):
            types[word] = "polysemy" if "polysemy" in response_lower else "homonymy"
        elif any(
            f"{t} for {w}" in response_lower or f"{w} is {t}" in response_lower or f"{w} ({t}" in response_lower
            for t in ["idiomatic", "syntactic", "figurative"]
        ):
            types[word] = next(t for t in ["idiomatic", "syntactic", "figurative"] if t in response_lower)
        else:
            types[word] = "unknown"
    return types


def generate_stage1_groups(puzzle_id: int, model: str, delay: float) -> list:
    results = []
    for level in range(1, 5):
        print(f"=== Generating Group {level} for Puzzle {puzzle_id} ===")
        prompt = build_prompt(level)
        reply = get_response(prompt, model)
        if reply:
            results.append({
                "group_number": level,
                "prompt": prompt,
                "response": reply,
                "ambiguity_types": extract_ambiguity_types(reply),
            })
        time.sleep(delay)
    return results


# --- Stage 2: WordNet Validation with Taxonomy ---

def get_wordnet_info(word: str) -> dict:
    if len(word.split()) > 1:
        return {
            "word": word,
            "sense_count": 0,
            "definitions": ["Idiomatic phrase, non-literal meaning"],
            "ambiguity_type": "idiomatic",
        }

    synsets = wn.synsets(word)
    senses = [syn.definition() for syn in synsets]
    ambiguity_type = "polysemy"
    if any("metaphor" in d.lower() or "figurative" in d.lower() for d in senses):
        ambiguity_type = "figurative"
    elif len(synsets) > 1 and len(set(s.pos() for s in synsets)) > 1:
        ambiguity_type = "homonymy"

    return {
        "word": word,
        "sense_count": len(senses),
        "definitions": senses[:5],
        "ambiguity_type": ambiguity_type,
    }


def run_stage2_on_groups(stage1_groups: list) -> list:
    results = []
    for group in stage1_groups:
        words = extract_word_list_from_response(group["response"])
        results.append({
            "group_number": group["group_number"],
            "words": words,
            "verification": [get_wordnet_info(w) for w in words],
        })
    return results


# --- Stage 3: Reverse Chain-of-Thought (RCoT) Verification ---

def build_rcot_prompt(word_list: list) -> str:
    return load_prompt("rcot_template.txt").format(word_list=word_list)


def ask_rcot(prompt: str, model: str) -> str:
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": load_prompt("rcot_system.txt")},
                {"role": "user", "content": prompt},
            ],
            temperature=0.5,
            max_tokens=800,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error in RCoT API call: {e}")
        return ""


def run_rcot_on_stage2(stage2_groups: list, puzzle_id: int, model: str, delay: float) -> list:
    results = []
    for group in stage2_groups:
        if not group["words"]:
            print(f"Skipping empty word list for group {group['group_number']}")
            continue
        prompt = build_rcot_prompt(group["words"])
        print(f"Verifying group {group['group_number']} with RCoT for Puzzle {puzzle_id}...")
        reply = ask_rcot(prompt, model)
        if reply:
            results.append({
                "group_number": group["group_number"],
                "words": group["words"],
                "prompt": prompt,
                "rcot_response": reply,
            })
        time.sleep(delay)
    return results


# --- Main Pipeline ---

def save_to_file(data, path: Path):
    path.write_text(json.dumps(data, indent=2))
    print(f"Saved results to {path}")


def generate_puzzles(num_puzzles: int, model: str, out_dir: Path, delay: float):
    out_dir.mkdir(parents=True, exist_ok=True)
    all_puzzles = []
    for puzzle_id in range(1, num_puzzles + 1):
        print(f"\n=== Processing Puzzle {puzzle_id} ===")

        stage1 = generate_stage1_groups(puzzle_id, model, delay)
        f1 = out_dir / f"puzzle_{puzzle_id}_stage1_output.json"
        save_to_file(stage1, f1)

        stage2 = run_stage2_on_groups(stage1)
        f2 = out_dir / f"puzzle_{puzzle_id}_stage2_react_output.json"
        save_to_file(stage2, f2)

        stage3 = run_rcot_on_stage2(stage2, puzzle_id, model, delay)
        f3 = out_dir / f"puzzle_{puzzle_id}_stage3_rcot_output.json"
        save_to_file(stage3, f3)

        all_puzzles.append({
            "puzzle_id": puzzle_id,
            "stage1_file": f1.name,
            "stage2_file": f2.name,
            "stage3_file": f3.name,
        })

    save_to_file(all_puzzles, out_dir / "all_puzzles_summary.json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--num-puzzles", type=int, default=10)
    parser.add_argument("--model", default="gpt-4o")
    parser.add_argument("--out-dir", type=Path, default=Path("data/generated"))
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds between API calls (rate limiting)")
    args = parser.parse_args()

    if not os.environ.get("OPENAI_API_KEY"):
        raise SystemExit("Set the OPENAI_API_KEY environment variable first.")

    nltk.download("wordnet", quiet=True)
    generate_puzzles(args.num_puzzles, args.model, args.out_dir, args.delay)
