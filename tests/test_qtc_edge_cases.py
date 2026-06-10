"""Additional unit tests for ecg_analytics.qtc covering uncovered branches."""

import numpy as np
import pandas as pd
import pytest

from ecg_analytics.qtc import (
    qtc_bazett,
    qtc_framingham,
    qtc_fridericia,
    qtc_hodges,
)


# ---------------------------------------------------------------------------
# Hodges validation (lines 46, 48 — uncovered)
# ---------------------------------------------------------------------------

def test_qtc_hodges_rejects_non_positive_qt():
    with pytest.raises(ValueError, match="QT intervals"):
        qtc_hodges([0.0], [72.0])


def test_qtc_hodges_rejects_negative_qt():
    with pytest.raises(ValueError, match="QT intervals"):
        qtc_hodges([-10.0], [72.0])


def test_qtc_hodges_rejects_non_positive_heart_rate():
    with pytest.raises(ValueError, match="Heart rates"):
        qtc_hodges([400.0], [0.0])


def test_qtc_hodges_rejects_negative_heart_rate():
    with pytest.raises(ValueError, match="Heart rates"):
        qtc_hodges([400.0], [-5.0])


# ---------------------------------------------------------------------------
# Array-type input variants
# ---------------------------------------------------------------------------

def test_qtc_bazett_with_scalar_inputs():
    result = qtc_bazett(400.0, 1000.0)
    np.testing.assert_allclose(result, 400.0)


def test_qtc_fridericia_with_pandas_series():
    qt = pd.Series([400.0, 420.0])
    rr = pd.Series([1000.0, 1000.0])
    result = qtc_fridericia(qt, rr)
    np.testing.assert_allclose(result, [400.0, 420.0])


def test_qtc_framingham_correction_direction():
    """When RR < 1000 ms (faster HR), Framingham correction should increase QTc."""
    result = qtc_framingham(400.0, 800.0)
    assert result > 400.0


def test_qtc_hodges_correction_at_higher_heart_rate():
    """At HR > 60 bpm, Hodges correction should increase QTc."""
    result = qtc_hodges(400.0, 80.0)
    expected = 400.0 + 1.75 * (80.0 - 60.0)
    np.testing.assert_allclose(result, expected)


def test_qtc_hodges_correction_at_lower_heart_rate():
    """At HR < 60 bpm, Hodges correction should decrease QTc."""
    result = qtc_hodges(400.0, 50.0)
    expected = 400.0 + 1.75 * (50.0 - 60.0)
    np.testing.assert_allclose(result, expected)
    assert result < 400.0


def test_qtc_bazett_rejects_zero_rr():
    with pytest.raises(ValueError, match="RR intervals"):
        qtc_bazett([400.0], [0.0])


def test_qtc_framingham_rejects_non_positive_qt():
    with pytest.raises(ValueError, match="QT intervals"):
        qtc_framingham([-1.0], [1000.0])
