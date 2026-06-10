"""Signal quality assessment utilities."""

from __future__ import annotations

import numpy as np


def snr_estimate(signal: np.ndarray, noise: np.ndarray | None = None) -> float:
    """Estimate signal-to-noise ratio in dB.

    If *noise* is not given, the noise is estimated as the high-frequency
    residual after a simple moving-average smoothing.
    """
    if noise is None:
        kernel_size = max(3, len(signal) // 100)
        smooth = np.convolve(signal, np.ones(kernel_size) / kernel_size, mode="same")
        noise = signal - smooth
    sig_power = np.mean(signal ** 2)
    noise_power = np.mean(noise ** 2)
    if noise_power == 0:
        return float("inf")
    return float(10 * np.log10(sig_power / noise_power))


def signal_quality_index(signal: np.ndarray, fs: float) -> dict[str, float]:
    """Compute a set of signal quality features.

    Returns a dictionary with:

    * ``snr_db`` — estimated SNR
    * ``kurtosis`` — signal kurtosis (high → spiky artifacts)
    * ``baseline_drift`` — range of the low-frequency envelope (mV)
    * ``flatline_fraction`` — fraction of samples with near-zero derivative
    """
    from scipy.stats import kurtosis as _kurtosis

    snr = snr_estimate(signal)
    kurt = float(_kurtosis(signal, fisher=True))

    # Baseline drift: range of a heavily smoothed version
    kernel = max(1, int(fs * 2))
    smooth = np.convolve(signal, np.ones(kernel) / kernel, mode="same")
    drift = float(np.ptp(smooth))

    # Flatline detection
    diff = np.abs(np.diff(signal))
    threshold = 0.01 * np.std(signal) if np.std(signal) > 0 else 1e-8
    flatline = float(np.mean(diff < threshold))

    return {
        "snr_db": snr,
        "kurtosis": kurt,
        "baseline_drift": drift,
        "flatline_fraction": flatline,
    }
