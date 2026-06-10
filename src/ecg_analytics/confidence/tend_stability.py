"""T-end stability sub-score for the confidence engine.

Wraps the T-end agreement framework to produce a 0–100 sub-score
reflecting how consistently the four T-end methods agree.
"""

from __future__ import annotations

from ..tend.agreement import TEndAgreement


def tend_stability_subscore(agreement: TEndAgreement) -> float:
    """Convert a :class:`TEndAgreement` into a 0–100 sub-score.

    Directly uses the stability_score already computed by the
    agreement framework.
    """
    return agreement.stability_score
