"""Tests for QTc formulas and longitudinal tracking."""

import numpy as np
import pandas as pd
import pytest

from ecg_analytics.qtc.formulas import (
    compute_all_qtc,
    qtc_bazett,
    qtc_framingham,
    qtc_fridericia,
    qtc_hodges,
)
from ecg_analytics.qtc.longitudinal import (
    QTcShiftResult,
    compute_qtc_shift,
    subject_drift_summary,
)


class TestFormulas:
    def test_fridericia_at_rr_1000(self):
        result = qtc_fridericia(400.0, 1000.0)
        np.testing.assert_allclose(result, 400.0)

    def test_bazett_at_rr_1000(self):
        result = qtc_bazett(400.0, 1000.0)
        np.testing.assert_allclose(result, 400.0)

    def test_framingham_at_rr_1000(self):
        result = qtc_framingham(400.0, 1000.0)
        np.testing.assert_allclose(result, 400.0)

    def test_hodges_at_hr_60(self):
        result = qtc_hodges(400.0, 60.0)
        np.testing.assert_allclose(result, 400.0)

    def test_vectorised(self):
        qt = np.array([380, 400, 420], dtype=float)
        rr = np.array([800, 1000, 1200], dtype=float)
        result = qtc_fridericia(qt, rr)
        assert result.shape == (3,)

    def test_negative_qt_raises(self):
        with pytest.raises(ValueError, match="QT"):
            qtc_bazett(-1.0, 1000.0)

    def test_negative_rr_raises(self):
        with pytest.raises(ValueError, match="RR"):
            qtc_fridericia(400.0, -1.0)

    def test_compute_all_returns_four_formulas(self):
        result = compute_all_qtc(400.0, 800.0)
        assert set(result.keys()) == {"fridericia", "bazett", "framingham", "hodges"}
        for val in result.values():
            assert float(val) > 0


class TestLongitudinal:
    def test_compute_qtc_shift(self):
        result = compute_qtc_shift(420.0, 490.0, subject_id="S001", threshold_ms=60.0)
        assert isinstance(result, QTcShiftResult)
        assert result.delta_qtc == pytest.approx(70.0)
        assert result.exceeds_threshold is True

    def test_shift_below_threshold(self):
        result = compute_qtc_shift(420.0, 440.0, threshold_ms=60.0)
        assert result.exceeds_threshold is False

    def test_subject_drift_summary(self):
        rows = []
        for s in ["A", "B"]:
            for tp in range(3):
                rows.append({"subject_id": s, "time_point": tp, "qtc_fridericia": 400 + tp * 30})
        df = pd.DataFrame(rows)
        summary = subject_drift_summary(df, baseline_time=0)
        assert len(summary) == 2
        assert "delta_qtc" in summary.columns
        assert "exceeds_threshold" in summary.columns
