"""Threshold method for T-end determination.

T-end is defined as the point where the T-wave amplitude falls below a
given fraction of the T-wave peak amplitude on the trailing edge.
"""

from __future__ import annotations

import numpy as np


def threshold_t_end(
    signal: np.ndarray,
    t_peak: int,
    fs: float,
    baseline: float = 0.0,
    threshold_fraction: float = 0.15,
    search_window_ms: float = 200.0,
) -> int | None:
    """Determine T-end via the threshold method.

    Parameters
    ----------
    signal : np.ndarray
        1-D ECG signal.
    t_peak : int
        Sample index of the T-wave peak.
    fs : float
        Sampling frequency in Hz.
    baseline : float
        Isoelectric baseline voltage.
    threshold_fraction : float
        Fraction of peak-to-baseline amplitude used as threshold (0–1).
    search_window_ms : float
        How far past the T-peak to search (ms).

    Returns
    -------
    int | None
        Sample index of T-end, or ``None`` if not found.
    """
    search_samples = int(search_window_ms * fs / 1000)
    end_idx = min(t_peak + search_samples, len(signal))

    if end_idx <= t_peak + 1:
        return None

    peak_amplitude = signal[t_peak] - baseline
    if abs(peak_amplitude) < 1e-12:
        return None

    threshold_value = baseline + threshold_fraction * peak_amplitude

    trailing = signal[t_peak:end_idx]

    if peak_amplitude > 0:
        # Positive T-wave: look for signal dropping below threshold
        crossings = np.where(trailing <= threshold_value)[0]
    else:
        # Inverted T-wave: look for signal rising above threshold
        crossings = np.where(trailing >= threshold_value)[0]

    if len(crossings) == 0:
        return None

    t_end_sample = t_peak + int(crossings[0])

    if t_end_sample <= t_peak or t_end_sample >= len(signal):
        return None

    return t_end_sample
