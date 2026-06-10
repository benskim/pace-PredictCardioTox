"""Tests for the demo data generator used by the Validation Engine UI."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "app"))

from demo_data import (
    MeasurementRecord,
    generate_high_confidence_record,
    generate_low_confidence_record,
    generate_study_dataset,
)


class TestHighConfidence:
    def test_score_above_85(self):
        r = generate_high_confidence_record()
        assert r.confidence_score >= 85

    def test_decision_auto_accept(self):
        r = generate_high_confidence_record()
        assert r.decision == "Auto Accept"

    def test_sub_scores_in_range(self):
        r = generate_high_confidence_record()
        for attr in ["signal_quality", "beat_consistency", "t_end_confidence", "noise_impact"]:
            val = getattr(r, attr)
            assert 0 <= val <= 100

    def test_has_reasons(self):
        r = generate_high_confidence_record()
        assert len(r.reasons) >= 1

    def test_deterministic(self):
        r1 = generate_high_confidence_record(record_id="X-001")
        r2 = generate_high_confidence_record(record_id="X-001")
        assert r1.confidence_score == r2.confidence_score


class TestLowConfidence:
    def test_score_below_60(self):
        r = generate_low_confidence_record()
        assert r.confidence_score < 60

    def test_decision_unreliable(self):
        r = generate_low_confidence_record()
        assert r.decision == "Measurement Unreliable"

    def test_reasons_mention_issues(self):
        r = generate_low_confidence_record()
        combined = " ".join(r.reasons).lower()
        assert any(
            kw in combined
            for kw in ["noise", "variability", "uncertain", "dropout", "disagreement"]
        )


class TestStudyDataset:
    def test_correct_count(self):
        ds = generate_study_dataset(n_records=50)
        assert len(ds) == 50

    def test_mixed_decisions(self):
        ds = generate_study_dataset(n_records=200)
        decisions = {r.decision for r in ds}
        assert len(decisions) >= 2

    def test_all_records_valid(self):
        ds = generate_study_dataset(n_records=100)
        for r in ds:
            assert isinstance(r, MeasurementRecord)
            assert 0 <= r.confidence_score <= 100
            assert r.qtcf_ms > 0
            assert r.rr_ms > 0

    def test_penalty_breakdown_sums(self):
        ds = generate_study_dataset(n_records=50)
        for r in ds:
            expected = (
                r.base_score
                - r.noise_penalty
                - r.beat_variability_penalty
                - r.t_end_ambiguity_penalty
                - r.formula_disagreement_penalty
            )
            assert abs(r.confidence_score - max(5, expected)) < 0.2 or r.confidence_score >= 85
