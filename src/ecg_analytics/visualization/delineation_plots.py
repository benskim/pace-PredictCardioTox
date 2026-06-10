"""Delineation overlay visualization."""

from __future__ import annotations

import numpy as np
from matplotlib import pyplot as plt
from matplotlib.figure import Figure

from ..delineation.labels import WAVE_CLASSES

_COLORS = {
    "P-wave": "#e377c2",
    "QRS": "#2ca02c",
    "T-wave": "#ff7f0e",
}


def plot_delineation_overlay(
    signal: np.ndarray,
    mask: np.ndarray,
    fs: float,
    title: str = "Wave Delineation",
    figsize: tuple[float, float] = (14, 5),
) -> Figure:
    """Overlay wave-class regions on top of an ECG signal.

    Parameters
    ----------
    signal : np.ndarray
        1-D ECG signal.
    mask : np.ndarray
        Per-sample class mask from the delineation model.
    fs : float
        Sampling frequency.
    """
    t = np.arange(len(signal)) / fs
    fig, ax = plt.subplots(figsize=figsize)
    ax.plot(t, signal, linewidth=0.6, color="black", label="ECG")

    for cls_id, cls_name in WAVE_CLASSES.items():
        if cls_id == 0:
            continue
        color = _COLORS.get(cls_name, "gray")
        regions = np.where(mask == cls_id, signal, np.nan)
        ax.fill_between(t, 0, regions, alpha=0.3, color=color, label=cls_name)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude (mV)")
    ax.set_title(title)
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    return fig
