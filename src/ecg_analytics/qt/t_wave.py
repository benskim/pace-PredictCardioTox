"""T-wave region extraction and peak detection utilities."""

from __future__ import annotations

import numpy as np
from scipy.signal import find_peaks


def find_t_peak(
    signal: np.ndarray,
    search_start: int,
    search_end: int,
) -> int | None:
    """Find the T-wave peak within a search window.

    The T-peak is identified as the maximum-amplitude local peak between
    *search_start* and *search_end* (sample indices).

    Returns ``None`` if no peak is found.
    """
    window = signal[search_start:search_end]
    if len(window) < 3:
        return None

    peaks, properties = find_peaks(window, distance=5)
    if len(peaks) == 0:
        # Fall back to global max in the window
        return int(search_start + np.argmax(np.abs(window)))

    # Select the most prominent peak
    heights = np.abs(window[peaks])
    best = peaks[int(np.argmax(heights))]
    return int(search_start + best)


def extract_t_wave_region(
    signal: np.ndarray,
    r_peak: int,
    fs: float,
    qrs_end_offset_ms: float = 80.0,
    t_search_window_ms: float = 400.0,
) -> tuple[int, int]:
    """Return the (start, end) sample indices of the expected T-wave region.

    The search window begins ``qrs_end_offset_ms`` after the R-peak and
    extends for ``t_search_window_ms``.

    Parameters
    ----------
    signal : np.ndarray
        1-D ECG signal (used for bounds checking only).
    r_peak : int
        Sample index of the R-peak.
    fs : float
        Sampling frequency in Hz.
    qrs_end_offset_ms : float
        Milliseconds after R-peak where the QRS is assumed to have ended.
    t_search_window_ms : float
        Width of the T-wave search window in ms.
    """
    start = r_peak + int(qrs_end_offset_ms * fs / 1000)
    end = start + int(t_search_window_ms * fs / 1000)
    end = min(end, len(signal))
    return start, end
