"""Geometric tangent method for T-end determination.

The *tangent method* fits a straight line at the point of maximum
downslope on the trailing edge of the T-wave, then defines T-end as the
intersection of that tangent with the isoelectric baseline.  This is the
recommended clinical approach for explainable T-end determination.
"""

from __future__ import annotations

import numpy as np


def tangent_t_end(
    signal: np.ndarray,
    t_peak: int,
    fs: float,
    baseline: float = 0.0,
    search_window_ms: float = 200.0,
) -> int | None:
    """Determine T-end via the geometric tangent method.

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
    search_window_ms : float
        How far past the T-peak to search for the maximum downslope (ms).

    Returns
    -------
    int | None
        Sample index of T-end, or ``None`` if the tangent does not intersect
        the baseline within a reasonable range.
    """
    search_samples = int(search_window_ms * fs / 1000)
    end_idx = min(t_peak + search_samples, len(signal) - 1)

    if end_idx <= t_peak + 2:
        return None

    trailing = signal[t_peak:end_idx]

    # First derivative
    deriv = np.diff(trailing.astype(float))
    if len(deriv) == 0:
        return None

    # Point of maximum downslope (most negative derivative)
    max_slope_idx = int(np.argmin(deriv))
    slope = deriv[max_slope_idx]

    if slope >= 0:
        # No downslope found — T-wave may be inverted; try max positive slope
        max_slope_idx = int(np.argmax(deriv))
        slope = deriv[max_slope_idx]
        if slope == 0:
            return None

    # Tangent line:  y = slope * (x - x0) + y0
    x0 = max_slope_idx
    y0 = trailing[max_slope_idx]

    # Intersection with baseline:  baseline = slope * (x_end - x0) + y0
    if slope == 0:
        return None
    x_end = x0 + (baseline - y0) / slope

    t_end_sample = t_peak + int(round(x_end))

    # Sanity: T-end must be after T-peak and within signal bounds
    if t_end_sample <= t_peak or t_end_sample >= len(signal):
        return None

    return t_end_sample
