"""Validation-specific plots: Bland-Altman, error distributions, heatmaps."""

from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure


def plot_bland_altman(
    predicted: np.ndarray,
    reference: np.ndarray,
    title: str = "Bland-Altman Plot",
    unit: str = "ms",
    figsize: tuple[float, float] = (8, 6),
) -> Figure:
    """Create a Bland-Altman (difference) plot.

    Parameters
    ----------
    predicted, reference : np.ndarray
        Paired measurement arrays.
    """
    mean_vals = (predicted + reference) / 2
    diff = predicted - reference
    mean_diff = np.mean(diff)
    std_diff = np.std(diff)

    fig, ax = plt.subplots(figsize=figsize)
    ax.scatter(mean_vals, diff, s=12, alpha=0.6, edgecolors="none")
    ax.axhline(mean_diff, color="red", linestyle="--", label=f"Mean: {mean_diff:.2f}")
    ax.axhline(mean_diff + 1.96 * std_diff, color="gray", linestyle=":", label="+1.96 SD")
    ax.axhline(mean_diff - 1.96 * std_diff, color="gray", linestyle=":", label="-1.96 SD")
    ax.set_xlabel(f"Mean of Predicted and Reference ({unit})")
    ax.set_ylabel(f"Predicted - Reference ({unit})")
    ax.set_title(title)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_error_distribution(
    errors: np.ndarray,
    title: str = "Error Distribution",
    unit: str = "ms",
    figsize: tuple[float, float] = (8, 5),
) -> Figure:
    """Histogram of measurement errors with summary statistics."""
    fig, ax = plt.subplots(figsize=figsize)
    ax.hist(errors, bins=40, edgecolor="white", alpha=0.8, color="#1f77b4")
    ax.axvline(np.mean(errors), color="red", linestyle="--", label=f"Mean: {np.mean(errors):.2f}")
    ax.axvline(np.median(errors), color="green", linestyle="--", label=f"Median: {np.median(errors):.2f}")
    ax.set_xlabel(f"Error ({unit})")
    ax.set_ylabel("Count")
    ax.set_title(title)
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_error_heatmap(
    noise_types: list[str],
    snr_levels: list[int],
    errors: np.ndarray,
    metric_name: str = "QT MAE (ms)",
    figsize: tuple[float, float] = (10, 6),
) -> Figure:
    """Heatmap of errors across noise types and SNR levels.

    Parameters
    ----------
    errors : np.ndarray
        Shape ``(len(noise_types), len(snr_levels))``.
    """
    fig, ax = plt.subplots(figsize=figsize)
    im = ax.imshow(errors, cmap="YlOrRd", aspect="auto")

    ax.set_xticks(range(len(snr_levels)))
    ax.set_xticklabels([f"{s} dB" for s in snr_levels])
    ax.set_yticks(range(len(noise_types)))
    ax.set_yticklabels(noise_types)

    for i in range(len(noise_types)):
        for j in range(len(snr_levels)):
            ax.text(j, i, f"{errors[i, j]:.1f}", ha="center", va="center", fontsize=9)

    ax.set_xlabel("SNR Level")
    ax.set_ylabel("Noise Type")
    ax.set_title(metric_name)
    fig.colorbar(im, ax=ax)
    fig.tight_layout()
    return fig
