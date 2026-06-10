"""Formula-agreement sub-score for the confidence engine.

Compares QTc values from all four correction formulas and quantifies
how sensitive the result is to formula selection.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from ..qtc.formulas import compute_all_qtc


@dataclass
class FormulaAgreementResult:
    """Results of QTc formula comparison for a single beat.

    Attributes
    ----------
    qtc_values : dict[str, float]
        QTc (ms) per formula.
    spread_ms : float
        Range (max − min) across formulas.
    mean_qtc_ms : float
        Mean QTc across formulas.
    sd_qtc_ms : float
        Standard deviation across formulas.
    agreement_score : float
        0–100 score (higher = better agreement).
    """

    qtc_values: dict[str, float]
    spread_ms: float
    mean_qtc_ms: float
    sd_qtc_ms: float
    agreement_score: float


def formula_agreement_score(qt_ms: float, rr_ms: float) -> FormulaAgreementResult:
    """Compute formula agreement for a single beat.

    Scoring (explainable):
      - Perfect agreement (spread = 0): score = 100
      - Spread of 10 ms: score ≈ 80
      - Spread of 30 ms: score ≈ 40
      - Spread ≥ 50 ms: score → 0
    """
    all_qtc = compute_all_qtc(qt_ms, rr_ms)
    values = {k: float(v) for k, v in all_qtc.items()}

    vals_arr = np.array(list(values.values()))
    spread = float(np.max(vals_arr) - np.min(vals_arr))
    mean_qtc = float(np.mean(vals_arr))
    sd_qtc = float(np.std(vals_arr, ddof=0))

    # Linear mapping: 0 spread → 100, 50 spread → 0
    score = max(0.0, 100.0 - spread * 2.0)

    return FormulaAgreementResult(
        qtc_values=values,
        spread_ms=spread,
        mean_qtc_ms=mean_qtc,
        sd_qtc_ms=sd_qtc,
        agreement_score=score,
    )
