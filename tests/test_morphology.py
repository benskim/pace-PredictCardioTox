"""Tests for T-wave morphology classification and risk scoring."""

from __future__ import annotations

import numpy as np
import pytest

from ecg_analytics.morphology.classifier import (
    MORPHOLOGY_TYPES,
    MorphologyResult,
    classify_t_wave,
)
from ecg_analytics.morphology.risk import morphology_risk_score, MORPHOLOGY_RISK_WEIGHTS


def _make_signal(shape: str, fs: float = 500.0) -> tuple[np.ndarray, int, int]:
    """Generate a synthetic T-wave segment embedded in a longer signal.

    Returns (signal, t_start, t_end).
    """
    n = 200
    t = np.linspace(0, 1, n)

    if shape == "normal":
        seg = 0.5 * np.exp(-((t - 0.4) ** 2) / (2 * 0.06**2))
    elif shape == "flat":
        seg = np.full(n, 0.001)
    elif shape == "low_amplitude":
        seg = 0.07 * np.exp(-((t - 0.4) ** 2) / (2 * 0.06**2))
    elif shape == "biphasic":
        seg = 0.4 * np.sin(2 * np.pi * t * 2.5)
    elif shape == "notched":
        seg = 0.5 * np.exp(-((t - 0.3) ** 2) / (2 * 0.04**2))
        seg += 0.4 * np.exp(-((t - 0.6) ** 2) / (2 * 0.04**2))
    else:
        seg = np.zeros(n)

    # Embed in longer signal
    signal = np.zeros(400)
    signal[100:300] = seg
    return signal, 100, 300


class TestClassifyTWave:
    def test_normal_morphology(self) -> None:
        sig, t_start, t_end = _make_signal("normal")
        result = classify_t_wave(sig, t_start, t_end, fs=500.0)
        assert isinstance(result, MorphologyResult)
        assert result.morphology in MORPHOLOGY_TYPES
        assert result.confidence > 0

    def test_flat_morphology(self) -> None:
        sig, t_start, t_end = _make_signal("flat")
        result = classify_t_wave(sig, t_start, t_end, fs=500.0)
        assert result.morphology == "flat"

    def test_low_amplitude_morphology(self) -> None:
        sig, t_start, t_end = _make_signal("low_amplitude")
        result = classify_t_wave(sig, t_start, t_end, fs=500.0)
        assert result.morphology in ("low_amplitude", "flat")

    def test_biphasic_morphology(self) -> None:
        sig, t_start, t_end = _make_signal("biphasic")
        result = classify_t_wave(sig, t_start, t_end, fs=500.0)
        assert result.morphology == "biphasic"

    def test_short_segment_returns_flat(self) -> None:
        sig = np.zeros(10)
        result = classify_t_wave(sig, 2, 5, fs=500.0)
        assert result.morphology == "flat"

    def test_features_populated(self) -> None:
        sig, t_start, t_end = _make_signal("normal")
        result = classify_t_wave(sig, t_start, t_end, fs=500.0)
        assert "amplitude" in result.features


class TestMorphologyRisk:
    def test_normal_low_risk(self) -> None:
        score = morphology_risk_score("normal")
        assert score == pytest.approx(0.0)

    def test_flat_high_risk(self) -> None:
        score = morphology_risk_score("flat")
        assert score == pytest.approx(100.0)

    def test_unknown_morphology(self) -> None:
        score = morphology_risk_score("unknown_type")
        assert 0 <= score <= 100

    def test_low_confidence_increases_risk(self) -> None:
        base = morphology_risk_score("normal", classification_confidence=1.0)
        low_conf = morphology_risk_score("normal", classification_confidence=0.5)
        assert low_conf > base

    def test_all_types_have_weights(self) -> None:
        for morph in MORPHOLOGY_TYPES:
            assert morph in MORPHOLOGY_RISK_WEIGHTS
