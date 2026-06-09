import numpy as np
import pytest

from ecg_analytics.qtc import qtc_bazett, qtc_framingham, qtc_fridericia, qtc_hodges


def test_qtc_formulas_at_one_second_rr_return_qt_for_rate_based_corrections():
    qt_ms = np.array([400.0, 420.0])
    rr_ms = np.array([1000.0, 1000.0])

    np.testing.assert_allclose(qtc_bazett(qt_ms, rr_ms), qt_ms)
    np.testing.assert_allclose(qtc_fridericia(qt_ms, rr_ms), qt_ms)
    np.testing.assert_allclose(qtc_framingham(qt_ms, rr_ms), qt_ms)
    np.testing.assert_allclose(qtc_hodges(qt_ms, np.array([60.0, 60.0])), qt_ms)


def test_qtc_rejects_non_positive_intervals():
    with pytest.raises(ValueError, match="QT intervals"):
        qtc_bazett([0.0], [1000.0])

    with pytest.raises(ValueError, match="RR intervals"):
        qtc_fridericia([400.0], [-1.0])


def test_qtc_rejects_nan_intervals():
    with pytest.raises(ValueError, match="NaN"):
        qtc_bazett([float("nan")], [1000.0])

    with pytest.raises(ValueError, match="NaN"):
        qtc_fridericia([400.0], [float("nan")])

    with pytest.raises(ValueError, match="NaN"):
        qtc_hodges([float("nan")], [60.0])

    with pytest.raises(ValueError, match="NaN"):
        qtc_hodges([400.0], [float("nan")])


def test_qtc_rejects_non_numeric_input():
    with pytest.raises(TypeError, match="Cannot convert"):
        qtc_bazett(["abc"], [1000.0])
