"""Additional unit tests for ecg_analytics.baseline covering uncovered branches."""

import pandas as pd
import pytest

from ecg_analytics.baseline import baseline_summary


def test_baseline_summary_raises_on_missing_qtc_column():
    df = pd.DataFrame({"subject_id": ["A"], "value": [400.0]})
    with pytest.raises(ValueError, match="Missing required column"):
        baseline_summary(df)


def test_baseline_summary_raises_on_missing_group_columns():
    df = pd.DataFrame({"qtc_ms": [400.0]})
    with pytest.raises(ValueError, match="Missing required column"):
        baseline_summary(df, group_columns="nonexistent_col")


def test_baseline_summary_raises_on_multiple_missing_group_columns():
    df = pd.DataFrame({"qtc_ms": [400.0]})
    with pytest.raises(ValueError, match="Missing required column"):
        baseline_summary(df, group_columns=["col_a", "col_b"])


def test_baseline_summary_with_multiple_group_columns():
    df = pd.DataFrame({
        "subject_id": ["A", "A", "A", "B"],
        "visit": [1, 1, 2, 1],
        "qtc_ms": [400.0, 410.0, 430.0, 450.0],
    })

    summary = baseline_summary(df, group_columns=["subject_id", "visit"])

    assert len(summary) == 3
    row_a1 = summary[(summary["subject_id"] == "A") & (summary["visit"] == 1)]
    assert row_a1["count"].item() == 2
    assert row_a1["mean"].item() == 405.0


def test_baseline_summary_with_custom_qtc_column():
    df = pd.DataFrame({
        "subject_id": ["A", "A"],
        "my_qtc": [400.0, 420.0],
    })

    summary = baseline_summary(df, qtc_column="my_qtc")

    assert summary["count"].item() == 2
    assert summary["mean"].item() == 410.0


def test_baseline_summary_computes_all_aggregations():
    df = pd.DataFrame({
        "subject_id": ["A", "A", "A"],
        "qtc_ms": [400.0, 410.0, 420.0],
    })

    summary = baseline_summary(df)

    assert set(summary.columns) == {
        "subject_id", "count", "mean", "median", "std", "min", "max",
    }
    assert summary["min"].item() == 400.0
    assert summary["max"].item() == 420.0
    assert summary["median"].item() == 410.0
