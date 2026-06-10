"""Signal-quality sub-score for the confidence engine.

Wraps the existing :func:`~ecg_analytics.preprocessing.quality.signal_quality_index`
and maps its output to a 0–100 sub-score.
"""

from __future__ import annotations

import numpy as np

from ..preprocessing.quality import signal_quality_index


def signal_quality_subscore(signal: np.ndarray, fs: float) -> float:
    """Compute a 0–100 signal-quality sub-score.

    Scoring (fully explainable):
      - SNR contribution: 0–50 points, linear from 0 dB (0 pts) to 30 dB (50 pts)
      - Flatline penalty: lose up to 25 points as flatline fraction approaches 1
      - Kurtosis penalty: lose up to 15 points for extreme kurtosis (>10)
      - Drift penalty: lose up to 10 points for baseline drift > 1 mV
    """
    sqi = signal_quality_index(signal, fs)

    snr = sqi["snr_db"]
    if np.isinf(snr):
        snr = 30.0
    snr_score = np.clip(snr / 30.0 * 50.0, 0.0, 50.0)

    flatline_penalty = sqi["flatline_fraction"] * 25.0

    kurt = abs(sqi["kurtosis"])
    kurt_penalty = min(15.0, max(0.0, (kurt - 3.0) / 7.0 * 15.0))

    drift = sqi["baseline_drift"]
    drift_penalty = min(10.0, drift / 1.0 * 10.0)

    score = snr_score + 50.0 - flatline_penalty - kurt_penalty - drift_penalty
    return float(np.clip(score, 0.0, 100.0))
