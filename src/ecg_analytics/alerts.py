"""Alert generation utilities for QTc analytics validation."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ._helpers import require_columns


@dataclass(frozen=True)
class AlertRule:
    """Thresholds used to identify QTc safety signals."""

    absolute_qtc_ms: float = 500.0
    delta_qtc_ms: float = 60.0
    qtc_column: str = "qtc_ms"
    baseline_column: str = "baseline_qtc_ms"


def generate_qtc_alerts(measurements: pd.DataFrame, rule: AlertRule | None = None) -> pd.DataFrame:
    """Return rows where QTc exceeds absolute or baseline-adjusted thresholds.

    Parameters
    ----------
    measurements:
        DataFrame containing at least the configured QTc column. If the baseline
        column is present, delta alerts are also evaluated.
    rule:
        Optional alert rule. Defaults to conservative validation thresholds of
        QTc >= 500 ms or QTc increase >= 60 ms from baseline.
    """
    rule = rule or AlertRule()
    require_columns(measurements, rule.qtc_column)

    alerts = measurements.copy()
    alerts["absolute_qtc_alert"] = alerts[rule.qtc_column] >= rule.absolute_qtc_ms

    if rule.baseline_column in alerts.columns:
        alerts["delta_qtc_ms"] = alerts[rule.qtc_column] - alerts[rule.baseline_column]
        alerts["delta_qtc_alert"] = alerts["delta_qtc_ms"] >= rule.delta_qtc_ms
    else:
        alerts["delta_qtc_ms"] = pd.NA
        alerts["delta_qtc_alert"] = False

    alerts["alert"] = alerts["absolute_qtc_alert"] | alerts["delta_qtc_alert"]
    return alerts.loc[alerts["alert"]].reset_index(drop=True)
