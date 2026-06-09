"""Digital filters for ECG signal conditioning."""

from __future__ import annotations

import numpy as np
from scipy.signal import butter, filtfilt, iirnotch


def bandpass_filter(
    signal: np.ndarray, fs: float, low: float = 0.5, high: float = 40.0, order: int = 4
) -> np.ndarray:
    """Zero-phase Butterworth bandpass filter.

    Parameters
    ----------
    signal : np.ndarray
        1-D ECG signal.
    fs : float
        Sampling frequency in Hz.
    low, high : float
        Cut-off frequencies in Hz.
    order : int
        Filter order (applied twice via *filtfilt*).
    """
    nyq = fs / 2.0
    b, a = butter(order, [low / nyq, high / nyq], btype="band")
    return filtfilt(b, a, signal).astype(signal.dtype)


def highpass_filter(
    signal: np.ndarray, fs: float, cutoff: float = 0.5, order: int = 4
) -> np.ndarray:
    """Zero-phase Butterworth highpass filter for baseline wander removal."""
    nyq = fs / 2.0
    b, a = butter(order, cutoff / nyq, btype="high")
    return filtfilt(b, a, signal).astype(signal.dtype)


def notch_filter(
    signal: np.ndarray, fs: float, freq: float = 50.0, quality: float = 30.0
) -> np.ndarray:
    """Notch (band-stop) filter for powerline interference removal.

    Parameters
    ----------
    freq : float
        Frequency to reject (50 Hz or 60 Hz).
    quality : float
        Quality factor of the notch.
    """
    b, a = iirnotch(freq, quality, fs)
    return filtfilt(b, a, signal).astype(signal.dtype)


def remove_baseline_wander(
    signal: np.ndarray, fs: float, cutoff: float = 0.5, order: int = 4
) -> np.ndarray:
    """Remove baseline wander using a highpass filter.

    This is a convenience alias for :func:`highpass_filter` with the default
    clinical cutoff of 0.5 Hz.
    """
    return highpass_filter(signal, fs, cutoff=cutoff, order=order)
