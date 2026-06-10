"""Tests for the expert variability framework."""

from __future__ import annotations

import pytest

from ecg_analytics.validation.expert_variability import (
    ExpertComparison,
    ExpertVariabilityReport,
    expert_variability_report,
    pairwise_comparison,
)


class TestPairwiseComparison:
    def test_identical_annotations(self) -> None:
        vals = [400.0, 410.0, 405.0]
        comp = pairwise_comparison(vals, vals, "A", "B")
        assert isinstance(comp, ExpertComparison)
        assert comp.mean_diff_ms == pytest.approx(0.0)
        assert comp.sd_diff_ms == pytest.approx(0.0)
        assert comp.agreement_within_5ms == pytest.approx(1.0)
        assert comp.agreement_within_10ms == pytest.approx(1.0)

    def test_small_differences(self) -> None:
        a = [400.0, 410.0, 420.0]
        b = [402.0, 408.0, 418.0]
        comp = pairwise_comparison(a, b, "A", "B")
        assert comp.abs_mean_diff_ms == pytest.approx(2.0)
        assert comp.agreement_within_5ms == pytest.approx(1.0)

    def test_large_differences(self) -> None:
        a = [400.0, 410.0]
        b = [430.0, 440.0]
        comp = pairwise_comparison(a, b)
        assert comp.agreement_within_5ms == pytest.approx(0.0)
        assert comp.agreement_within_20ms == pytest.approx(0.0)


class TestExpertVariabilityReport:
    def test_two_reviewers(self) -> None:
        annotations = {
            "reviewer_A": [400.0, 410.0, 405.0],
            "reviewer_B": [402.0, 408.0, 407.0],
        }
        report = expert_variability_report(annotations)
        assert isinstance(report, ExpertVariabilityReport)
        assert report.n_reviewers == 2
        assert report.n_beats == 3
        assert len(report.pairwise) == 1
        assert report.overall_sd_ms > 0

    def test_three_reviewers(self) -> None:
        annotations = {
            "A": [400.0, 410.0],
            "B": [402.0, 408.0],
            "C": [401.0, 411.0],
        }
        report = expert_variability_report(annotations)
        assert report.n_reviewers == 3
        # C(3,2) = 3 pairwise comparisons
        assert len(report.pairwise) == 3

    def test_single_reviewer(self) -> None:
        annotations = {"A": [400.0, 410.0]}
        report = expert_variability_report(annotations)
        assert report.n_reviewers == 1
        assert len(report.pairwise) == 0
