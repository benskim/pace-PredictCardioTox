#!/usr/bin/env python3
"""Generate notebook templates 13-16 for the QTc Confidence Engine additions."""

import json
import pathlib

NOTEBOOKS_DIR = pathlib.Path(__file__).resolve().parent.parent / "notebooks"


def _cell(cell_type: str, source: list[str]) -> dict:
    cell = {
        "cell_type": cell_type,
        "metadata": {},
        "source": source,
    }
    if cell_type == "code":
        cell["execution_count"] = None
        cell["outputs"] = []
    return cell


def _notebook(cells: list[dict]) -> dict:
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3",
            },
            "language_info": {
                "name": "python",
                "version": "3.12.0",
            },
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def nb_13_measurement_confidence() -> dict:
    cells = [
        _cell("markdown", [
            "# 13 — Measurement Confidence Engine\n",
            "\n",
            "This notebook demonstrates the **QTc Measurement Confidence Score**,\n",
            "an explainable composite metric (0–100) that integrates:\n",
            "\n",
            "1. Signal quality\n",
            "2. T-end method stability\n",
            "3. T-wave morphology risk\n",
            "4. Formula agreement\n",
            "5. Beat-to-beat stability\n",
            "\n",
            "**Interpretation tiers:**\n",
            "- 90–100: High Confidence\n",
            "- 70–89: Review Recommended\n",
            "- <70: Manual Review Required\n",
        ]),
        _cell("code", [
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "\n",
            "from ecg_analytics.confidence import (\n",
            "    measurement_confidence,\n",
            "    signal_quality_subscore,\n",
            "    formula_agreement_score,\n",
            "    beat_stability_score,\n",
            ")\n",
            "from ecg_analytics.tend.agreement import compute_agreement\n",
            "from ecg_analytics.confidence.tend_stability import tend_stability_subscore\n",
            "from ecg_analytics.confidence.morphology_risk import morphology_risk_subscore\n",
            "from ecg_analytics.morphology import classify_t_wave\n",
        ]),
        _cell("markdown", [
            "## Generate a synthetic ECG signal\n",
        ]),
        _cell("code", [
            "fs = 500.0  # Hz\n",
            "t = np.linspace(0, 2, int(2 * fs))\n",
            "# Simple synthetic: R-peak at t=0.5s, T-wave around t=0.75s\n",
            "signal = (\n",
            "    1.5 * np.exp(-((t - 0.5) ** 2) / (2 * 0.005**2))   # R-peak\n",
            "    + 0.4 * np.exp(-((t - 0.75) ** 2) / (2 * 0.03**2))  # T-wave\n",
            ")\n",
            "plt.figure(figsize=(12, 3))\n",
            "plt.plot(t, signal)\n",
            "plt.title('Synthetic ECG')\n",
            "plt.xlabel('Time (s)')\n",
            "plt.show()\n",
        ]),
        _cell("markdown", [
            "## Compute sub-scores\n",
        ]),
        _cell("code", [
            "# Signal quality\n",
            "sq_score = signal_quality_subscore(signal, fs)\n",
            "print(f'Signal Quality Sub-score: {sq_score:.1f}')\n",
            "\n",
            "# T-end stability (run all 4 methods)\n",
            "t_peak = int(0.75 * fs)\n",
            "agreement = compute_agreement(signal, t_peak, fs)\n",
            "ts_score = tend_stability_subscore(agreement)\n",
            "print(f'T-End Stability Sub-score: {ts_score:.1f}')\n",
            "print(f'  Method results: {agreement.method_results}')\n",
            "\n",
            "# Morphology\n",
            "t_start = int(0.65 * fs)\n",
            "t_end_idx = int(0.90 * fs)\n",
            "morph = classify_t_wave(signal, t_start, t_end_idx, fs)\n",
            "mr_score = morphology_risk_subscore(morph.morphology, morph.confidence)\n",
            "print(f'Morphology Risk Sub-score: {mr_score:.1f} (type: {morph.morphology})')\n",
            "\n",
            "# Formula agreement\n",
            "fa = formula_agreement_score(qt_ms=400.0, rr_ms=850.0)\n",
            "print(f'Formula Agreement Sub-score: {fa.agreement_score:.1f} (spread: {fa.spread_ms:.1f} ms)')\n",
            "\n",
            "# Beat stability (simulated beat-level QTs)\n",
            "beat_qts = [398.0, 402.0, 400.0, 399.5, 401.0, 400.5, 399.0, 401.5, 400.0, 398.5]\n",
            "bs = beat_stability_score(beat_qts)\n",
            "print(f'Beat Stability Sub-score: {bs.stability_score:.1f} (CV: {bs.cv:.4f})')\n",
        ]),
        _cell("markdown", [
            "## Composite Confidence Score\n",
        ]),
        _cell("code", [
            "result = measurement_confidence(\n",
            "    signal_quality=sq_score,\n",
            "    tend_stability=ts_score,\n",
            "    morphology=mr_score,\n",
            "    formula_agreement=fa.agreement_score,\n",
            "    beat_stability=bs.stability_score,\n",
            ")\n",
            "print(f'Measurement Confidence Score: {result.score:.1f}')\n",
            "print(f'Tier: {result.tier}')\n",
            "print(f'Sub-scores: {result.sub_scores}')\n",
        ]),
        _cell("markdown", [
            "## Visualization — Sub-score Breakdown\n",
        ]),
        _cell("code", [
            "labels = list(result.sub_scores.keys())\n",
            "values = list(result.sub_scores.values())\n",
            "\n",
            "fig, ax = plt.subplots(figsize=(8, 5))\n",
            "colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']\n",
            "ax.barh(labels, values, color=colors)\n",
            "ax.set_xlim(0, 105)\n",
            "ax.axvline(90, color='green', linestyle='--', alpha=0.5, label='High threshold')\n",
            "ax.axvline(70, color='orange', linestyle='--', alpha=0.5, label='Review threshold')\n",
            "for i, v in enumerate(values):\n",
            "    ax.text(v + 1, i, f'{v:.1f}', va='center')\n",
            "ax.set_title(f'Confidence Breakdown (Overall: {result.score:.1f} — {result.tier})')\n",
            "ax.legend()\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
        ]),
    ]
    return _notebook(cells)


