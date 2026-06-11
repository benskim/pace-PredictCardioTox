"""Common data model shared by all dataset adapters."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class Annotation:
    """Single fiducial-point annotation on an ECG signal.

    Attributes
    ----------
    sample : int
        Sample index in the signal array.
    symbol : str
        Annotation symbol (e.g. ``"p"``, ``"N"``, ``"t"``).
    label : str
        Human-readable label (e.g. ``"T-peak"``, ``"T-end"``).
    lead : int
        Lead index the annotation refers to (0-based).
    """

    sample: int
    symbol: str
    label: str = ""
    lead: int = 0


@dataclass
class ECGRecord:
    """Unified ECG record returned by every dataset adapter.

    Attributes
    ----------
    record_id : str
        Unique identifier within the dataset (e.g. ``"sel100"``).
    signal : np.ndarray
        Raw ECG signal of shape ``(n_samples, n_leads)``.
    fs : float
        Sampling frequency in Hz.
    lead_names : list[str]
        Channel / lead names.
    annotations : list[Annotation]
        Fiducial-point annotations shipped with the record.
    metadata : dict
        Arbitrary extra metadata (units, comments, …).
    """

    record_id: str
    signal: np.ndarray
    fs: float
    lead_names: list[str] = field(default_factory=list)
    annotations: list[Annotation] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    @property
    def duration_s(self) -> float:
        """Total duration of the record in seconds."""
        return self.signal.shape[0] / self.fs

    @property
    def n_leads(self) -> int:
        return self.signal.shape[1] if self.signal.ndim == 2 else 1

    def lead(self, idx: int = 0) -> np.ndarray:
        """Return the 1-D signal for a single lead."""
        if self.signal.ndim == 1:
            return self.signal
        return self.signal[:, idx]

