"""Composite Measurement Confidence Score (0–100).

Aggregates all sub-scores into a single explainable confidence metric
with defined interpretation tiers.

Tiers
-----
90–100  High Confidence
70–89   Review Recommended
<70     Manual Review Required
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


# Default sub-score weights (sum to 1.0)
DEFAULT_WEIGHTS: dict[str, float] = {
    "signal_quality": 0.20,
    "tend_stability": 0.25,
    "morphology": 0.15,
    "formula_agreement": 0.15,
    "beat_stability": 0.25,
}


@dataclass
class ConfidenceResult:
    """Composite measurement confidence result.

    Attributes
    ----------
    score : float
        Final confidence score (0–100).
    tier : str
        Interpretation: ``"high"``, ``"review"``, or ``"manual_review"``.
    sub_scores : dict[str, float]
        Individual component sub-scores (0–100).
    weights : dict[str, float]
        Weights applied to each sub-score.
    """

    score: float
    tier: str
    sub_scores: dict[str, float] = field(default_factory=dict)
    weights: dict[str, float] = field(default_factory=dict)


def _tier(score: float) -> str:
    if score >= 90.0:
        return "high"
    if score >= 70.0:
        return "review"
    return "manual_review"


def measurement_confidence(
    signal_quality: float = 100.0,
    tend_stability: float = 100.0,
    morphology: float = 100.0,
    formula_agreement: float = 100.0,
    beat_stability: float = 100.0,
    weights: dict[str, float] | None = None,
) -> ConfidenceResult:
    """Compute the composite Measurement Confidence Score.

    All inputs are 0–100 sub-scores.  The output is a weighted average,
    clipped to [0, 100].

    Parameters
    ----------
    signal_quality, tend_stability, morphology, formula_agreement, beat_stability
        Sub-scores (0–100).
    weights : dict | None
        Custom weights keyed by sub-score name.  Defaults to
        :data:`DEFAULT_WEIGHTS`.

    Returns
    -------
    ConfidenceResult
    """
    w = weights or DEFAULT_WEIGHTS
    sub = {
        "signal_quality": signal_quality,
        "tend_stability": tend_stability,
        "morphology": morphology,
        "formula_agreement": formula_agreement,
        "beat_stability": beat_stability,
    }

    total_weight = sum(w.get(k, 0.0) for k in sub)
    if total_weight == 0:
        total_weight = 1.0

    score = sum(sub[k] * w.get(k, 0.0) for k in sub) / total_weight
    score = float(np.clip(score, 0.0, 100.0))

    return ConfidenceResult(
        score=score,
        tier=_tier(score),
        sub_scores=sub,
        weights=dict(w),
    )
