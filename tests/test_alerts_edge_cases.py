"""Additional unit tests for ecg_analytics.alerts covering uncovered branches."""

import pandas as pd
import pytest

from ecg_analytics.alerts import AlertRule, generate_qtc_alerts


def test_generate_qtc_alerts_raises_on_missing_qtc_column():
    df = pd.DataFrame({"subject_id": ["A"], "some_other": [400.0]})
    with pytest.raises(ValueError, match="Missing required column"):
        generate_qtc_alerts(df)


def test_generate_qtc_alerts_without_baseline_column():
    """When the baseline column is absent, delta alerts should be False and
    delta_qtc_ms should be NA."""
    df = pd.DataFrame({"qtc_ms": [510.0, 400.0]})

    alerts = generate_qtc_alerts(df)

    assert len(alerts) == 1
    assert alerts["absolute_qtc_alert"].iloc[0] == True
    assert alerts["delta_qtc_alert"].iloc[0] == False
    assert pd.isna(alerts["delta_qtc_ms"].iloc[0])


def test_generate_qtc_alerts_with_custom_rule():
    df = pd.DataFrame({
        "my_qtc": [450.0, 350.0],
        "my_baseline": [380.0, 340.0],
    })
    rule = AlertRule(
        absolute_qtc_ms=440.0,
        delta_qtc_ms=50.0,
        qtc_column="my_qtc",
        baseline_column="my_baseline",
    )

    alerts = generate_qtc_alerts(df, rule)

    assert len(alerts) == 1
    assert alerts["my_qtc"].iloc[0] == 450.0
    assert alerts["absolute_qtc_alert"].iloc[0] == True
    assert alerts["delta_qtc_alert"].iloc[0] == True


def test_generate_qtc_alerts_returns_empty_when_no_alerts():
    df = pd.DataFrame({"qtc_ms": [400.0, 420.0], "baseline_qtc_ms": [390.0, 410.0]})

    alerts = generate_qtc_alerts(df)

    assert len(alerts) == 0
