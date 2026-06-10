"""Noise robustness visualizations."""

from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure


def plot_noise_comparison(
    clean: np.ndarray,
    noisy: np.ndarray,
    fs: float,
    noise_label: str = "Noisy",
    snr_db: float | None = None,
    figsize: tuple[float, float] = (14, 6),
) -> Figure:
    """Side-by-side comparison of clean vs. noisy signal."""
    t = np.arange(len(clean)) / fs
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=figsize, sharex=True)

    ax1.plot(t, clean, linewidth=0.6, color="#1f77b4")
    ax1.set_title("Clean Signal")
    ax1.set_ylabel("Amplitude (mV)")
    ax1.grid(True, alpha=0.3)

    label = noise_label
    if snr_db is not None:
        label += f" (SNR={snr_db} dB)"
    ax2.plot(t, noisy, linewidth=0.6, color="#d62728")
    ax2.set_title(label)
    ax2.set_xlabel("Time (s)")
    ax2.set_ylabel("Amplitude (mV)")
    ax2.grid(True, alpha=0.3)

    fig.tight_layout()
    return fig


def plot_noise_degradation(
    snr_levels: list[int],
    mae_values: dict[str, list[float]],
    metric_name: str = "QT MAE (ms)",
    figsize: tuple[float, float] = (8, 5),
) -> Figure:
    """Line plot showing metric degradation across SNR levels.

    Parameters
    ----------
    mae_values : dict
        Mapping of noise type name to list of metric values
        (one per SNR level).
    """
    fig, ax = plt.subplots(figsize=figsize)
    for name, vals in mae_values.items():
        ax.plot(snr_levels, vals, marker="o", label=name)

    ax.set_xlabel("SNR (dB)")
    ax.set_ylabel(metric_name)
    ax.set_title(f"{metric_name} vs. SNR")
    ax.legend(fontsize=8)
    ax.invert_xaxis()  # Lower SNR (more noise) on the right
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig
