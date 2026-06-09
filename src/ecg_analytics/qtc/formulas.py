"""QTc correction formulas.

All four standard formulas are implemented:

* **Fridericia** (default reporting formula)
* **Bazett**
* **Framingham**
* **Hodges**
"""

from __future__ import annotations

import numpy as np

from .._helpers import Numeric, to_positive_array


def _validate(qt_ms: Numeric, rr_ms: Numeric) -> tuple[np.ndarray, np.ndarray]:
    qt = to_positive_array(qt_ms, "QT intervals")
    rr = to_positive_array(rr_ms, "RR intervals")
    return qt, rr


def qtc_fridericia(qt_ms: Numeric, rr_ms: Numeric) -> np.ndarray:
    """Fridericia correction: QT / RR^(1/3), with RR in seconds."""
    qt, rr = _validate(qt_ms, rr_ms)
    return qt / np.cbrt(rr / 1000.0)


def qtc_bazett(qt_ms: Numeric, rr_ms: Numeric) -> np.ndarray:
    """Bazett correction: QT / sqrt(RR), with RR in seconds."""
    qt, rr = _validate(qt_ms, rr_ms)
    return qt / np.sqrt(rr / 1000.0)


def qtc_framingham(qt_ms: Numeric, rr_ms: Numeric) -> np.ndarray:
    """Framingham correction: QT + 154 * (1 - RR_s)."""
    qt, rr = _validate(qt_ms, rr_ms)
    return qt + 154.0 * (1.0 - rr / 1000.0)


def qtc_hodges(qt_ms: Numeric, heart_rate_bpm: Numeric) -> np.ndarray:
    """Hodges correction: QT + 1.75 * (HR - 60)."""
    qt = to_positive_array(qt_ms, "QT intervals")
    hr = to_positive_array(heart_rate_bpm, "Heart rates")
    return qt + 1.75 * (hr - 60.0)


def compute_all_qtc(qt_ms: Numeric, rr_ms: Numeric) -> dict[str, np.ndarray]:
    """Compute all four QTc corrections simultaneously.

    Returns a dict keyed by formula name.  Heart rate for Hodges is
    derived from the RR interval.
    """
    rr = to_positive_array(rr_ms, "RR intervals")
    hr_bpm = 60_000.0 / rr
    return {
        "fridericia": qtc_fridericia(qt_ms, rr_ms),
        "bazett": qtc_bazett(qt_ms, rr_ms),
        "framingham": qtc_framingham(qt_ms, rr_ms),
        "hodges": qtc_hodges(qt_ms, hr_bpm),
    }
