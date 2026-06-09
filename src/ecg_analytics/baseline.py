"""Baseline summary helpers for ECG validation datasets."""

from __future__ import annotations

import pandas as pd

from ._helpers import require_columns


def baseline_summary(
    measurements: pd.DataFrame,
    group_columns: str | list[str] = "subject_id",
    qtc_column: str = "qtc_ms",
) -> pd.DataFrame:
    """Summarize baseline QTc measurements by subject or cohort grouping."""
    if isinstance(group_columns, str):
        group_columns = [group_columns]
    require_columns(measurements, qtc_column, *group_columns)

    return (
        measurements.groupby(group_columns, dropna=False)[qtc_column]
        .agg(count="count", mean="mean", median="median", std="std", min="min", max="max")
        .reset_index()
    )
