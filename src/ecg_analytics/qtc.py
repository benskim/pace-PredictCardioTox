"""QT correction formulas used in ECG analytics validation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def _as_array(values: float | pd.Series | np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=float)


def _validate_intervals(qt_ms: float | pd.Series | np.ndarray, rr_ms: float | pd.Series | np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    qt = _as_array(qt_ms)
    rr = _as_array(rr_ms)
    if np.any(qt <= 0):
        raise ValueError("QT intervals must be positive milliseconds.")
    if np.any(rr <= 0):
        raise ValueError("RR intervals must be positive milliseconds.")
    return qt, rr


def qtc_bazett(qt_ms: float | pd.Series | np.ndarray, rr_ms: float | pd.Series | np.ndarray) -> np.ndarray:
    """Calculate QTc with Bazett's formula: QT / sqrt(RR seconds)."""
    qt, rr = _validate_intervals(qt_ms, rr_ms)
    return qt / np.sqrt(rr / 1000.0)


def qtc_fridericia(qt_ms: float | pd.Series | np.ndarray, rr_ms: float | pd.Series | np.ndarray) -> np.ndarray:
    """Calculate QTc with Fridericia's formula: QT / cbrt(RR seconds)."""
    qt, rr = _validate_intervals(qt_ms, rr_ms)
    return qt / np.cbrt(rr / 1000.0)


def qtc_framingham(qt_ms: float | pd.Series | np.ndarray, rr_ms: float | pd.Series | np.ndarray) -> np.ndarray:
    """Calculate QTc with the Framingham correction."""
    qt, rr = _validate_intervals(qt_ms, rr_ms)
    return qt + 154.0 * (1.0 - rr / 1000.0)


def qtc_hodges(qt_ms: float | pd.Series | np.ndarray, heart_rate_bpm: float | pd.Series | np.ndarray) -> np.ndarray:
    """Calculate QTc with Hodges' formula using heart rate in beats per minute."""
    qt = _as_array(qt_ms)
    heart_rate = _as_array(heart_rate_bpm)
    if np.any(qt <= 0):
        raise ValueError("QT intervals must be positive milliseconds.")
    if np.any(heart_rate <= 0):
        raise ValueError("Heart rates must be positive beats per minute.")
    return qt + 1.75 * (heart_rate - 60.0)
