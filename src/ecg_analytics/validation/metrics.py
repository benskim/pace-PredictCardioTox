"""Validation metrics for delineation, QT, QTc, and longitudinal analysis."""

from __future__ import annotations

import numpy as np


def _ensure_array(x: list | np.ndarray) -> np.ndarray:
    return np.asarray(x, dtype=float)


# ------------------------------------------------------------------
# Delineation metrics
# ------------------------------------------------------------------


def delineation_metrics(
    predicted_samples: list | np.ndarray,
    reference_samples: list | np.ndarray,
    fs: float = 1.0,
) -> dict[str, float]:
    """Compute T-end (or any fiducial point) delineation accuracy metrics.

    Parameters
    ----------
    predicted_samples, reference_samples : array-like
        Predicted and reference sample indices.
    fs : float
        Sampling frequency; when > 1 errors are reported in **ms**.

    Returns
    -------
    dict with ``mae_ms``, ``median_error_ms``, ``p95_error_ms``,
    ``mean_error_ms``, ``std_error_ms``.
    """
    pred = _ensure_array(predicted_samples)
    ref = _ensure_array(reference_samples)
    errors_samples = pred - ref
    errors_ms = errors_samples / fs * 1000 if fs > 1 else errors_samples

    abs_errors = np.abs(errors_ms)
    return {
        "mae_ms": float(np.mean(abs_errors)),
        "median_error_ms": float(np.median(errors_ms)),
        "p95_error_ms": float(np.percentile(abs_errors, 95)),
        "mean_error_ms": float(np.mean(errors_ms)),
        "std_error_ms": float(np.std(errors_ms)),
    }


# ------------------------------------------------------------------
# QT metrics
# ------------------------------------------------------------------


def qt_metrics(
    predicted_qt_ms: list | np.ndarray,
    reference_qt_ms: list | np.ndarray,
) -> dict[str, float]:
    """QT measurement accuracy metrics.

    Returns ``mae_ms`` and ``rmse_ms``.
    """
    pred = _ensure_array(predicted_qt_ms)
    ref = _ensure_array(reference_qt_ms)
    errors = pred - ref
    return {
        "mae_ms": float(np.mean(np.abs(errors))),
        "rmse_ms": float(np.sqrt(np.mean(errors ** 2))),
        "mean_error_ms": float(np.mean(errors)),
        "std_error_ms": float(np.std(errors)),
    }


# ------------------------------------------------------------------
# QTc metrics
# ------------------------------------------------------------------


def qtc_metrics(
    predicted_qtc_ms: list | np.ndarray,
    reference_qtc_ms: list | np.ndarray,
) -> dict[str, float]:
    """QTc accuracy metrics. Returns ``mae_ms`` and ``rmse_ms``."""
    pred = _ensure_array(predicted_qtc_ms)
    ref = _ensure_array(reference_qtc_ms)
    errors = pred - ref
    return {
        "mae_ms": float(np.mean(np.abs(errors))),
        "rmse_ms": float(np.sqrt(np.mean(errors ** 2))),
        "mean_error_ms": float(np.mean(errors)),
        "std_error_ms": float(np.std(errors)),
    }


# ------------------------------------------------------------------
# Longitudinal / shift metrics
# ------------------------------------------------------------------


def longitudinal_metrics(
    predicted_delta_qtc: list | np.ndarray,
    reference_delta_qtc: list | np.ndarray,
) -> dict[str, float]:
    """Delta-QTc (shift) accuracy metrics."""
    pred = _ensure_array(predicted_delta_qtc)
    ref = _ensure_array(reference_delta_qtc)
    errors = pred - ref
    return {
        "delta_qtc_mae_ms": float(np.mean(np.abs(errors))),
        "delta_qtc_rmse_ms": float(np.sqrt(np.mean(errors ** 2))),
        "delta_qtc_mean_error_ms": float(np.mean(errors)),
    }
