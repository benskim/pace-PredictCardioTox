"""End-to-end QT interval measurement combining R-peak detection,
T-wave analysis, and the tangent method.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks

from .t_wave import extract_t_wave_region, find_t_peak
from .tangent import tangent_t_end


@dataclass
class QTMeasurement:
    """Single-beat QT measurement result."""

    r_peak: int
    q_onset: int | None
    t_end: int | None
    t_peak: int | None
    qt_samples: int | None
    qt_ms: float | None
    rr_ms: float | None


def _detect_r_peaks(signal: np.ndarray, fs: float) -> np.ndarray:
    """Simple R-peak detector using amplitude thresholding.

    This is a supporting component — not the focus of the repository.
    For production use, replace with a validated detector.
    """
    min_distance = int(0.3 * fs)  # minimum 300 ms between beats
    threshold = 0.5 * np.std(signal)
    peaks, _ = find_peaks(signal, height=threshold, distance=min_distance)
    return peaks


def _estimate_q_onset(
    signal: np.ndarray, r_peak: int, fs: float, window_ms: float = 80.0
) -> int:
    """Estimate QRS onset (Q) as the minimum before the R-peak."""
    window = int(window_ms * fs / 1000)
    start = max(0, r_peak - window)
    segment = signal[start:r_peak]
    if len(segment) == 0:
        return r_peak
    return int(start + np.argmin(segment))


def measure_qt_intervals(
    signal: np.ndarray,
    fs: float,
    r_peaks: np.ndarray | None = None,
    baseline: float = 0.0,
) -> list[QTMeasurement]:
    """Measure QT intervals for every beat in a single-lead signal.

    Parameters
    ----------
    signal : np.ndarray
        1-D ECG signal.
    fs : float
        Sampling frequency in Hz.
    r_peaks : np.ndarray | None
        Pre-detected R-peak indices.  If ``None``, a built-in detector
        is used.
    baseline : float
        Isoelectric baseline value for the tangent method.

    Returns
    -------
    list[QTMeasurement]
    """
    if r_peaks is None:
        r_peaks = _detect_r_peaks(signal, fs)

    results: list[QTMeasurement] = []
    for i, rp in enumerate(r_peaks):
        rp = int(rp)
        # RR interval
        rr_ms: float | None = None
        if i > 0:
            rr_ms = (rp - int(r_peaks[i - 1])) / fs * 1000

        # Q-onset
        q_onset = _estimate_q_onset(signal, rp, fs)

        # T-wave region
        t_start, t_end_search = extract_t_wave_region(signal, rp, fs)
        t_peak = find_t_peak(signal, t_start, t_end_search)

        t_end: int | None = None
        if t_peak is not None:
            t_end = tangent_t_end(signal, t_peak, fs, baseline=baseline)

        qt_samples: int | None = None
        qt_ms: float | None = None
        if t_end is not None:
            qt_samples = t_end - q_onset
            qt_ms = qt_samples / fs * 1000

        results.append(
            QTMeasurement(
                r_peak=rp,
                q_onset=q_onset,
                t_end=t_end,
                t_peak=t_peak,
                qt_samples=qt_samples,
                qt_ms=qt_ms,
                rr_ms=rr_ms,
            )
        )

    return results
