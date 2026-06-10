"""Publication-quality report generation from validation results."""

from __future__ import annotations

import pandas as pd

from .pipeline import ValidationResult


def _results_to_df(results: list[ValidationResult]) -> pd.DataFrame:
    rows: list[dict] = []
    for r in results:
        row: dict = {
            "dataset": r.dataset,
            "noise_type": r.noise_type,
            "snr_db": r.snr_db,
            "n_beats": r.n_beats,
        }
        for k, v in r.qt.items():
            row[f"qt_{k}"] = v
        for formula, metrics in r.qtc.items():
            for k, v in metrics.items():
                row[f"qtc_{formula}_{k}"] = v
        for k, v in r.delineation.items():
            row[f"delin_{k}"] = v
        rows.append(row)
    return pd.DataFrame(rows)


def results_to_markdown(results: list[ValidationResult]) -> str:
    """Render validation results as a Markdown table."""
    df = _results_to_df(results)
    return df.to_markdown(index=False, floatfmt=".2f")


def results_to_latex(results: list[ValidationResult]) -> str:
    """Render validation results as a LaTeX table."""
    df = _results_to_df(results)
    return df.to_latex(index=False, float_format="%.2f")
