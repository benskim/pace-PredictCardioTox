import pandas as pd

from ecg_analytics.alerts import AlertRule, generate_qtc_alerts
from ecg_analytics.baseline import baseline_summary


def test_generate_qtc_alerts_flags_absolute_and_delta_thresholds():
    measurements = pd.DataFrame(
        {
            "subject_id": ["A", "B", "C"],
            "qtc_ms": [480.0, 501.0, 470.0],
            "baseline_qtc_ms": [430.0, 460.0, 405.0],
        }
    )

    alerts = generate_qtc_alerts(measurements, AlertRule())

    assert alerts["subject_id"].tolist() == ["B", "C"]
    assert alerts["absolute_qtc_alert"].tolist() == [True, False]
    assert alerts["delta_qtc_alert"].tolist() == [False, True]


def test_baseline_summary_groups_measurements():
    measurements = pd.DataFrame(
        {
            "subject_id": ["A", "A", "B"],
            "qtc_ms": [400.0, 420.0, 450.0],
        }
    )

    summary = baseline_summary(measurements)

    assert summary.loc[summary["subject_id"] == "A", "count"].item() == 2
    assert summary.loc[summary["subject_id"] == "A", "mean"].item() == 410.0
