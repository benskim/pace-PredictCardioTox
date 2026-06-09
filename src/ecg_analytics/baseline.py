"""Baseline summary helpers for ECG validation datasets."""

from __future__ import annotations

import pandas as pd


def baseline_summary(
    measurements: pd.DataFrame,
    group_columns: str | list[str] = "subject_id",
    qtc_column: str = "qtc_ms",
) -> pd.DataFrame:
    """Summarize baseline QTc measurements by subject or cohort grouping."""
    if qtc_column not in measurements.columns:
        raise ValueError(f"Missing required QTc column: {qtc_column}")
    if isinstance(group_columns, str):
        group_columns = [group_columns]
    elif not isinstance(group_columns, list):
        raise TypeError(
            f"group_columns must be a string or list of strings, got {type(group_columns).__name__}"
        )
    missing = [column for column in group_columns if column not in measurements.columns]
    if missing:
        raise ValueError(f"Missing grouping columns: {missing}")

    return (
        measurements.groupby(group_columns, dropna=False)[qtc_column]
        .agg(count="count", mean="mean", median="median", std="std", min="min", max="max")
        .reset_index()
    )
