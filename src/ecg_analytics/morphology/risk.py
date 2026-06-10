"""Morphology-based measurement risk scoring.

Maps T-wave morphology classes to measurement difficulty / risk, producing
a *Morphology Risk Score* that feeds into the overall confidence engine.
"""

from __future__ import annotations

# Risk weights: higher → more difficult to measure T-end reliably.
MORPHOLOGY_RISK_WEIGHTS: dict[str, float] = {
    "normal": 0.0,
    "flat": 1.0,
    "low_amplitude": 0.7,
    "biphasic": 0.6,
    "notched": 0.8,
    "merged_tu": 0.9,
}


def morphology_risk_score(
    morphology: str,
    classification_confidence: float = 1.0,
) -> float:
    """Compute a 0–100 risk score based on T-wave morphology.

    Higher scores indicate greater measurement difficulty (risk).

    Parameters
    ----------
    morphology : str
        Morphology class name (e.g. ``"normal"``, ``"biphasic"``).
    classification_confidence : float
        Confidence of the morphology classifier (0–1).  Lower classifier
        confidence increases the risk score slightly.

    Returns
    -------
    float
        Risk score in [0, 100].
    """
    weight = MORPHOLOGY_RISK_WEIGHTS.get(morphology, 0.5)

    # Uncertainty bump: low classifier confidence adds risk
    uncertainty_penalty = (1.0 - classification_confidence) * 0.2

    raw_risk = weight + uncertainty_penalty
    return float(min(100.0, raw_risk * 100.0))
