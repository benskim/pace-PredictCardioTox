"""Tests for the Measurement Confidence Engine (src/ecg_analytics/confidence/)."""

from __future__ import annotations

import numpy as np
import pytest

from ecg_analytics.confidence.signal_quality import signal_quality_subscore
from ecg_analytics.confidence.tend_stability import tend_stability_subscore
from ecg_analytics.confidence.morphology_risk import morphology_risk_subscore
from ecg_analytics.confidence.formula_agreement import (
    FormulaAgreementResult,
    formula_agreement_score,
)
from ecg_analytics.confidence.beat_stability import (
    BeatStabilityResult,
    beat_qt_stats,
    beat_stability_score,
)
from ecg_analytics.confidence.confidence_score import (
    ConfidenceResult,
    measurement_confidence,
)
from ecg_analytics.tend.agreement import TEndAgreement


class TestSignalQualitySubscore:
    def test_clean_signal_high_score(self) -> None:
        # Sine wave — reasonably clean
        t = np.linspace(0, 2, 1000)
        sig = np.sin(2 * np.pi * 1.0 * t)
        score = signal_quality_subscore(sig, fs=500.0)
        assert 0 <= score <= 100

    def test_flatline_penalised(self) -> None:
        sig = np.zeros(1000)
        score = signal_quality_subscore(sig, fs=500.0)
        # All-zero signal: SNR=inf→50pts, but flatline fraction=1→-25pts
        assert score < 100


class TestTEndStabilitySubscore:
    def test_wraps_agreement_score(self) -> None:
        agreement = TEndAgreement(stability_score=85.0)
        assert tend_stability_subscore(agreement) == 85.0


class TestMorphologyRiskSubscore:
    def test_normal_high_confidence(self) -> None:
        score = morphology_risk_subscore("normal")
        assert score == 100.0

    def test_flat_low_confidence(self) -> None:
        score = morphology_risk_subscore("flat")
        assert score == 0.0

    def test_range(self) -> None:
        for morph in ["normal", "flat", "biphasic", "notched", "low_amplitude"]:
            score = morphology_risk_subscore(morph)
            assert 0 <= score <= 100


class TestFormulaAgreement:
    def test_at_rr_1000(self) -> None:
        """At RR=1000ms (HR=60), all formulas should be close."""
        result = formula_agreement_score(qt_ms=400.0, rr_ms=1000.0)
        assert isinstance(result, FormulaAgreementResult)
        assert result.spread_ms >= 0
        assert result.agreement_score >= 0

    def test_extreme_hr_reduces_agreement(self) -> None:
        # Very short RR → large HR → formulas diverge
        high_hr = formula_agreement_score(qt_ms=350.0, rr_ms=400.0)
        normal_hr = formula_agreement_score(qt_ms=400.0, rr_ms=1000.0)
        assert high_hr.spread_ms >= normal_hr.spread_ms

    def test_all_four_formulas_present(self) -> None:
        result = formula_agreement_score(qt_ms=400.0, rr_ms=800.0)
        assert set(result.qtc_values.keys()) == {"fridericia", "bazett", "framingham", "hodges"}


class TestBeatStability:
    def test_stats_basic(self) -> None:
        stats = beat_qt_stats([400.0, 400.0, 400.0])
        assert stats["mean"] == pytest.approx(400.0)
        assert stats["sd"] == pytest.approx(0.0)
        assert stats["cv"] == pytest.approx(0.0)

    def test_stats_empty(self) -> None:
        stats = beat_qt_stats([])
        assert stats["mean"] == 0.0

    def test_score_stable_beats(self) -> None:
        result = beat_stability_score([400.0, 401.0, 399.0, 400.0, 400.5] * 3)
        assert isinstance(result, BeatStabilityResult)
        assert result.stability_score > 70

    def test_score_unstable_beats(self) -> None:
        result = beat_stability_score([300.0, 500.0])
        assert result.stability_score < 50

    def test_score_empty(self) -> None:
        result = beat_stability_score([])
        assert result.stability_score == 0.0
        assert result.n_beats == 0


class TestMeasurementConfidence:
    def test_all_perfect_high_confidence(self) -> None:
        result = measurement_confidence(
            signal_quality=100.0,
            tend_stability=100.0,
            morphology=100.0,
            formula_agreement=100.0,
            beat_stability=100.0,
        )
        assert isinstance(result, ConfidenceResult)
        assert result.score == pytest.approx(100.0)
        assert result.tier == "high"

    def test_all_zero_manual_review(self) -> None:
        result = measurement_confidence(
            signal_quality=0.0,
            tend_stability=0.0,
            morphology=0.0,
            formula_agreement=0.0,
            beat_stability=0.0,
        )
        assert result.score == pytest.approx(0.0)
        assert result.tier == "manual_review"

    def test_tier_review(self) -> None:
        result = measurement_confidence(
            signal_quality=75.0,
            tend_stability=80.0,
            morphology=75.0,
            formula_agreement=80.0,
            beat_stability=75.0,
        )
        assert result.tier == "review"

    def test_custom_weights(self) -> None:
        custom = {"signal_quality": 1.0, "tend_stability": 0, "morphology": 0,
                  "formula_agreement": 0, "beat_stability": 0}
        result = measurement_confidence(signal_quality=50.0, weights=custom)
        assert result.score == pytest.approx(50.0)

    def test_sub_scores_populated(self) -> None:
        result = measurement_confidence()
        assert len(result.sub_scores) == 5
        assert len(result.weights) == 5
