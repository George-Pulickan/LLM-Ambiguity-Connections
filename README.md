# Tracking and Amplifying Linguistic Ambiguity in LLM-Generated Connections Puzzles

This repository contains the code, data, and evaluation framework described in the paper:

**"Tracking and Amplifying Linguistic Ambiguity in LLM-Generated Connections Puzzles"**

We define a taxonomy of linguistic ambiguity (polysemy, homonymy, idiomatic, syntactic, figurative) and propose a three-stage pipeline leveraging Chain-of-Thought prompting and ReAct-based external validation to generate and evaluate puzzles.

## Features

- Taxonomy of ambiguity types
- Puzzle generation pipeline (Least-to-Most → ReAct → Reverse CoT)
- Automatic ambiguity metrics (sense count, ambiguous word ratio, stagewise growth)
- Prompt engineering for controlled ambiguity injection

## Code Structure

- `pipeline/` – Puzzle generation and validation pipeline (Python scripts)
- `data/` – Sample puzzles, ambiguity logs, WordNet outputs
- `prompts/` – Prompt templates for CoT, ReAct, RCoT
- `metrics/` – Evaluation scripts and metric computation
- `notebooks/` – Jupyter notebooks for analysis and visualization

## Example Output

- Puzzle with 4 groups, each with ambiguity annotations
- Chain of Thought trace with external validation log

## Citation

Coming soon (ACL submission)
