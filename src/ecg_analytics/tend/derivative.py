"""Derivative-based T-end determination.

T-end is located as the first near-zero-crossing of the smoothed first
derivative on the trailing edge of the T-wave, indicating the return to
the isoelectric baseline.
"""

from __future__ import annotations

import numpy as np
from scipy.ndimage import uniform_filter1d


def derivative_t_end(
    signal: np.ndarray,
    t_peak: int,
    fs: float,
    smooth_ms: float = 20.0,
    search_window_ms: float = 200.0,
    zero_threshold_fraction: float = 0.05,
) -> int | None:
    """Determine T-end via the derivative zero-crossing method.

    Parameters
    ----------
    signal : np.ndarray
        1-D ECG signal.
    t_peak : int
        Sample index of the T-wave peak.
    fs : float
        Sampling frequency in Hz.
    smooth_ms : float
        Smoothing window width in ms applied before differentiation.
    search_window_ms : float
        How far past the T-peak to search (ms).
    zero_threshold_fraction : float
        Fraction of the peak derivative magnitude below which the
        derivative is considered "zero".

    Returns
    -------
    int | None
        Sample index of T-end, or ``None`` if not found.
    """
    search_samples = int(search_window_ms * fs / 1000)
    smooth_samples = max(3, int(smooth_ms * fs / 1000))
    end_idx = min(t_peak + search_samples, len(signal) - 1)

    if end_idx <= t_peak + 2:
        return None

    trailing = signal[t_peak:end_idx].astype(float)

    # Smooth then differentiate
    smoothed = uniform_filter1d(trailing, size=smooth_samples)
    deriv = np.diff(smoothed)

    if len(deriv) == 0:
        return None

    # Threshold for "near zero"
    max_deriv_mag = np.max(np.abs(deriv))
    if max_deriv_mag < 1e-12:
        return None

    zero_thresh = zero_threshold_fraction * max_deriv_mag

    # Find first point after the initial downslope where |derivative| < threshold
    # Skip the first few samples (still on the T-wave descent)
    min_skip = max(1, len(deriv) // 4)
    for i in range(min_skip, len(deriv)):
        if abs(deriv[i]) < zero_thresh:
            t_end_sample = t_peak + i
            if t_end_sample < len(signal):
                return t_end_sample
            return None

    return None
