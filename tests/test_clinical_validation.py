"""Tests for the clinical validation package."""

from __future__ import annotations

import numpy as np
import pytest
import matplotlib

matplotlib.use("Agg")

from ecg_analytics.validation.clinical import (
    BlandAltmanResult,
    bland_altman_analysis,
    plot_clinical_bland_altman,
    plot_coverage_bars,
)


class TestBlandAltmanAnalysis:
    def test_identical_measurements(self) -> None:
        pred = [400.0, 410.0, 420.0]
        ref = [400.0, 410.0, 420.0]
        ba = bland_altman_analysis(pred, ref)
        assert isinstance(ba, BlandAltmanResult)
        assert ba.bias == pytest.approx(0.0)
        assert ba.sd == pytest.approx(0.0)
        assert ba.coverage_5ms == pytest.approx(1.0)
        assert ba.coverage_10ms == pytest.approx(1.0)
        assert ba.coverage_20ms == pytest.approx(1.0)
        assert ba.n == 3

    def test_systematic_bias(self) -> None:
        pred = np.array([405.0, 415.0, 425.0])
        ref = np.array([400.0, 410.0, 420.0])
        ba = bland_altman_analysis(pred, ref)
        assert ba.bias == pytest.approx(5.0)
        assert ba.coverage_5ms == pytest.approx(1.0)
        assert ba.coverage_10ms == pytest.approx(1.0)

    def test_large_errors_low_coverage(self) -> None:
        pred = np.array([400.0, 440.0])
        ref = np.array([400.0, 400.0])
        ba = bland_altman_analysis(pred, ref)
        assert ba.coverage_5ms < 1.0

    def test_limits_of_agreement(self) -> None:
        pred = np.array([400.0, 410.0, 420.0])
        ref = np.array([402.0, 408.0, 418.0])
        ba = bland_altman_analysis(pred, ref)
        assert ba.loa_lower < ba.bias < ba.loa_upper


class TestPlots:
    def test_clinical_bland_altman_plot(self) -> None:
        pred = np.random.normal(400, 10, 50)
        ref = pred + np.random.normal(0, 3, 50)
        fig = plot_clinical_bland_altman(pred, ref)
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)

    def test_coverage_bars_plot(self) -> None:
        ba = BlandAltmanResult(
            bias=2.0, sd=5.0,
            loa_lower=-7.8, loa_upper=11.8,
            coverage_5ms=0.6, coverage_10ms=0.85, coverage_20ms=0.98,
            n=100,
        )
        fig = plot_coverage_bars(ba)
        assert fig is not None
        import matplotlib.pyplot as plt
        plt.close(fig)
