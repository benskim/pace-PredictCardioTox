"""Basic ECG signal visualization."""

from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.figure import Figure


def plot_ecg_signal(
    signal: np.ndarray,
    fs: float,
    title: str = "ECG Signal",
    ax: Axes | None = None,
    figsize: tuple[float, float] = (14, 4),
) -> Figure:
    """Plot a single-lead ECG signal with a time axis in seconds.

    Returns the :class:`~matplotlib.figure.Figure`.
    """
    t = np.arange(len(signal)) / fs
    if ax is None:
        fig, ax = plt.subplots(figsize=figsize)
    else:
        fig = ax.figure

    ax.plot(t, signal, linewidth=0.6, color="#1f77b4")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude (mV)")
    ax.set_title(title)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig


def plot_multi_lead(
    signals: np.ndarray,
    fs: float,
    lead_names: list[str] | None = None,
    title: str = "12-Lead ECG",
    figsize: tuple[float, float] = (14, 16),
) -> Figure:
    """Plot a multi-lead ECG (signals shape: ``(samples, leads)``)."""
    n_leads = signals.shape[1] if signals.ndim == 2 else 1
    if lead_names is None:
        lead_names = [f"Lead {i}" for i in range(n_leads)]

    fig, axes = plt.subplots(n_leads, 1, figsize=figsize, sharex=True)
    if n_leads == 1:
        axes = [axes]
    t = np.arange(signals.shape[0]) / fs

    for i, ax_i in enumerate(axes):
        lead_signal = signals[:, i] if signals.ndim == 2 else signals
        ax_i.plot(t, lead_signal, linewidth=0.5, color="#1f77b4")
        ax_i.set_ylabel(lead_names[i], fontsize=8)
        ax_i.grid(True, alpha=0.3)
        ax_i.tick_params(labelsize=7)

    axes[-1].set_xlabel("Time (s)")
    fig.suptitle(title, fontsize=12)
    fig.tight_layout()
    return fig
