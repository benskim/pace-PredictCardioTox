"""Orchestrator that runs a full validation suite across datasets."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from ..datasets.base import ECGRecord
from ..preprocessing.noise import NOISE_FUNCTIONS, STANDARD_SNR_LEVELS
from ..qt.measurement import measure_qt_intervals
from ..qtc.formulas import compute_all_qtc
from .metrics import qt_metrics, qtc_metrics


@dataclass
class ValidationResult:
    """Container for one validation run's metrics."""

    dataset: str = ""
    noise_type: str = "clean"
    snr_db: float | None = None
    n_beats: int = 0
    qt: dict[str, float] = field(default_factory=dict)
    qtc: dict[str, dict[str, float]] = field(default_factory=dict)
    delineation: dict[str, float] = field(default_factory=dict)


class ValidationPipeline:
    """Run QT / QTc validation across records and noise conditions.

    Example usage::

        pipeline = ValidationPipeline()
        results = pipeline.run(records, reference_qt_ms, reference_qtc_ms)
    """

    def evaluate_record(
        self,
        record: ECGRecord,
        reference_qt_ms: np.ndarray | None = None,
        reference_qtc_ms: np.ndarray | None = None,
        lead: int = 0,
    ) -> ValidationResult:
        """Evaluate a single record on the primary (clean) signal."""
        signal = record.lead(lead)
        measurements = measure_qt_intervals(signal, record.fs)

        pred_qt = np.array([m.qt_ms for m in measurements if m.qt_ms is not None])
        pred_rr = np.array([m.rr_ms for m in measurements if m.rr_ms is not None and m.qt_ms is not None])

        result = ValidationResult(
            dataset=record.metadata.get("database", ""),
            n_beats=len(pred_qt),
        )

        if reference_qt_ms is not None and len(pred_qt) > 0:
            n = min(len(pred_qt), len(reference_qt_ms))
            result.qt = qt_metrics(pred_qt[:n], reference_qt_ms[:n])

        if reference_qtc_ms is not None and len(pred_qt) > 0 and len(pred_rr) > 0:
            n = min(len(pred_qt), len(pred_rr), len(reference_qtc_ms))
            all_qtc = compute_all_qtc(pred_qt[:n], pred_rr[:n])
            for formula, values in all_qtc.items():
                result.qtc[formula] = qtc_metrics(values, reference_qtc_ms[:n])

        return result

    def evaluate_noise_robustness(
        self,
        record: ECGRecord,
        reference_qt_ms: np.ndarray | None = None,
        lead: int = 0,
        snr_levels: list[int] | None = None,
        noise_types: list[str] | None = None,
    ) -> list[ValidationResult]:
        """Evaluate across noise types and SNR levels."""
        snr_levels = snr_levels or STANDARD_SNR_LEVELS
        noise_types = noise_types or list(NOISE_FUNCTIONS)
        results: list[ValidationResult] = []

        for noise_type in noise_types:
            noise_fn = NOISE_FUNCTIONS[noise_type]
            for snr in snr_levels:
                signal = record.lead(lead)
                noisy = noise_fn(signal, record.fs, snr_db=float(snr))
                measurements = measure_qt_intervals(noisy, record.fs)
                pred_qt = np.array([m.qt_ms for m in measurements if m.qt_ms is not None])

                vr = ValidationResult(
                    dataset=record.metadata.get("database", ""),
                    noise_type=noise_type,
                    snr_db=float(snr),
                    n_beats=len(pred_qt),
                )

                if reference_qt_ms is not None and len(pred_qt) > 0:
                    n = min(len(pred_qt), len(reference_qt_ms))
                    vr.qt = qt_metrics(pred_qt[:n], reference_qt_ms[:n])

                results.append(vr)

        return results
