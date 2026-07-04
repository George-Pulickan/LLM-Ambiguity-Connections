"""Refresh the real NYT Connections dataset from the public archive.

Downloads the community-maintained NYT-Connections-Answers archive
(https://github.com/Eyefyre/NYT-Connections-Answers), writes it as
Real_Data_Ans.json, and regenerates Real_Data.json (puzzle boards: the 16
words of each puzzle, shuffled with a fixed seed for reproducibility).

Usage:
    python data/update_real_data.py
"""

import json
import random
import ssl
import urllib.request
from pathlib import Path

import certifi

URL = "https://raw.githubusercontent.com/Eyefyre/NYT-Connections-Answers/main/connections.json"
ROOT = Path(__file__).resolve().parent.parent
SEED = 42


def main():
    print(f"Downloading {URL} ...")
    ctx = ssl.create_default_context(cafile=certifi.where())
    with urllib.request.urlopen(URL, context=ctx) as r:
        answers = json.load(r)
    answers.sort(key=lambda p: p["id"])
    print(f"Fetched {len(answers)} puzzles "
          f"({answers[0]['date']} .. {answers[-1]['date']})")

    boards = {}
    rng = random.Random(SEED)
    for puzzle in answers:
        words = [w for ans in puzzle["answers"] for w in ans["members"]]
        rng.shuffle(words)
        boards[str(puzzle["id"])] = words

    (ROOT / "Real_Data_Ans.json").write_text(json.dumps(answers, indent=4))
    (ROOT / "Real_Data.json").write_text(json.dumps(boards, indent=4))
    print("Wrote Real_Data_Ans.json and Real_Data.json")


if __name__ == "__main__":
    main()
