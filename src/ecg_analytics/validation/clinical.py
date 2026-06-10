"""Clinical validation utilities.

Provides reusable Bland–Altman analysis, coverage statistics, and
publication-quality figure generation for method-comparison studies.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure


@dataclass
class BlandAltmanResult:
    """Output of a Bland–Altman analysis.

    Attributes
    ----------
    bias : float
        Mean difference (predicted − reference) in ms.
    sd : float
        Standard deviation of differences.
    loa_lower, loa_upper : float
        95 % limits of agreement (bias ± 1.96 × SD).
    coverage_5ms : float
        Fraction of beats within ±5 ms.
    coverage_10ms : float
    coverage_20ms : float
    n : int
        Number of paired measurements.
    """

    bias: float
    sd: float
    loa_lower: float
    loa_upper: float
    coverage_5ms: float
    coverage_10ms: float
    coverage_20ms: float
    n: int


def bland_altman_analysis(
    predicted: np.ndarray | list[float],
    reference: np.ndarray | list[float],
) -> BlandAltmanResult:
    """Perform Bland–Altman analysis on paired measurements.

    Parameters
    ----------
    predicted, reference : array-like
        Paired measurement arrays (ms).

    Returns
    -------
    BlandAltmanResult
    """
    pred = np.asarray(predicted, dtype=float)
    ref = np.asarray(reference, dtype=float)
    diff = pred - ref
    abs_diff = np.abs(diff)

    bias = float(np.mean(diff))
    sd = float(np.std(diff, ddof=1)) if len(diff) > 1 else 0.0

    return BlandAltmanResult(
        bias=bias,
        sd=sd,
        loa_lower=bias - 1.96 * sd,
        loa_upper=bias + 1.96 * sd,
        coverage_5ms=float(np.mean(abs_diff <= 5.0)),
        coverage_10ms=float(np.mean(abs_diff <= 10.0)),
        coverage_20ms=float(np.mean(abs_diff <= 20.0)),
        n=len(diff),
    )


def plot_clinical_bland_altman(
    predicted: np.ndarray | list[float],
    reference: np.ndarray | list[float],
    title: str = "Bland-Altman Analysis",
    unit: str = "ms",
    figsize: tuple[float, float] = (9, 7),
) -> Figure:
    """Publication-quality Bland–Altman plot with bias, LoA, and coverage bands.

    Parameters
    ----------
    predicted, reference : array-like
        Paired measurements.

    Returns
    -------
    matplotlib.figure.Figure
    """
    pred = np.asarray(predicted, dtype=float)
    ref = np.asarray(reference, dtype=float)
    ba = bland_altman_analysis(pred, ref)

    mean_vals = (pred + ref) / 2
    diff = pred - ref

    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(mean_vals, diff, s=14, alpha=0.5, color="#1f77b4", edgecolors="none")

    # Bias line
    ax.axhline(ba.bias, color="red", linewidth=1.5, linestyle="--", label=f"Bias: {ba.bias:.2f} {unit}")

    # Limits of agreement
    ax.axhline(ba.loa_upper, color="#555555", linewidth=1, linestyle=":",
               label=f"+1.96 SD: {ba.loa_upper:.2f}")
    ax.axhline(ba.loa_lower, color="#555555", linewidth=1, linestyle=":",
               label=f"-1.96 SD: {ba.loa_lower:.2f}")

    # Coverage bands
    for band, color, alpha in [(5, "#2ca02c", 0.08), (10, "#ff7f0e", 0.06), (20, "#9467bd", 0.04)]:
        ax.axhspan(-band, band, color=color, alpha=alpha, label=f"±{band} {unit}")

    ax.set_xlabel(f"Mean of Methods ({unit})", fontsize=11)
    ax.set_ylabel(f"Difference ({unit})", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(True, alpha=0.25)

    # Annotate coverage
    text_lines = [
        f"n = {ba.n}",
        f"±5 {unit}: {ba.coverage_5ms:.1%}",
        f"±10 {unit}: {ba.coverage_10ms:.1%}",
        f"±20 {unit}: {ba.coverage_20ms:.1%}",
    ]
    ax.text(
        0.02, 0.02, "\n".join(text_lines),
        transform=ax.transAxes, fontsize=9, verticalalignment="bottom",
        bbox={"boxstyle": "round,pad=0.4", "facecolor": "white", "alpha": 0.8},
    )

    fig.tight_layout()
    return fig


def plot_coverage_bars(
    ba_result: BlandAltmanResult,
    title: str = "Coverage Analysis",
    figsize: tuple[float, float] = (7, 5),
) -> Figure:
    """Bar chart of coverage at ±5, ±10, ±20 ms thresholds.

    Parameters
    ----------
    ba_result : BlandAltmanResult

    Returns
    -------
    matplotlib.figure.Figure
    """
    labels = ["±5 ms", "±10 ms", "±20 ms"]
    values = [ba_result.coverage_5ms * 100, ba_result.coverage_10ms * 100, ba_result.coverage_20ms * 100]
    colors = ["#2ca02c", "#ff7f0e", "#9467bd"]

    fig, ax = plt.subplots(figsize=figsize)
    bars = ax.bar(labels, values, color=colors, edgecolor="white", width=0.5)

    for bar, val in zip(bars, values):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                f"{val:.1f}%", ha="center", va="bottom", fontsize=11, fontweight="bold")

    ax.set_ylim(0, 110)
    ax.set_ylabel("Coverage (%)", fontsize=11)
    ax.set_title(title, fontsize=13, fontweight="bold")
    ax.grid(True, axis="y", alpha=0.3)
    fig.tight_layout()
    return fig
