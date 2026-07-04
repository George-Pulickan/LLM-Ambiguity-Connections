# Solver experiments — the "weekend run"

Goal: one paper table comparing current models × prompting strategies on the same
puzzle set, with confidence intervals. This fills §8 of the paper with real,
current-model numbers and directly addresses the "GPT-3.5 vs GPT-4-Turbo reads
as a time capsule" concern.

## The interesting hypothesis

If CoT/ToT scaffolding lifts a *standard* model but a *reasoning* model beats both
with the plain direct prompt, that's a clean workshop-sized finding:
**inference-time search scaffolds vs. native reasoning**.

## Recommended matrix (9 runs, ~100 puzzles each)

Pick one standard model, one small/cheap model, and one reasoning model that are
current at run time (check https://platform.openai.com/docs/models), e.g. a
`gpt-4o`-class model, a mini-tier model, and an o-series/`gpt-5`-class reasoning
model. The harness auto-switches API parameters for reasoning models
(no temperature; `max_completion_tokens=16000` to cover hidden reasoning tokens).

```bash
export OPENAI_API_KEY=sk-...

for MODEL in gpt-4o gpt-4o-mini o3; do          # substitute current model ids
  for STRAT in direct cot tot; do
    python experiments/solve_puzzles.py --dataset real \
      --model "$MODEL" --strategy "$STRAT" --limit 100
  done
done
```

Notes:
- `--limit 100` uses the first 100 real puzzles. For a contamination probe, add a
  second pass on the newest puzzles (post model-cutoff): they are at the END of
  Real_Data.json, which is sorted by id — use a small wrapper or `--dataset generated
  --file Testing_Data.json` for the synthetic set.
- Cost: dominated by the reasoning model's ToT runs. Budget rough order:
  100 puzzles × ~1–8k tokens ≈ single-digit dollars for standard models; check the
  reasoning model's pricing before launching its 3 runs.
- Each run writes `results/solver/<model>_<strategy>_<dataset>_{summary,records}.json`
  (records include raw responses for the trace-analysis follow-up).

## Then build the paper table

```bash
python experiments/make_solver_table.py > paper/solver_table.tex
```

Add `\input{solver_table}` in §8 of `paper/main.tex` (replacing the "we report no
solver numbers" paragraph with the table and 2–3 sentences of findings), recompile,
and check per-level accuracies in the summaries — the level-3 (purple) column is
where the human-hard/machine-hard divergence shows.
