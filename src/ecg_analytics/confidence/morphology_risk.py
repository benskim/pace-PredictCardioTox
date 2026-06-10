"""Morphology-risk sub-score for the confidence engine.

Converts a morphology risk score (0–100, higher = riskier) into a
confidence sub-score (0–100, higher = more confident).
"""

from __future__ import annotations

from ..morphology.risk import morphology_risk_score


def morphology_risk_subscore(morphology: str, classification_confidence: float = 1.0) -> float:
    """Compute a 0–100 confidence sub-score from morphology risk.

    A "normal" morphology yields a high sub-score; difficult morphologies
    yield low sub-scores.
    """
    risk = morphology_risk_score(morphology, classification_confidence)
    return max(0.0, 100.0 - risk)
