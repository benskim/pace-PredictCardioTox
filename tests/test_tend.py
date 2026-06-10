"""Tests for the T-end method agreement framework (src/ecg_analytics/tend/)."""

from __future__ import annotations

import numpy as np
import pytest

from ecg_analytics.tend.threshold import threshold_t_end
from ecg_analytics.tend.derivative import derivative_t_end
from ecg_analytics.tend.wavelet import wavelet_t_end
from ecg_analytics.tend.agreement import (
    TEndAgreement,
    compute_agreement,
    tend_stability_metrics,
    tend_stability_score,
)


def _synthetic_t_wave(fs: float = 500.0, duration_ms: float = 400.0) -> np.ndarray:
    """Positive T-wave: baseline → rise → peak → fall → baseline."""
    n = int(duration_ms * fs / 1000)
    t = np.linspace(0, 1, n)
    # Gaussian-like shape peaking at t=0.4
    signal = np.exp(-((t - 0.4) ** 2) / (2 * 0.05**2))
    return signal


class TestThresholdTEnd:
    def test_finds_t_end_on_synthetic(self) -> None:
        sig = _synthetic_t_wave(fs=500.0)
        t_peak = int(0.4 * len(sig))
        result = threshold_t_end(sig, t_peak, fs=500.0, baseline=0.0)
        assert result is not None
        assert result > t_peak

    def test_returns_none_for_flat_signal(self) -> None:
        sig = np.zeros(200)
        result = threshold_t_end(sig, t_peak=50, fs=500.0)
        assert result is None

    def test_returns_none_if_search_window_too_small(self) -> None:
        sig = _synthetic_t_wave(fs=500.0)
        t_peak = len(sig) - 2
        result = threshold_t_end(sig, t_peak, fs=500.0)
        assert result is None


class TestDerivativeTEnd:
    def test_finds_t_end_on_synthetic(self) -> None:
        sig = _synthetic_t_wave(fs=500.0)
        t_peak = int(0.4 * len(sig))
        result = derivative_t_end(sig, t_peak, fs=500.0)
        assert result is not None
        assert result > t_peak

    def test_returns_none_for_flat(self) -> None:
        sig = np.zeros(200)
        result = derivative_t_end(sig, t_peak=50, fs=500.0)
        assert result is None


class TestWaveletTEnd:
    def test_finds_t_end_on_synthetic(self) -> None:
        sig = _synthetic_t_wave(fs=500.0)
        t_peak = int(0.4 * len(sig))
        result = wavelet_t_end(sig, t_peak, fs=500.0)
        assert result is not None
        assert result > t_peak

    def test_returns_none_for_flat(self) -> None:
        sig = np.zeros(200)
        result = wavelet_t_end(sig, t_peak=50, fs=500.0)
        assert result is None


class TestStabilityMetrics:
    def test_single_value(self) -> None:
        metrics = tend_stability_metrics([350.0])
        assert metrics["sd_ms"] == 0.0
        assert metrics["mean_ms"] == 350.0

    def test_multiple_values(self) -> None:
        metrics = tend_stability_metrics([340.0, 345.0, 350.0, 355.0])
        assert metrics["mean_ms"] == pytest.approx(347.5)
        assert metrics["sd_ms"] > 0
        assert metrics["iqr_ms"] > 0
        assert metrics["range_ms"] == pytest.approx(15.0)

    def test_empty_returns_zeros(self) -> None:
        metrics = tend_stability_metrics([])
        assert metrics["mean_ms"] == 0.0


class TestStabilityScore:
    def test_perfect_agreement(self) -> None:
        metrics = {"sd_ms": 0.0, "range_ms": 0.0}
        score = tend_stability_score(metrics, n_valid=4, n_total=4)
        assert score == 100.0

    def test_no_valid_methods(self) -> None:
        score = tend_stability_score({}, n_valid=0, n_total=4)
        assert score == 0.0

    def test_partial_coverage(self) -> None:
        metrics = {"sd_ms": 0.0, "range_ms": 0.0}
        score = tend_stability_score(metrics, n_valid=2, n_total=4)
        assert 0 < score < 100


class TestComputeAgreement:
    def test_agreement_on_synthetic(self) -> None:
        sig = _synthetic_t_wave(fs=500.0)
        t_peak = int(0.4 * len(sig))
        result = compute_agreement(sig, t_peak, fs=500.0)
        assert isinstance(result, TEndAgreement)
        assert result.stability_score >= 0
        # At least some methods should succeed on a clean synthetic T-wave
        valid = [v for v in result.method_results.values() if v is not None]
        assert len(valid) >= 2
