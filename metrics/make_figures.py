"""Generate all paper figures from results/*.json.

Every figure in the paper is produced by this script from committed result
files — no hand-made or unreproducible figures.

Usage:
    python metrics/make_figures.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "results"
OUT_PDF = ROOT / "paper" / "figures"
OUT_PNG = RESULTS / "figures"

# NYT Connections category colours (level 0-3: yellow, green, blue, purple)
NYT_COLORS = ["#f9df6d", "#a0c35a", "#b0c4ef", "#ba81c5"]
# Okabe-Ito colourblind-safe categorical palette (fixed order)
OKABE_ITO = ["#0072B2", "#E69F00", "#009E73"]

plt.rcParams.update({
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "grid.color": "#dddddd",
    "grid.linewidth": 0.5,
    "axes.axisbelow": True,
    "figure.dpi": 200,
})


def save(fig, name):
    OUT_PDF.mkdir(parents=True, exist_ok=True)
    OUT_PNG.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_PDF / f"{name}.pdf", bbox_inches="tight")
    fig.savefig(OUT_PNG / f"{name}.png", bbox_inches="tight")
    plt.close(fig)
    print(f"wrote {OUT_PDF / name}.pdf")


def fig_metric_validation():
    data = json.load(open(RESULTS / "metric_validation.json"))
    scores = data["per_group_scores"]
    by_level = {lv: [s["similarity"] for s in scores if s["level"] == lv] for lv in range(4)}

    fig, ax = plt.subplots(figsize=(3.3, 2.4))
    positions = list(by_level.keys())
    bp = ax.boxplot(
        [by_level[lv] for lv in positions], positions=positions, widths=0.62,
        patch_artist=True, showfliers=False, medianprops=dict(color="#333333", linewidth=1.2),
        boxprops=dict(linewidth=0.8, edgecolor="#555555"),
        whiskerprops=dict(linewidth=0.8, color="#555555"),
        capprops=dict(linewidth=0.8, color="#555555"),
    )
    for patch, color in zip(bp["boxes"], NYT_COLORS):
        patch.set_facecolor(color)
    means = [np.mean(by_level[lv]) for lv in positions]
    ax.plot(positions, means, marker="D", markersize=4, color="#333333", linewidth=1, label="mean")
    for x, m in zip(positions, means):
        ax.annotate(f"{m:.3f}", (x, m), textcoords="offset points", xytext=(14, 4), fontsize=7.5)
    ax.set_xticks(positions)
    ax.set_xticklabels(["0\n(easiest)", "1", "2", "3\n(hardest)"])
    ax.set_xlabel("Official NYT difficulty level")
    ax.set_ylabel("Intra-group similarity")
    rho = data["spearman_rho"]
    ax.set_title(f"Spearman $\\rho$ = {rho:.3f}, n = {data['n_groups']} groups", fontsize=8.5)
    save(fig, "metric_validation")


def fig_dataset_comparison():
    data = json.load(open(RESULTS / "dataset_comparison.json"))
    sources = [
        ("real_nyt", "Real NYT"),
        ("gpt4o_synthetic", "GPT-4o synthetic"),
        ("ambiguity_pipeline", "Ambiguity pipeline"),
    ]
    raw = data["raw_scores"]

    fig, ax = plt.subplots(figsize=(3.3, 2.0))
    ypos = np.arange(len(sources))[::-1]
    for (key, label), y, color in zip(sources, ypos, OKABE_ITO):
        vals = np.array([v for v in raw[key] if v is not None])
        bp = ax.boxplot(
            [vals], positions=[y], widths=0.55, vert=False, patch_artist=True,
            showfliers=False, medianprops=dict(color="#333333", linewidth=1.2),
            boxprops=dict(linewidth=0.8, edgecolor="#555555"),
            whiskerprops=dict(linewidth=0.8, color="#555555"),
            capprops=dict(linewidth=0.8, color="#555555"),
        )
        bp["boxes"][0].set_facecolor(color)
        bp["boxes"][0].set_alpha(0.75)
        ax.annotate(f"{vals.mean():.3f}", (vals.mean(), y + 0.38), fontsize=7.5, ha="center")
    ax.set_yticks(ypos)
    ax.set_yticklabels([label for _, label in sources])
    ax.set_xlabel("Intra-group similarity (lower = harder)")
    save(fig, "dataset_comparison")


def fig_ambiguity_ladder():
    data = json.load(open(RESULTS / "ambiguity_metrics.json"))
    levels = [1, 2, 3, 4]
    gen = [data["generated_by_group_level"][f"group_{lv}"] for lv in levels]
    senses = [g["mean_senses"] for g in gen]
    phrases = [g["phrase_ratio"] for g in gen]
    real_senses = data["real_nyt_overall"]["mean_senses"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(3.3, 2.0))
    x = np.arange(len(levels))

    ax1.bar(x, senses, width=0.62, color="#0072B2")
    ax1.axhline(real_senses, color="#333333", linewidth=1, linestyle="--")
    ax1.annotate(f"NYT avg ({real_senses:.1f})", (0.02, real_senses + 0.7),
                 fontsize=6.5, color="#333333")
    for xi, s in zip(x, senses):
        ax1.annotate(f"{s:.1f}", (xi, s + 0.4), ha="center", fontsize=7)
    ax1.set_xticks(x)
    ax1.set_xticklabels(levels)
    ax1.set_xlabel("Group level")
    ax1.set_ylabel("Mean WordNet senses")
    ax1.set_ylim(0, max(senses) * 1.18)

    ax2.bar(x, phrases, width=0.62, color="#0072B2")
    for xi, p in zip(x, phrases):
        ax2.annotate(f"{p:.2f}", (xi, p + 0.015), ha="center", fontsize=7)
    ax2.set_xticks(x)
    ax2.set_xticklabels(levels)
    ax2.set_xlabel("Group level")
    ax2.set_ylabel("Multi-word phrase ratio")
    ax2.set_ylim(0, 0.62)

    fig.tight_layout(w_pad=1.4)
    save(fig, "ambiguity_ladder")


if __name__ == "__main__":
    fig_metric_validation()
    fig_dataset_comparison()
    fig_ambiguity_ladder()
