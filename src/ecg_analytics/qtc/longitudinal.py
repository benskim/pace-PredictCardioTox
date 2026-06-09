"""Longitudinal QTc shift tracking and subject-level drift analysis."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass
class QTcShiftResult:
    """Result of a QTc shift calculation for a single subject.

    Attributes
    ----------
    subject_id : str
        Subject identifier.
    baseline_qtc : float
        Mean baseline QTc (ms).
    current_qtc : float
        Current (post-baseline) QTc (ms).
    delta_qtc : float
        Shift from baseline (ms).
    exceeds_threshold : bool
        Whether the shift exceeds the clinical threshold.
    """

    subject_id: str
    baseline_qtc: float
    current_qtc: float
    delta_qtc: float
    exceeds_threshold: bool


def compute_qtc_shift(
    baseline_qtc_ms: float | np.ndarray,
    current_qtc_ms: float | np.ndarray,
    subject_id: str = "",
    threshold_ms: float = 60.0,
) -> QTcShiftResult:
    """Compute the QTc shift for a single subject.

    Parameters
    ----------
    baseline_qtc_ms : float or array
        Baseline QTc values (averaged if array).
    current_qtc_ms : float or array
        Post-baseline QTc values (averaged if array).
    threshold_ms : float
        Clinical significance threshold (default 60 ms).
    """
    bl = float(np.mean(baseline_qtc_ms))
    cur = float(np.mean(current_qtc_ms))
    delta = cur - bl
    return QTcShiftResult(
        subject_id=subject_id,
        baseline_qtc=bl,
        current_qtc=cur,
        delta_qtc=delta,
        exceeds_threshold=abs(delta) >= threshold_ms,
    )


def subject_drift_summary(
    df: pd.DataFrame,
    subject_col: str = "subject_id",
    time_col: str = "time_point",
    qtc_col: str = "qtc_fridericia",
    baseline_time: str | int = 0,
    threshold_ms: float = 60.0,
) -> pd.DataFrame:
    """Summarize QTc drift across subjects from a longitudinal DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        Longitudinal measurements with at least *subject_col*, *time_col*,
        and *qtc_col* columns.
    baseline_time : str | int
        The value in *time_col* that marks the baseline measurement.
    threshold_ms : float
        Clinical significance threshold for delta QTc.

    Returns
    -------
    pd.DataFrame with one row per subject, columns:
        ``subject_id``, ``baseline_qtc``, ``last_qtc``, ``delta_qtc``,
        ``max_delta_qtc``, ``exceeds_threshold``.
    """
    rows: list[dict] = []
    for sid, grp in df.groupby(subject_col):
        bl_mask = grp[time_col] == baseline_time
        if not bl_mask.any():
            continue
        bl_qtc = float(grp.loc[bl_mask, qtc_col].mean())
        last_qtc = float(grp[qtc_col].iloc[-1])
        deltas = grp[qtc_col].values - bl_qtc
        rows.append(
            {
                "subject_id": sid,
                "baseline_qtc": bl_qtc,
                "last_qtc": last_qtc,
                "delta_qtc": last_qtc - bl_qtc,
                "max_delta_qtc": float(np.max(np.abs(deltas))),
                "exceeds_threshold": bool(np.max(np.abs(deltas)) >= threshold_ms),
            }
        )
    return pd.DataFrame(rows)
