"""Beat-to-beat QT stability analysis and scoring.

Quantifies how consistent QT interval measurements are across
consecutive beats within a single recording.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class BeatStabilityResult:
    """Beat-level QT statistics and stability score.

    Attributes
    ----------
    n_beats : int
        Number of valid beat measurements.
    mean_qt_ms : float
    median_qt_ms : float
    sd_qt_ms : float
    iqr_qt_ms : float
    cv : float
        Coefficient of variation (SD / mean).
    stability_score : float
        0–100 score (higher = more stable).
    """

    n_beats: int
    mean_qt_ms: float
    median_qt_ms: float
    sd_qt_ms: float
    iqr_qt_ms: float
    cv: float
    stability_score: float


def beat_qt_stats(qt_values_ms: list[float] | np.ndarray) -> dict[str, float]:
    """Compute descriptive statistics for a set of beat-level QT values.

    Returns
    -------
    dict with ``mean``, ``median``, ``sd``, ``iqr``, ``cv``.
    """
    arr = np.array(qt_values_ms, dtype=float)
    if len(arr) == 0:
        return {"mean": 0.0, "median": 0.0, "sd": 0.0, "iqr": 0.0, "cv": 0.0}

    mean = float(np.mean(arr))
    return {
        "mean": mean,
        "median": float(np.median(arr)),
        "sd": float(np.std(arr, ddof=1)) if len(arr) > 1 else 0.0,
        "iqr": float(np.percentile(arr, 75) - np.percentile(arr, 25)),
        "cv": float(np.std(arr, ddof=1) / mean) if mean > 0 and len(arr) > 1 else 0.0,
    }


def beat_stability_score(qt_values_ms: list[float] | np.ndarray) -> BeatStabilityResult:
    """Compute beat-to-beat stability analysis with a 0–100 score.

    Scoring (explainable):
      - CV contribution: 0–60 points.  CV = 0 → 60, CV ≥ 0.15 → 0
      - IQR contribution: 0–25 points.  IQR = 0 → 25, IQR ≥ 30 ms → 0
      - Sample-size bonus: 0–15 points.  ≥10 beats → 15, <3 beats → 0
    """
    arr = np.array(qt_values_ms, dtype=float)
    stats = beat_qt_stats(arr)
    n = len(arr)

    if n == 0:
        return BeatStabilityResult(
            n_beats=0,
            mean_qt_ms=0.0,
            median_qt_ms=0.0,
            sd_qt_ms=0.0,
            iqr_qt_ms=0.0,
            cv=0.0,
            stability_score=0.0,
        )

    cv = stats["cv"]
    iqr = stats["iqr"]

    cv_score = max(0.0, 60.0 * (1.0 - cv / 0.15))
    iqr_score = max(0.0, 25.0 * (1.0 - iqr / 30.0))
    size_bonus = min(15.0, max(0.0, (n - 2) / 8 * 15.0))

    total = min(100.0, cv_score + iqr_score + size_bonus)

    return BeatStabilityResult(
        n_beats=n,
        mean_qt_ms=stats["mean"],
        median_qt_ms=stats["median"],
        sd_qt_ms=stats["sd"],
        iqr_qt_ms=stats["iqr"],
        cv=cv,
        stability_score=total,
    )
