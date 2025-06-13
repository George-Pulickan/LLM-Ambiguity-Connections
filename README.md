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

## Running `code/main`

The primary script for generating puzzles is `code/main`. To run it:

1.  **Set your OpenAI API Key**: This script requires an OpenAI API key to function. Set it as an environment variable:
    ```bash
    export OPENAI_API_KEY='your_actual_api_key_here'
    ```
    Replace `'your_actual_api_key_here'` with your valid OpenAI API key.

2.  **Run the script**:
    ```bash
    python code/main
    ```
    The script will prompt you to enter the number of puzzles you wish to generate.

3.  **Dependencies**: Ensure you have `nltk` and `openai` installed in your Python environment. If not, you can typically install them using pip:
    ```bash
    pip install nltk openai
    ```
    The script will attempt to download the `wordnet` corpus from NLTK automatically upon first run.
