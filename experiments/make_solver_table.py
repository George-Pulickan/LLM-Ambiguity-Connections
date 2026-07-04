"""Build the paper's solver-results LaTeX table from results/solver/*_summary.json.

Run after completing the solver runs described in experiments/README.md:

    python experiments/make_solver_table.py > paper/solver_table.tex

Rows are grouped by model, columns by strategy; each cell shows puzzle solve
rate with its 95% Wilson CI. Paste or \\input{} the output into paper/main.tex.
"""

import json
from collections import defaultdict
from pathlib import Path

RESULTS = Path(__file__).resolve().parent.parent / "results" / "solver"
STRATEGIES = ["direct", "cot", "tot"]


def fmt(summary):
    if not summary:
        return "---"
    sr = summary["solve_rate"]
    lo, hi = summary.get("solve_rate_ci95", (None, None))
    if sr is None:
        return "---"
    if lo is None:
        return f"{sr:.1%}".replace("%", r"\%")
    return (f"{sr:.1%} [{lo:.1%}, {hi:.1%}]").replace("%", r"\%")


def main():
    by_model = defaultdict(dict)
    n_by_model = {}
    for f in sorted(RESULTS.glob("*_summary.json")):
        s = json.loads(f.read_text())
        by_model[s["model"]][s["strategy"]] = s
        n_by_model[s["model"]] = s["n_puzzles"]

    if not by_model:
        raise SystemExit(f"No summaries found in {RESULTS}. Run experiments/solve_puzzles.py first.")

    print(r"\begin{table*}[t]")
    print(r"\centering\small")
    print(r"\begin{tabular}{l" + "c" * len(STRATEGIES) + "c}")
    print(r"\toprule")
    print(r"\textbf{Model} & " + " & ".join(f"\\textbf{{{s.upper() if s != 'direct' else 'Direct'}}}" for s in STRATEGIES) + r" & $n$ \\")
    print(r"\midrule")
    for model in sorted(by_model):
        cells = [fmt(by_model[model].get(s)) for s in STRATEGIES]
        print(f"{model} & " + " & ".join(cells) + f" & {n_by_model[model]} \\\\")
    print(r"\bottomrule")
    print(r"\end{tabular}")
    print(r"\caption{Puzzle solve rate (all four groups exact) by model and prompting"
          r" strategy, with 95\% Wilson confidence intervals. Harness:"
          r" \texttt{experiments/solve\_puzzles.py}; prompts in Appendix~\ref{app:prompts}.}")
    print(r"\label{tab:solver}")
    print(r"\end{table*}")


if __name__ == "__main__":
    main()
