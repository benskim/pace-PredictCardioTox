"""QTc correction formulas.

All four standard formulas are implemented:

* **Fridericia** (default reporting formula)
* **Bazett**
* **Framingham**
* **Hodges**
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def _as_array(values: float | pd.Series | np.ndarray) -> np.ndarray:
    return np.asarray(values, dtype=float)


def _validate(
    qt_ms: float | pd.Series | np.ndarray,
    rr_ms: float | pd.Series | np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    qt = _as_array(qt_ms)
    rr = _as_array(rr_ms)
    if np.any(qt <= 0):
        raise ValueError("QT intervals must be positive milliseconds.")
    if np.any(rr <= 0):
        raise ValueError("RR intervals must be positive milliseconds.")
    return qt, rr


def qtc_fridericia(
    qt_ms: float | pd.Series | np.ndarray,
    rr_ms: float | pd.Series | np.ndarray,
) -> np.ndarray:
    """Fridericia correction: QT / RR^(1/3), with RR in seconds."""
    qt, rr = _validate(qt_ms, rr_ms)
    return qt / np.cbrt(rr / 1000.0)


def qtc_bazett(
    qt_ms: float | pd.Series | np.ndarray,
    rr_ms: float | pd.Series | np.ndarray,
) -> np.ndarray:
    """Bazett correction: QT / sqrt(RR), with RR in seconds."""
    qt, rr = _validate(qt_ms, rr_ms)
    return qt / np.sqrt(rr / 1000.0)


def qtc_framingham(
    qt_ms: float | pd.Series | np.ndarray,
    rr_ms: float | pd.Series | np.ndarray,
) -> np.ndarray:
    """Framingham correction: QT + 154 * (1 - RR_s)."""
    qt, rr = _validate(qt_ms, rr_ms)
    return qt + 154.0 * (1.0 - rr / 1000.0)


def qtc_hodges(
    qt_ms: float | pd.Series | np.ndarray,
    heart_rate_bpm: float | pd.Series | np.ndarray,
) -> np.ndarray:
    """Hodges correction: QT + 1.75 * (HR - 60)."""
    qt = _as_array(qt_ms)
    hr = _as_array(heart_rate_bpm)
    if np.any(qt <= 0):
        raise ValueError("QT intervals must be positive milliseconds.")
    if np.any(hr <= 0):
        raise ValueError("Heart rates must be positive beats per minute.")
    return qt + 1.75 * (hr - 60.0)


def compute_all_qtc(
    qt_ms: float | pd.Series | np.ndarray,
    rr_ms: float | pd.Series | np.ndarray,
) -> dict[str, np.ndarray]:
    """Compute all four QTc corrections simultaneously.

    Returns a dict keyed by formula name.  Heart rate for Hodges is
    derived from the RR interval.
    """
    rr = _as_array(rr_ms)
    hr_bpm = 60_000.0 / rr
    return {
        "fridericia": qtc_fridericia(qt_ms, rr_ms),
        "bazett": qtc_bazett(qt_ms, rr_ms),
        "framingham": qtc_framingham(qt_ms, rr_ms),
        "hodges": qtc_hodges(qt_ms, hr_bpm),
    }