def nb_14_expert_variability() -> dict:
    cells = [
        _cell("markdown", [
            "# 14 — Expert (Inter-Observer) Variability\n",
            "\n",
            "This notebook demonstrates the framework for comparing manual\n",
            "annotations from multiple expert reviewers.\n",
            "\n",
            "Metrics:\n",
            "- Mean difference\n",
            "- SD of differences\n",
            "- Agreement rates at ±5, ±10, ±20 ms\n",
        ]),
        _cell("code", [
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "\n",
            "from ecg_analytics.validation.expert_variability import (\n",
            "    pairwise_comparison,\n",
            "    expert_variability_report,\n",
            ")\n",
        ]),
        _cell("markdown", [
            "## Simulate expert annotations\n",
        ]),
        _cell("code", [
            "np.random.seed(42)\n",
            "n_beats = 50\n",
            "# Ground-truth T-end positions (ms)\n",
            "truth = np.random.normal(420, 15, n_beats)\n",
            "\n",
            "# Three reviewers with different biases and noise\n",
            "reviewer_A = truth + np.random.normal(0, 3, n_beats)\n",
            "reviewer_B = truth + np.random.normal(2, 5, n_beats)\n",
            "reviewer_C = truth + np.random.normal(-1, 4, n_beats)\n",
            "\n",
            "annotations = {\n",
            "    'Reviewer A': reviewer_A,\n",
            "    'Reviewer B': reviewer_B,\n",
            "    'Reviewer C': reviewer_C,\n",
            "}\n",
        ]),
        _cell("markdown", [
            "## Pairwise comparison\n",
        ]),
        _cell("code", [
            "comp = pairwise_comparison(reviewer_A, reviewer_B, 'A', 'B')\n",
            "print(f'A vs B: mean diff = {comp.mean_diff_ms:.2f} ms, '\n",
            "      f'SD = {comp.sd_diff_ms:.2f} ms')\n",
            "print(f'  Agreement ±5 ms: {comp.agreement_within_5ms:.1%}')\n",
            "print(f'  Agreement ±10 ms: {comp.agreement_within_10ms:.1%}')\n",
        ]),
        _cell("markdown", [
            "## Full variability report\n",
        ]),
        _cell("code", [
            "report = expert_variability_report(annotations)\n",
            "print(f'Reviewers: {report.n_reviewers}')\n",
            "print(f'Beats: {report.n_beats}')\n",
            "print(f'Overall SD: {report.overall_sd_ms:.2f} ms')\n",
            "print()\n",
            "for comp in report.pairwise:\n",
            "    print(f'{comp.reviewer_a} vs {comp.reviewer_b}: '\n",
            "          f'mean={comp.mean_diff_ms:.2f}, SD={comp.sd_diff_ms:.2f}, '\n",
            "          f'±5ms={comp.agreement_within_5ms:.1%}')\n",
        ]),
        _cell("markdown", [
            "## Visualization\n",
        ]),
        _cell("code", [
            "fig, axes = plt.subplots(1, 3, figsize=(15, 4))\n",
            "pairs = [(reviewer_A, reviewer_B, 'A vs B'),\n",
            "         (reviewer_A, reviewer_C, 'A vs C'),\n",
            "         (reviewer_B, reviewer_C, 'B vs C')]\n",
            "for ax, (a, b, title) in zip(axes, pairs):\n",
            "    diff = a - b\n",
            "    mean = (a + b) / 2\n",
            "    ax.scatter(mean, diff, s=12, alpha=0.6)\n",
            "    ax.axhline(np.mean(diff), color='red', linestyle='--')\n",
            "    ax.axhline(np.mean(diff) + 1.96 * np.std(diff), color='gray', linestyle=':')\n",
            "    ax.axhline(np.mean(diff) - 1.96 * np.std(diff), color='gray', linestyle=':')\n",
            "    ax.set_title(title)\n",
            "    ax.set_xlabel('Mean (ms)')\n",
            "    ax.set_ylabel('Difference (ms)')\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
        ]),
    ]
    return _notebook(cells)


