"""Controlled noise injection for robustness evaluation.

Each function adds a specific noise type to a clean ECG signal at a
given signal-to-noise ratio (SNR) in dB.
"""

from __future__ import annotations

import numpy as np


def _scale_noise(signal: np.ndarray, noise: np.ndarray, snr_db: float) -> np.ndarray:
    """Scale *noise* so that ``signal + scaled_noise`` has the target SNR."""
    sig_power = np.mean(signal ** 2)
    noise_power = np.mean(noise ** 2)
    if noise_power == 0:
        return noise
    target_noise_power = sig_power / (10 ** (snr_db / 10))
    return noise * np.sqrt(target_noise_power / noise_power)


def add_baseline_wander(
    signal: np.ndarray,
    fs: float,
    snr_db: float = 12.0,
    freq: float = 0.3,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Add sinusoidal baseline wander."""
    rng = rng or np.random.default_rng()
    t = np.arange(len(signal)) / fs
    phase = rng.uniform(0, 2 * np.pi)
    noise = np.sin(2 * np.pi * freq * t + phase)
    return signal + _scale_noise(signal, noise, snr_db)


def add_emg_noise(
    signal: np.ndarray,
    fs: float,
    snr_db: float = 12.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Add band-limited Gaussian noise simulating muscle EMG artifacts."""
    rng = rng or np.random.default_rng()
    noise = rng.standard_normal(len(signal))
    # Band-limit to ~20–500 Hz via simple spectral mask
    from scipy.signal import butter, filtfilt

    nyq = fs / 2.0
    low = min(20.0 / nyq, 0.99)
    high = min(500.0 / nyq, 0.99)
    if low < high:
        b, a = butter(2, [low, high], btype="band")
        noise = filtfilt(b, a, noise)
    return signal + _scale_noise(signal, noise, snr_db)


def add_powerline_noise(
    signal: np.ndarray,
    fs: float,
    snr_db: float = 12.0,
    freq: float = 50.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Add powerline interference at 50 Hz or 60 Hz."""
    rng = rng or np.random.default_rng()
    t = np.arange(len(signal)) / fs
    phase = rng.uniform(0, 2 * np.pi)
    noise = np.sin(2 * np.pi * freq * t + phase)
    return signal + _scale_noise(signal, noise, snr_db)


def add_motion_artifact(
    signal: np.ndarray,
    fs: float,
    snr_db: float = 12.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Add synthetic motion artifact (low-frequency transients)."""
    rng = rng or np.random.default_rng()
    n = len(signal)
    t = np.arange(n) / fs
    # Sum of a few random low-freq components
    noise = np.zeros(n, dtype=float)
    for _ in range(3):
        f = rng.uniform(0.1, 1.5)
        phi = rng.uniform(0, 2 * np.pi)
        amp = rng.uniform(0.5, 1.5)
        noise += amp * np.sin(2 * np.pi * f * t + phi)
    return signal + _scale_noise(signal, noise, snr_db)


# Standard SNR levels for noise robustness experiments
STANDARD_SNR_LEVELS = [24, 18, 12, 6, 0]

# Noise type registry
NOISE_FUNCTIONS = {
    "baseline_wander": add_baseline_wander,
    "emg": add_emg_noise,
    "powerline": add_powerline_noise,
    "motion_artifact": add_motion_artifact,
}


def inject_noise(
    signal: np.ndarray,
    fs: float,
    noise_type: str,
    snr_db: float = 12.0,
    rng: np.random.Generator | None = None,
) -> np.ndarray:
    """Inject noise of a named type.

    Parameters
    ----------
    noise_type : str
        One of ``"baseline_wander"``, ``"emg"``, ``"powerline"``,
        ``"motion_artifact"``.
    """
    fn = NOISE_FUNCTIONS.get(noise_type)
    if fn is None:
        raise ValueError(
            f"Unknown noise type {noise_type!r}. "
            f"Choose from {list(NOISE_FUNCTIONS)}"
        )
    return fn(signal, fs, snr_db=snr_db, rng=rng)
