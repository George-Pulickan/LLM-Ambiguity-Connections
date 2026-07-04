# Response to NAACL-SRW 2025 Reviews (Submission 110)

This document maps every point raised by Reviewers cmRe and f2S2 to the concrete
change made in the revised paper (`paper/main.tex`) and codebase. Section/table/figure
numbers refer to the revised paper.

## Reviewer cmRe

| # | Review point | Fix | Where |
|---|---|---|---|
| 1 | "Not described in enough detail to replicate; in particular, the prompts are not given" | Every prompt (generation, validation, audit, and all three solver strategies) is reproduced verbatim in the paper and versioned as text files | Appendix A; `prompts/` |
| 2 | "How accurate is the difficulty assessment method? If it is not sound, we have no way of knowing whether the construction method is, either" | **New experiment.** The metric is validated against ground-truth official NYT difficulty levels on 830 puzzles / 3,320 groups (data current through 2026-07-04): Spearman ρ = −0.441 (p < 1e−157), monotonic per-level means, 70% within-puzzle pairwise ordering accuracy. The paper now explicitly treats the metric as a coarse corpus-level signal and documents where it fails (wordplay categories) | §6, Table 1, Fig. 2; `metrics/validate_difficulty.py`, `results/metric_validation.json` |
| 3 | "Are there other measures of how good a puzzle is other than difficulty (novelty, fun)?" | Acknowledged head-on: a full human-evaluation protocol (solvability, fairness, enjoyment; mixed-effects analyses; H3 explicitly guards against 'ambiguous = arbitrary') is specified. It is honestly labeled *designed, not yet run* and listed as the first limitation | Appendix C, §10 |
| 4 | "Solving methods described very briefly... nothing about ToT in 3.2–3.3. What are 'base' and 'challenge'? What is the 'false group'?" | The undocumented solve-rate experiments (and their unexplained categories) are **removed** rather than papered over: their numbers were not regenerable from a specified protocol. In their place: a fully documented solver harness with three specified strategies (direct/CoT/ToT), defined metrics, and per-instance logging, so the experiment is one command | §8; `experiments/solve_puzzles.py`, `prompts/solver_*.txt` |
| 5 | "What is the hypothesis that these experiments are meant to prove?" | The paper is reframed around one crisp claim: *explicitly targeting an ambiguity taxonomy, with external validation, produces measurably harder groups than human construction or naive LLM generation — under a metric whose relation to ground truth we measured.* Contributions are enumerated in §1 | §1, §7.2 |
| 6 | "Seed dataset cited only by a filename (connections.json). What is the source, is it freely available?" | Dataset provenance stated with URL (community-maintained NYT-Connections-Answers archive), scope (1,114 puzzles, 2023-06-12 to 2026-07-04, refreshable via `data/update_real_data.py`), license/usage note in the Ethics Statement | §6.2 footnote, Appendix B, Ethics |
| 7 | Figure 3 caption/axis mismatch; text refers to Table 1/2 but shows figures; Figures 4 and 5 swapped | All figures and tables are regenerated from committed result files by one script; references use `\ref` so numbering cannot drift | `metrics/make_figures.py`; throughout |

## Reviewer f2S2

