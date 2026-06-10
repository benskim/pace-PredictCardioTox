"""Tests for the validation module (metrics, pipeline, reports)."""

import numpy as np

from ecg_analytics.validation.metrics import (
    delineation_metrics,
    longitudinal_metrics,
    qt_metrics,
    qtc_metrics,
)
from ecg_analytics.validation.pipeline import ValidationResult
from ecg_analytics.validation.reports import results_to_markdown


class TestMetrics:
    def test_delineation_metrics_perfect(self):
        pred = np.array([100, 200, 300])
        ref = np.array([100, 200, 300])
        m = delineation_metrics(pred, ref, fs=250.0)
        assert m["mae_ms"] == 0.0
        assert m["p95_error_ms"] == 0.0

    def test_delineation_metrics_with_errors(self):
        pred = np.array([102, 198, 305])
        ref = np.array([100, 200, 300])
        m = delineation_metrics(pred, ref, fs=250.0)
        assert m["mae_ms"] > 0

    def test_qt_metrics(self):
        pred = np.array([400.0, 410.0, 390.0])
        ref = np.array([398.0, 412.0, 395.0])
        m = qt_metrics(pred, ref)
        assert "mae_ms" in m
        assert "rmse_ms" in m
        assert m["mae_ms"] > 0

    def test_qtc_metrics(self):
        pred = np.array([440.0, 450.0])
        ref = np.array([438.0, 452.0])
        m = qtc_metrics(pred, ref)
        assert m["mae_ms"] > 0
        assert m["rmse_ms"] > 0

    def test_longitudinal_metrics(self):
        pred = np.array([10.0, 20.0, 30.0])
        ref = np.array([12.0, 18.0, 32.0])
        m = longitudinal_metrics(pred, ref)
        assert "delta_qtc_mae_ms" in m


class TestPipeline:
    def test_validation_result_defaults(self):
        vr = ValidationResult()
        assert vr.dataset == ""
        assert vr.noise_type == "clean"
        assert vr.n_beats == 0


class TestReports:
    def test_results_to_markdown(self):
        r = ValidationResult(dataset="qtdb", n_beats=10, qt={"mae_ms": 5.0, "rmse_ms": 6.0})
        md = results_to_markdown([r])
        assert "qtdb" in md
        assert "5.00" in md
