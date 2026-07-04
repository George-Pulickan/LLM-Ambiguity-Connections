# Mind the Gap: Adversarial Synthesis of Human-Easy, Machine-Hard Word Puzzles

*One-page research proposal — July 2026 (working title)*

## Problem

Frontier reasoning models now near-saturate NYT Connections (o1 already scored 90.7 on
the standard benchmark; the community's response has been heuristic trick-word injection
with no human verification). What nobody has established is whether the residual failures
reflect a **real, structured gap in lateral semantic reasoning** or just noise and training-set
contamination. We propose to make the *gap itself* the scientific object: a closed-loop
framework that searches for puzzles verifiably **easy for humans but hard for reasoning
models**, plus the analyses that make the gap interpretable.

## Method — the loop

1. **Generator** LLM proposes Connections-style puzzles (4×4 grid + theme labels).
2. **Validity verifier** rejects puzzles without a unique partition (embedding-overlap
   checks + solver-based search for alternative solutions).
3. **Human-solvability proxy** keeps the loop honest: a predictor of human solve rate
   trained on published NYT puzzles and public per-puzzle human performance data,
   using features we have already built and validated (intra/inter-group embedding
   similarity — validated against official NYT difficulty at ρ = −0.44, n = 3,320 groups —
   plus word frequency and WordNet sense statistics). Generation is constrained to
   puzzles predicted human-solvable; without this the loop degenerates into obscurity.
4. **Adversarial signal**: cheap solvers in the inner loop; frontier reasoning models
   evaluated periodically in the outer loop only (cost control). Search runs as
   **MAP-Elites** over interpretable trick dimensions (red-herring density, polysemy
   load, wordform-vs-meaning tricks, encyclopedic knowledge) so we discover *diverse*
   failure modes rather than one exploit repeated.

## Experiments

- **Transfer split**: optimize against held-in solvers (o-series, Claude); evaluate on
  held-out families (Gemini, DeepSeek). Do adversarial puzzles transfer across families
  or overfit one model's quirks? Clean analogy to adversarial-example transferability.
- **Baselines**: hardest-quartile real NYT; lechmazur-style trick-word injection;
  Merino-style ToT generation without adversarial feedback; random valid puzzles.
  Metric = the **human–AI gap**, not raw difficulty.
- **Preregistered human study** (Prolific): paired within-subject, 40–60 puzzles ×
  25–30 solvers, mixed-effects logistic regression with puzzle random effects, power
  analysis up front. Target claim: human solve rate indistinguishable from matched NYT
  controls; model solve rate drops by X points.
- **Trace analysis**: annotate reasoning traces for premature commitment, failure to
  backtrack, dominant-sense anchoring — updating the existing knowledge-type taxonomy
  (Samadarshi et al., 2024) for the reasoning-model era.
- **Ablations**: drop the solvability constraint (loop should degenerate into obscurity),
  drop QD diversity, drop solver feedback.

## Positioning (literature sweep, 2026-07-04)

| Line | Closest work | Our differentiation |
|---|---|---|
| Declarative/adversarial benchmark construction | AutoBencher (Li et al., arXiv:2407.08351); Dynabench | Verified *human-easiness* constraint; structured puzzle domain; trace taxonomy |
| Human-easy / AI-hard benchmarks | ARC-AGI-2 (static, hand-built, visual); SimpleBench (200 hand-written items) | *Generative, closed-loop, self-renewing* — contamination-free by construction |
| Connections + LLMs | Samadarshi et al. 2024; NYT-Connections (arXiv:2412.01621); lechmazur Extended Connections (940 puzzles, heuristic tricks, no human verification) | Adversarial search + human verification + failure-mode diversity |
| QD/MAP-Elites × LLMs | Rainbow Teaming; QD Red-Teaming (arXiv:2506.07121); QD-Vulnerabilities (arXiv:2606.00801) | Same machinery, different object: capability gaps, not safety jailbreaks — cite and adapt |

No existing work occupies the intersection: **adversarially searched + human-verified-easy +
interpretable failure dimensions**. The QD-safety line is the methodological neighbor and
the direction most likely to converge on us; re-sweep before submission.

## Assets already in hand (this repository)

1,114-puzzle NYT dataset with reproducible refresh script; a difficulty metric *validated
against ground truth* (ρ = −0.441, p < 1e−157; 70% pairwise ordering accuracy) — the core
of the solvability proxy; a solver-evaluation harness (direct/CoT/ToT); a three-stage
ambiguity-amplifying generator (a ready-made baseline and trick-dimension source); and an
empirical finding that the official game drifted harder post-2025 — useful for
contamination-aware control selection.

## Risks

- **Gap turns out small** → still a publishable contamination-free robustness finding, but
  weaker; pilot with ~20 puzzles before the full study.
- **Per-puzzle human data**: public sources exist (WordsRated per-puzzle fail rates/average
  guesses; community compilations) but a complete ~900-puzzle solve-rate table is
  unconfirmed — verify/scrape in week 1; fallback = official difficulty levels + our
  validated metric as proxy features, calibrated on the pilot.
- **API cost** for reasoning models — outer loop only.
- **Bandwidth**: multi-month effort competing with other commitments; needs a primary-project decision.

## Timeline & venue

Build Sep–Nov 2026 → pilot human study Dec 2026 → full study Jan 2027 →
**ARR Feb 2027 (ACL 2027)** or **NeurIPS 2027 Datasets & Benchmarks** (best fit).
Fallbacks: Wordplay workshop, IEEE CoG.