| # | Review point | Fix | Where |
|---|---|---|---|
| 1 | Lacks reproducibility; no prompts; unclear setup | Full release: pipeline, prompts, metrics, figure generation, datasets, requirements. Every number in the paper regenerates from the repo (commands in README) | whole repo; Appendix A |
| 2 | Starting-point data not cited appropriately | See cmRe #6 | §6.2, Appendix B |
| 3 | L88 "various strategies" vague; L89 "our experiments" undefined; L98 "analysis of their games" unattributed | Rewritten introduction names methods explicitly and enumerates contributions; the constraints section states the analysis basis (422 published puzzles + Merino et al. 2024) | §1, §4 |
| 4 | Criteria contain duplicates (4≈1, 8≈3); criterion 6 vague; 7 undefined ("valid"); 9 harms understanding | The ten criteria are consolidated into six non-overlapping conditions; vacuous "must be valid" removed (validity = conditions 1–2, checked automatically); each condition has a concrete example. The consolidation is acknowledged in the text | §4 |
| 5 | Ll.148–152 dynamic difficulty adjustment unclear in practice | Removed. The revised method's difficulty control is the explicit four-tier ladder, which is fully specified and measured | §5.1, §7.1 |
| 6 | Strategy 5 risk: puzzles humans might disagree on / not solvable | Addressed three ways: RCoT audit stage must reconstruct a coherent rationale from the word list alone (§5.3); fairness hypothesis H3 in the human-eval protocol; explicit limitation "a group can be diverse yet unsolvable" | §5.3, §10, Appendix C |
| 7 | L205 "a JSON file" unsourced | See cmRe #6 | §6.2 |
| 8 | Ll.223–227 "recent/relevant" categories undefined; Nice/Niche category generation disconnected; "5-LETTER WORDS" criterion vague | The single-prompt generation description is simplified and demoted to what it is in the revised paper: a baseline dataset (documented in Appendix B). The niche-category machinery, which was never evaluated, is removed | Appendix B |
| 9 | Structure: construction hard to follow; Figures 1–2 never referenced; 3.1 belongs with 2.3; setup mixed into Results; models not named/cited per experiment | Full restructure: pipeline overview figure referenced in text (Fig. 1); metric definition (§6.1) and its validation (§6.2) form one section; every experiment states data, model (GPT-4o generation; all-mpnet-base-v2 embeddings, cited), and procedure before results; Results contains only results | §5–§7 |
| 10 | Unstable references ("The following Table Figure"); text mentions CoT results missing from figure; wrong figure references | All cross-references are LaTeX `\ref`s to regenerated artifacts | throughout |
| 11 | Figure 4 groups unmotivated | The old figure is gone; every reported breakdown (pipeline tiers, NYT levels, sources) is defined where introduced | §7 |
| 12 | L85 claim unspecific; L87 user-experience effects unjustified | User-experience claims removed from the paper's claims; they are now hypotheses in the human-eval protocol | Appendix C |
| 13 | Ll.345 "structured reasoning" conclusion unbacked (one model, one technique) | That claim is removed. The comparison now has n = 4,452 / 6,016 / 200 groups with significance tests, and claims are scoped to what the validated metric supports | §7.2, Table 3 |
| 14 | Ll.381 conclusions unbacked; hallucination may explain larger distances (invalid puzzles, not harder ones) | Directly acknowledged: the validity concern is why Stage 2 (LLM-free WordNet validation) and Stage 3 (reverse audit) exist, why fairness is H3 in the human protocol, and why "diverse yet unsolvable" is a named limitation. Claims are corpus-level and metric-scoped | §5.2–5.3, §10 |
| 15 | Generalisability (ll.390–402) not backed | Generalization claims cut to one method-level sentence in the conclusion; single-generator-family and puzzle-type-coverage limitations added | §9, §10 |
| 16 | Cite newer LLM-reasoning work | Added GSM-Symbolic (Mirzadeh et al., 2024) — which also motivates the external-validation design — plus ReAct, Least-to-Most, RCoT, Samadarshi et al. 2024, Todd et al. 2024 | §2 |
| 17 | Typos, line-break issues, grammar, missing citation at L99, "(mention authors name)" placeholder | Paper rewritten from scratch; the placeholder citation is now Merino et al. (2024) | throughout |

## Changes that go beyond the reviews

- **Dataset refreshed to 2026-07-04** (1,114 puzzles vs the original 422) via a
  reproducible update script; all statistics re-computed on current data. This surfaced
  a new finding now in §7.2: the official game has drifted significantly harder since
  late 2025 (0.294 → 0.275 mean intra-group similarity, p = 1.6e−9), converging toward
  the pipeline's semantic-diversity regime.

- The difficulty formula now averages over the C(n,2) distinct pairs rather than all n² ordered pairs including self-similarity (which compressed the scale); noted in §6.1.
- Honest negative/nuanced findings are reported: tiers 2 and 3 are statistically indistinguishable in sense count, and real NYT difficulty is *not* driven by lexical ambiguity (flat sense counts across levels) — which sharpens the paper's positioning of ambiguity as a new difficulty axis.
- Solve-rate numbers from the previous submission (23.46%, 1.73%, etc.) are intentionally **not** carried over: no protocol or logs existed to regenerate them. The released harness (`experiments/solve_puzzles.py`) regenerates them properly; add a Results subsection once run.
