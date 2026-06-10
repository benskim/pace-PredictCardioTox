"""Wavelet-based T-end determination.

Uses a Continuous Wavelet Transform (CWT) to detect the modulus-maxima
pattern on the trailing edge of the T-wave.  The last significant
modulus maximum before the signal returns to baseline is taken as T-end.
"""

from __future__ import annotations

import numpy as np


def _ricker(points: int, a: float) -> np.ndarray:
    """Ricker (Mexican-hat) wavelet — standalone implementation."""
    A = 2.0 / (np.sqrt(3 * a) * (np.pi ** 0.25))
    wsq = a ** 2
    vec = np.arange(0, points) - (points - 1.0) / 2
    tsq = vec ** 2
    mod = 1 - tsq / wsq
    gauss = np.exp(-tsq / (2 * wsq))
    return A * mod * gauss


def _cwt_single_scale(data: np.ndarray, width: int) -> np.ndarray:
    """Compute CWT at a single Ricker-wavelet scale via convolution."""
    n_wavelet = min(10 * width, len(data))
    if n_wavelet < 1:
        n_wavelet = 1
    wavelet_data = _ricker(n_wavelet, float(width))
    return np.convolve(data, wavelet_data, mode="same")


def wavelet_t_end(
    signal: np.ndarray,
    t_peak: int,
    fs: float,
    search_window_ms: float = 200.0,
    wavelet_width_ms: float = 40.0,
    energy_threshold_fraction: float = 0.10,
) -> int | None:
    """Determine T-end via CWT modulus-maxima analysis.

    Parameters
    ----------
    signal : np.ndarray
        1-D ECG signal.
    t_peak : int
        Sample index of the T-wave peak.
    fs : float
        Sampling frequency in Hz.
    search_window_ms : float
        How far past the T-peak to search (ms).
    wavelet_width_ms : float
        Width parameter of the Ricker (Mexican-hat) wavelet in ms.
    energy_threshold_fraction : float
        Fraction of peak CWT energy below which the T-wave is considered
        to have ended.

    Returns
    -------
    int | None
        Sample index of T-end, or ``None`` if not found.
    """
    search_samples = int(search_window_ms * fs / 1000)
    end_idx = min(t_peak + search_samples, len(signal))

    if end_idx <= t_peak + 4:
        return None

    trailing = signal[t_peak:end_idx].astype(float)
    width_samples = max(1, int(wavelet_width_ms * fs / 1000))

    # CWT with a single Ricker wavelet scale
    coefficients = _cwt_single_scale(trailing, width_samples)
    energy = np.abs(coefficients)

    peak_energy = np.max(energy)
    if peak_energy < 1e-12:
        return None

    threshold = energy_threshold_fraction * peak_energy

    # Walk from end backwards to find last above-threshold point
    for i in range(len(energy) - 1, 0, -1):
        if energy[i] >= threshold:
            t_end_sample = t_peak + i
            if t_end_sample < len(signal):
                return t_end_sample
            return None

    return None