def nb_15_beat_variability() -> dict:
    cells = [
        _cell("markdown", [
            "# 15 — Beat-to-Beat QT Variability\n",
            "\n",
            "This notebook examines beat-level QT consistency and computes\n",
            "the **Beat Stability Score**.\n",
            "\n",
            "Metrics: Mean QT, Median QT, SD, IQR, Coefficient of Variation.\n",
        ]),
        _cell("code", [
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "\n",
            "from ecg_analytics.confidence.beat_stability import (\n",
            "    beat_qt_stats,\n",
            "    beat_stability_score,\n",
            ")\n",
        ]),
        _cell("markdown", [
            "## Simulated beat-level QT intervals\n",
        ]),
        _cell("code", [
            "np.random.seed(123)\n",
            "\n",
            "# Stable subject\n",
            "stable_qts = np.random.normal(400, 2, 20)\n",
            "\n",
            "# Unstable subject\n",
            "unstable_qts = np.random.normal(400, 15, 20)\n",
            "\n",
            "print('Stable QTs:', np.round(stable_qts[:5], 1), '...')\n",
            "print('Unstable QTs:', np.round(unstable_qts[:5], 1), '...')\n",
        ]),
        _cell("markdown", [
            "## Beat statistics\n",
        ]),
        _cell("code", [
            "stats_stable = beat_qt_stats(stable_qts)\n",
            "stats_unstable = beat_qt_stats(unstable_qts)\n",
            "\n",
            "print('Stable subject:')\n",
            "for k, v in stats_stable.items():\n",
            "    print(f'  {k}: {v:.2f}')\n",
            "\n",
            "print('\\nUnstable subject:')\n",
            "for k, v in stats_unstable.items():\n",
            "    print(f'  {k}: {v:.2f}')\n",
        ]),
        _cell("markdown", [
            "## Beat Stability Score\n",
        ]),
        _cell("code", [
            "result_stable = beat_stability_score(stable_qts)\n",
            "result_unstable = beat_stability_score(unstable_qts)\n",
            "\n",
            "print(f'Stable: score={result_stable.stability_score:.1f}, '\n",
            "      f'CV={result_stable.cv:.4f}, IQR={result_stable.iqr_qt_ms:.1f}')\n",
            "print(f'Unstable: score={result_unstable.stability_score:.1f}, '\n",
            "      f'CV={result_unstable.cv:.4f}, IQR={result_unstable.iqr_qt_ms:.1f}')\n",
        ]),
        _cell("markdown", [
            "## Visualization\n",
        ]),
        _cell("code", [
            "fig, axes = plt.subplots(1, 2, figsize=(12, 4))\n",
            "\n",
            "for ax, qts, label, score in [\n",
            "    (axes[0], stable_qts, 'Stable', result_stable.stability_score),\n",
            "    (axes[1], unstable_qts, 'Unstable', result_unstable.stability_score),\n",
            "]:\n",
            "    ax.plot(qts, 'o-', markersize=4)\n",
            "    ax.axhline(np.mean(qts), color='red', linestyle='--', label=f'Mean: {np.mean(qts):.1f}')\n",
            "    ax.fill_between(\n",
            "        range(len(qts)),\n",
            "        np.mean(qts) - np.std(qts),\n",
            "        np.mean(qts) + np.std(qts),\n",
            "        alpha=0.15, color='red', label='±1 SD',\n",
            "    )\n",
            "    ax.set_title(f'{label} (score: {score:.0f})')\n",
            "    ax.set_xlabel('Beat')\n",
            "    ax.set_ylabel('QT (ms)')\n",
            "    ax.legend(fontsize=8)\n",
            "\n",
            "plt.tight_layout()\n",
            "plt.show()\n",
        ]),
    ]
    return _notebook(cells)


