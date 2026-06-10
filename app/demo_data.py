"""Demo data generator for the QTc Measurement Validation Engine.

Creates realistic ECG measurement scenarios with pre-computed confidence
metrics for demonstration purposes. No ML or real ECG signals required.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field

import numpy as np


@dataclass
class MeasurementRecord:
    """A single ECG measurement with confidence metadata."""

    record_id: str
    subject_id: str
    timepoint: str
    lead: str

    # QTc values (ms)
    qt_ms: float
    rr_ms: float
    hr_bpm: float
    qtcf_ms: float  # Fridericia
    qtcb_ms: float  # Bazett

    # Confidence sub-scores (0-100)
    signal_quality: float
    beat_consistency: float
    t_end_confidence: float
    noise_impact: float
    qt_stability: float

    # Composite
    confidence_score: float
    decision: str  # "Auto Accept" | "Manual Review Recommended" | "Measurement Unreliable"

    # Penalty breakdown
    base_score: float = 100.0
    noise_penalty: float = 0.0
    beat_variability_penalty: float = 0.0
    t_end_ambiguity_penalty: float = 0.0
    formula_disagreement_penalty: float = 0.0

    # Explainability
    reasons: list[str] = field(default_factory=list)


def _decision_from_score(score: float) -> str:
    if score >= 85:
        return "Auto Accept"
    if score >= 60:
        return "Manual Review Recommended"
    return "Measurement Unreliable"


def _reasons_high(record: MeasurementRecord) -> list[str]:
    reasons = []
    if record.signal_quality >= 85:
        reasons.append("Low baseline noise detected")
    if record.beat_consistency >= 85:
        reasons.append("Consistent QT measurements across beats")
    if record.t_end_confidence >= 85:
        reasons.append("Stable T-wave termination point")
    if record.noise_impact >= 85:
        reasons.append("Minimal signal dropout")
    if record.qt_stability >= 85:
        reasons.append("QTc formulas show strong agreement")
    if not reasons:
        reasons.append("Moderate signal quality with acceptable variability")
    return reasons


def _reasons_low(record: MeasurementRecord) -> list[str]:
    reasons = []
    if record.signal_quality < 60:
        reasons.append("High baseline noise detected")
    if record.beat_consistency < 60:
        reasons.append("Significant beat-to-beat variability")
    if record.t_end_confidence < 60:
        reasons.append("Uncertain T-wave ending point")
    if record.noise_impact < 60:
        reasons.append("Signal interruption or dropout detected")
    if record.qt_stability < 60:
        reasons.append("Large disagreement between QTc formulas")
    if not reasons:
        reasons.append("Multiple moderate quality concerns")
    return reasons


def _seed_from_id(record_id: str) -> int:
    return int(hashlib.md5(record_id.encode()).hexdigest()[:8], 16)


def generate_high_confidence_record(
    record_id: str = "ECG-A-001",
    subject_id: str = "SUBJ-101",
    timepoint: str = "Day 1 Pre-dose",
    qtcf_ms: float = 451.0,
) -> MeasurementRecord:
    """Generate a high-confidence measurement record."""
    rng = np.random.default_rng(_seed_from_id(record_id))

    signal_quality = rng.uniform(88, 98)
    beat_consistency = rng.uniform(90, 97)
    t_end_confidence = rng.uniform(87, 96)
    noise_impact = rng.uniform(85, 95)
    qt_stability = rng.uniform(86, 96)

    noise_penalty = round(rng.uniform(1, 6), 1)
    beat_penalty = round(rng.uniform(0.5, 3), 1)
    t_end_penalty = round(rng.uniform(0.5, 2.5), 1)
    formula_penalty = round(rng.uniform(0, 2), 1)

    confidence = 100 - noise_penalty - beat_penalty - t_end_penalty - formula_penalty

    rr_ms = round(rng.uniform(750, 950), 0)
    hr_bpm = round(60000 / rr_ms, 1)
    qt_ms = round(qtcf_ms * np.cbrt(rr_ms / 1000), 1)
    qtcb_ms = round(qt_ms / np.sqrt(rr_ms / 1000), 1)

    record = MeasurementRecord(
        record_id=record_id,
        subject_id=subject_id,
        timepoint=timepoint,
        lead="II",
        qt_ms=qt_ms,
        rr_ms=rr_ms,
        hr_bpm=hr_bpm,
        qtcf_ms=qtcf_ms,
        qtcb_ms=qtcb_ms,
        signal_quality=round(signal_quality, 1),
        beat_consistency=round(beat_consistency, 1),
        t_end_confidence=round(t_end_confidence, 1),
        noise_impact=round(noise_impact, 1),
        qt_stability=round(qt_stability, 1),
        confidence_score=round(confidence, 1),
        decision=_decision_from_score(confidence),
        base_score=100.0,
        noise_penalty=noise_penalty,
        beat_variability_penalty=beat_penalty,
        t_end_ambiguity_penalty=t_end_penalty,
        formula_disagreement_penalty=formula_penalty,
    )
    record.reasons = _reasons_high(record)
    return record


def generate_low_confidence_record(
    record_id: str = "ECG-B-001",
    subject_id: str = "SUBJ-102",
    timepoint: str = "Day 1 Pre-dose",
    qtcf_ms: float = 452.0,
) -> MeasurementRecord:
    """Generate a low-confidence measurement record."""
    rng = np.random.default_rng(_seed_from_id(record_id))

    signal_quality = rng.uniform(25, 50)
    beat_consistency = rng.uniform(20, 45)
    t_end_confidence = rng.uniform(22, 48)
    noise_impact = rng.uniform(28, 52)
    qt_stability = rng.uniform(25, 45)

    noise_penalty = round(rng.uniform(20, 35), 1)
    beat_penalty = round(rng.uniform(12, 22), 1)
    t_end_penalty = round(rng.uniform(8, 18), 1)
    formula_penalty = round(rng.uniform(5, 12), 1)

    confidence = max(5, 100 - noise_penalty - beat_penalty - t_end_penalty - formula_penalty)

    rr_ms = round(rng.uniform(750, 950), 0)
    hr_bpm = round(60000 / rr_ms, 1)
    qt_ms = round(qtcf_ms * np.cbrt(rr_ms / 1000), 1)
    qtcb_ms = round(qt_ms / np.sqrt(rr_ms / 1000), 1)

    record = MeasurementRecord(
        record_id=record_id,
        subject_id=subject_id,
        timepoint=timepoint,
        lead="II",
        qt_ms=qt_ms,
        rr_ms=rr_ms,
        hr_bpm=hr_bpm,
        qtcf_ms=qtcf_ms,
        qtcb_ms=qtcb_ms,
        signal_quality=round(signal_quality, 1),
        beat_consistency=round(beat_consistency, 1),
        t_end_confidence=round(t_end_confidence, 1),
        noise_impact=round(noise_impact, 1),
        qt_stability=round(qt_stability, 1),
        confidence_score=round(confidence, 1),
        decision=_decision_from_score(confidence),
        base_score=100.0,
        noise_penalty=noise_penalty,
        beat_variability_penalty=beat_penalty,
        t_end_ambiguity_penalty=t_end_penalty,
        formula_disagreement_penalty=formula_penalty,
    )
    record.reasons = _reasons_low(record)
    return record


def generate_study_dataset(n_records: int = 200, seed: int = 42) -> list[MeasurementRecord]:
    """Generate a study-level dataset with mixed confidence levels.

    Distribution: ~60% high, ~25% medium, ~15% low confidence.
    """
    rng = np.random.default_rng(seed)
    records = []

    subjects = [f"SUBJ-{i:03d}" for i in range(1, 41)]
    timepoints = [
        "Screening",
        "Day -1 Pre-dose",
        "Day 1 Pre-dose",
        "Day 1 1h Post",
        "Day 1 2h Post",
        "Day 1 4h Post",
        "Day 1 8h Post",
        "Day 1 12h Post",
        "Day 7 Pre-dose",
        "Day 7 2h Post",
    ]

    for i in range(n_records):
        record_id = f"ECG-{i:04d}"
        subject = subjects[i % len(subjects)]
        tp = timepoints[i % len(timepoints)]

        roll = rng.random()
        base_qtcf = rng.uniform(390, 470)

        if roll < 0.60:
            record = generate_high_confidence_record(
                record_id=record_id,
                subject_id=subject,
                timepoint=tp,
                qtcf_ms=round(base_qtcf, 1),
            )
        elif roll < 0.85:
            record = _generate_medium_confidence_record(
                record_id=record_id,
                subject_id=subject,
                timepoint=tp,
                qtcf_ms=round(base_qtcf, 1),
                rng=rng,
            )
        else:
            record = generate_low_confidence_record(
                record_id=record_id,
                subject_id=subject,
                timepoint=tp,
                qtcf_ms=round(base_qtcf, 1),
            )
        records.append(record)

    return records


def _generate_medium_confidence_record(
    record_id: str,
    subject_id: str,
    timepoint: str,
    qtcf_ms: float,
    rng: np.random.Generator,
) -> MeasurementRecord:
    """Generate a medium-confidence measurement record (60-84 range)."""
    signal_quality = rng.uniform(60, 82)
    beat_consistency = rng.uniform(62, 80)
    t_end_confidence = rng.uniform(58, 78)
    noise_impact = rng.uniform(60, 80)
    qt_stability = rng.uniform(62, 82)

    noise_penalty = round(rng.uniform(6, 15), 1)
    beat_penalty = round(rng.uniform(3, 10), 1)
    t_end_penalty = round(rng.uniform(2, 8), 1)
    formula_penalty = round(rng.uniform(1, 6), 1)

    confidence = max(55, 100 - noise_penalty - beat_penalty - t_end_penalty - formula_penalty)

    rr_ms = round(rng.uniform(750, 950), 0)
    hr_bpm = round(60000 / rr_ms, 1)
    qt_ms = round(qtcf_ms * np.cbrt(rr_ms / 1000), 1)
    qtcb_ms = round(qt_ms / np.sqrt(rr_ms / 1000), 1)

    record = MeasurementRecord(
        record_id=record_id,
        subject_id=subject_id,
        timepoint=timepoint,
        lead="II",
        qt_ms=qt_ms,
        rr_ms=rr_ms,
        hr_bpm=hr_bpm,
        qtcf_ms=qtcf_ms,
        qtcb_ms=qtcb_ms,
        signal_quality=round(signal_quality, 1),
        beat_consistency=round(beat_consistency, 1),
        t_end_confidence=round(t_end_confidence, 1),
        noise_impact=round(noise_impact, 1),
        qt_stability=round(qt_stability, 1),
        confidence_score=round(confidence, 1),
        decision=_decision_from_score(confidence),
        base_score=100.0,
        noise_penalty=noise_penalty,
        beat_variability_penalty=beat_penalty,
        t_end_ambiguity_penalty=t_end_penalty,
        formula_disagreement_penalty=formula_penalty,
    )

    reasons = []
    if record.signal_quality < 70:
        reasons.append("Moderate baseline noise present")
    if record.beat_consistency < 70:
        reasons.append("Some beat-to-beat variability observed")
    if record.t_end_confidence < 70:
        reasons.append("T-wave ending partially ambiguous")
    if record.noise_impact < 70:
        reasons.append("Minor signal quality concerns")
    if not reasons:
        reasons.append("Multiple minor quality factors detected")
    record.reasons = reasons
    return record
