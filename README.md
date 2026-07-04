# Tracking and Amplifying Linguistic Ambiguity in LLM-Generated Connections Puzzles

This repository contains the code, data, and evaluation framework described in the paper:

**"Tracking and Amplifying Linguistic Ambiguity in LLM-Generated Connections Puzzles"**

We define a taxonomy of linguistic ambiguity and propose a three-stage pipeline that leverages Chain-of-Thought (CoT) prompting and ReAct-based external validation to generate NYT Connections-style puzzles with deliberately amplified ambiguity. We then evaluate how well LLMs solve these puzzles by fine-tuning Llama models on real, synthetic, and mixed datasets.

## Ambiguity Taxonomy

Puzzle groups are constructed and annotated according to five types of linguistic ambiguity:

| Type | Description | Example |
|------|-------------|---------|
| **Polysemy** | One word with multiple *related* senses | "bank" (riverbank / financial institution) |
| **Homonymy** | Same spelling/pronunciation, *distinct* meanings | "bat" (animal / sports equipment) |
| **Idiomatic** | Phrases with non-literal meanings | "break the ice" |
| **Syntactic** | Words that create ambiguous sentence structures | "saw" in "he saw the man with a telescope" |
| **Figurative** | Metaphorical meanings | "light" (brightness / hope) |

## Puzzle Generation Pipeline

The full pipeline lives in [`code/main`](code/main) and runs against the OpenAI API (GPT-4o). Each generated puzzle contains 4 groups of 4 words, with ambiguity increasing group by group:

### Stage 1 — Least-to-Most Generation with CoT
- **Group 1:** a clearly defined semantic category (e.g., colors)
- **Group 2:** slightly overlapping or flexible meanings (e.g., tools)
- **Group 3:** polysemous or homonymous words
- **Group 4:** idiomatic, syntactic, or figurative ambiguity

The model explains its reasoning step by step and labels each word with its ambiguity type. A heuristic parser (`extract_ambiguity_types`) extracts those labels from the CoT trace, and `extract_word_list_from_response` recovers the final 4-word Python list (with a regex + numbered-line fallback).

Output: `puzzle_<id>_stage1_output.json`

### Stage 2 — ReAct-Style External Validation with WordNet
Each word is validated against **NLTK WordNet**:
- **Sense count** (number of synsets) and up to 5 definitions per word
- Automatic ambiguity-type classification: multi-word phrases → *idiomatic*; definitions mentioning metaphor → *figurative*; multiple synsets across parts of speech → *homonymy*; otherwise *polysemy*

Output: `puzzle_<id>_stage2_react_output.json`

### Stage 3 — Reverse Chain-of-Thought (RCoT) Verification
GPT-4o acts as a *puzzle auditor*: given only the final word list, it must justify why each word belongs in the group and identify its ambiguity type, verifying the group holds up without access to the original reasoning.

Output: `puzzle_<id>_stage3_rcot_output.json` and an `all_puzzles_summary.json` index.

### Running the pipeline

```bash
pip install openai nltk
python code/main
```

You will need to:
1. Set your OpenAI API key in the `OpenAI(api_key="")` call at the top of `code/main`.
2. Enter the number of puzzles to generate when prompted (defaults to 10 on invalid input).

WordNet is downloaded automatically via `nltk.download('wordnet')`. A 2-second delay between API calls guards against rate limits.

## Solver Evaluation: Fine-Tuning Llama

Three Colab notebooks fine-tune Llama-family models (via Hugging Face `transformers` + `datasets`) to *solve* Connections puzzles under different training-data conditions:

| Notebook | Training data |
|----------|---------------|
| `Llama Model(Real Data Set).ipynb` | Real NYT Connections puzzles (`Real_Data.json` + `Real_Data_Ans.json`) |
| `Llama Model(Synthetic Data Set)` | Synthetic GPT-4o-generated puzzles (`Training_Data.json`) |
| `Llama Model(Mixed Dataset)` | A mix of real and synthetic puzzles |

> Note: the Synthetic and Mixed notebooks are Jupyter notebooks stored without the `.ipynb` extension; rename them to open in Jupyter/Colab.

Puzzles and answers are converted into instruction–response pairs (16 shuffled words in, 4 labeled groups out) and split into train/test sets with scikit-learn.

## Repository Layout

```
├── code/
│   └── main                          # Three-stage generation pipeline (Python)
├── data/
│   └── gpt4o/
│       └── json_files.zip            # Pipeline outputs for a 50-puzzle GPT-4o run
│                                     # (stage1 / stage2_react / stage3_rcot per puzzle)
├── Real_Data.json                    # Real NYT Connections boards (16 words per puzzle)
├── Real_Data_Ans.json                # Real puzzle solutions (groups with difficulty levels)
├── Training_Data.json                # Synthetic puzzles with word groups + final boards
├── Testing_Data.json                 # Held-out synthetic evaluation puzzles
├── Llama Model(Real Data Set).ipynb  # Fine-tuning on real data
├── Llama Model(Synthetic Data Set)   # Fine-tuning on synthetic data (notebook)
├── Llama Model(Mixed Dataset)        # Fine-tuning on mixed data (notebook)
└── LICENSE
```

## Data Formats

**`Real_Data.json`** — maps puzzle ID → flat list of 16 words:

```json
{ "1": ["RACECAR", "OPTION", "TAB", "JAZZ", ...] }
```

**`Real_Data_Ans.json`** — list of solutions with per-group difficulty levels (0 = easiest, 3 = hardest):

```json
{
  "id": 1,
  "date": "2023-06-12",
  "answers": [
    { "level": 0, "group": "WET WEATHER", "members": ["HAIL", "RAIN", "SLEET", "SNOW"] }
  ]
}
```

**`Training_Data.json` / `Testing_Data.json`** — synthetic puzzles with named word groups, the shuffled 16-word board, and the final grouping:

```json
{
  "puzzle_id": 1,
  "word_groups": { "2. Words with Double Meanings": ["Bark", "Jam", "Pitch", "Ring"] },
  "final_puzzle": ["Cornfield", "Labyrinth", ...],
  "final_groups": { ... }
}
```

## Ambiguity Metrics

The pipeline tracks ambiguity through three automatic signals:

- **Sense count** — WordNet synsets per word (Stage 2)
- **Ambiguous word ratio** — share of words in a group with more than one sense
- **Stagewise growth** — how ambiguity annotations evolve from Stage 1 generation through Stage 3 verification

## Citation

Coming soon (ACL submission).

## License

See [LICENSE](LICENSE).