def nb_16_clinical_validation() -> dict:
    cells = [
        _cell("markdown", [
            "# 16 — Clinical Validation Package\n",
            "\n",
            "This notebook demonstrates the clinical validation utilities:\n",
            "\n",
            "- **Bland–Altman analysis** with bias and limits of agreement\n",
            "- **Coverage analysis** at ±5, ±10, ±20 ms\n",
            "- Publication-quality figures\n",
        ]),
        _cell("code", [
            "import numpy as np\n",
            "import matplotlib.pyplot as plt\n",
            "\n",
            "from ecg_analytics.validation.clinical import (\n",
            "    bland_altman_analysis,\n",
            "    plot_clinical_bland_altman,\n",
            "    plot_coverage_bars,\n",
            ")\n",
        ]),
        _cell("markdown", [
            "## Simulate paired measurements\n",
        ]),
        _cell("code", [
            "np.random.seed(42)\n",
            "n = 200\n",
            "reference = np.random.normal(420, 20, n)\n",
            "predicted = reference + np.random.normal(1.5, 6, n)  # slight bias + noise\n",
        ]),
        _cell("markdown", [
            "## Bland–Altman Analysis\n",
        ]),
        _cell("code", [
            "ba = bland_altman_analysis(predicted, reference)\n",
            "print(f'Bias: {ba.bias:.2f} ms')\n",
            "print(f'SD: {ba.sd:.2f} ms')\n",
            "print(f'LoA: [{ba.loa_lower:.2f}, {ba.loa_upper:.2f}] ms')\n",
            "print(f'Coverage ±5 ms: {ba.coverage_5ms:.1%}')\n",
            "print(f'Coverage ±10 ms: {ba.coverage_10ms:.1%}')\n",
            "print(f'Coverage ±20 ms: {ba.coverage_20ms:.1%}')\n",
        ]),
        _cell("markdown", [
            "## Bland–Altman Plot (publication quality)\n",
        ]),
        _cell("code", [
            "fig = plot_clinical_bland_altman(predicted, reference,\n",
            "                                 title='QT Measurement: Method vs Reference')\n",
            "plt.show()\n",
        ]),
        _cell("markdown", [
            "## Coverage Bar Chart\n",
        ]),
        _cell("code", [
            "fig = plot_coverage_bars(ba, title='QT Measurement Coverage')\n",
            "plt.show()\n",
        ]),
        _cell("markdown", [
            "## Multi-condition Comparison\n",
            "\n",
            "Compare Bland–Altman statistics across noise conditions.\n",
        ]),
        _cell("code", [
            "conditions = ['Clean', 'SNR 24 dB', 'SNR 12 dB', 'SNR 6 dB']\n",
            "noise_levels = [0, 3, 8, 15]  # additional noise SD (ms)\n",
            "\n",
            "results = []\n",
            "for cond, noise_sd in zip(conditions, noise_levels):\n",
            "    noisy_pred = reference + np.random.normal(1.5, 6 + noise_sd, n)\n",
            "    ba_result = bland_altman_analysis(noisy_pred, reference)\n",
            "    results.append((cond, ba_result))\n",
            "    print(f'{cond}: bias={ba_result.bias:.2f}, '\n",
            "          f'SD={ba_result.sd:.2f}, '\n",
            "          f'±10ms={ba_result.coverage_10ms:.1%}')\n",
        ]),
    ]
    return _notebook(cells)


def main() -> None:
    NOTEBOOKS_DIR.mkdir(exist_ok=True)
    notebooks = {
        "13_measurement_confidence.ipynb": nb_13_measurement_confidence(),
        "14_expert_variability.ipynb": nb_14_expert_variability(),
        "15_beat_variability.ipynb": nb_15_beat_variability(),
        "16_clinical_validation.ipynb": nb_16_clinical_validation(),
    }
    for name, nb in notebooks.items():
        path = NOTEBOOKS_DIR / name
        path.write_text(json.dumps(nb, indent=1) + "\n")
        print(f"Generated {path}")


if __name__ == "__main__":
    main()
