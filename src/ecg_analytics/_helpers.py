"""Shared validation helpers used across ECG analytics modules."""

from __future__ import annotations

from typing import Union

import numpy as np
import pandas as pd

Numeric = Union[float, "pd.Series", "np.ndarray"]
"""Scalar, Series, or array accepted by QTc correction functions."""


def to_positive_array(values: Numeric, name: str) -> np.ndarray:
    """Convert *values* to a float array and verify every element is positive.

    Raises ``ValueError`` when any element is <= 0, using *name* in the
    message so callers get a domain-specific error.
    """
    arr = np.asarray(values, dtype=float)
    if np.any(arr <= 0):
        raise ValueError(f"{name} must be positive.")
    return arr


def require_columns(df: pd.DataFrame, *columns: str) -> None:
    """Raise ``ValueError`` if *df* is missing any of the listed *columns*."""
    missing = [c for c in columns if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required column(s): {', '.join(missing)}")
