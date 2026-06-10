"""Expert (inter-observer) variability framework.

Provides utilities for comparing manual annotations from multiple
reviewers and computing inter-observer agreement metrics to support
future manual-annotation validation studies.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class ExpertComparison:
    """Pairwise comparison between two reviewers.

    Attributes
    ----------
    reviewer_a, reviewer_b : str
        Reviewer identifiers.
    mean_diff_ms : float
        Mean signed difference (A − B) in ms.
    sd_diff_ms : float
        SD of differences.
    abs_mean_diff_ms : float
        Mean absolute difference.
    agreement_within_5ms : float
        Fraction of beats where |A − B| ≤ 5 ms.
    agreement_within_10ms : float
    agreement_within_20ms : float
    """

    reviewer_a: str
    reviewer_b: str
    mean_diff_ms: float
    sd_diff_ms: float
    abs_mean_diff_ms: float
    agreement_within_5ms: float
    agreement_within_10ms: float
    agreement_within_20ms: float


@dataclass
class ExpertVariabilityReport:
    """Full inter-observer variability report.

    Attributes
    ----------
    n_beats : int
    n_reviewers : int
    pairwise : list[ExpertComparison]
    overall_sd_ms : float
        Pooled SD across all reviewer pairs.
    """

    n_beats: int
    n_reviewers: int
    pairwise: list[ExpertComparison] = field(default_factory=list)
    overall_sd_ms: float = 0.0


def pairwise_comparison(
    values_a: np.ndarray | list[float],
    values_b: np.ndarray | list[float],
    reviewer_a: str = "A",
    reviewer_b: str = "B",
) -> ExpertComparison:
    """Compare two sets of measurements (same beats, different reviewers).

    Parameters
    ----------
    values_a, values_b : array-like
        Measurements from reviewer A and B (ms), aligned beat-by-beat.
    """
    a = np.asarray(values_a, dtype=float)
    b = np.asarray(values_b, dtype=float)
    diff = a - b
    abs_diff = np.abs(diff)

    return ExpertComparison(
        reviewer_a=reviewer_a,
        reviewer_b=reviewer_b,
        mean_diff_ms=float(np.mean(diff)),
        sd_diff_ms=float(np.std(diff, ddof=1)) if len(diff) > 1 else 0.0,
        abs_mean_diff_ms=float(np.mean(abs_diff)),
        agreement_within_5ms=float(np.mean(abs_diff <= 5.0)),
        agreement_within_10ms=float(np.mean(abs_diff <= 10.0)),
        agreement_within_20ms=float(np.mean(abs_diff <= 20.0)),
    )


def expert_variability_report(
    annotations: dict[str, np.ndarray | list[float]],
) -> ExpertVariabilityReport:
    """Generate a full inter-observer variability report.

    Parameters
    ----------
    annotations : dict[str, array-like]
        Keyed by reviewer ID, each value is an array of measurements (ms)
        for the same set of beats (same length).

    Returns
    -------
    ExpertVariabilityReport
    """
    reviewers = sorted(annotations.keys())
    n_reviewers = len(reviewers)

    if n_reviewers < 2:
        n = len(list(annotations.values())[0]) if annotations else 0
        return ExpertVariabilityReport(n_beats=n, n_reviewers=n_reviewers)

    n_beats = len(np.asarray(list(annotations.values())[0]))
    comparisons: list[ExpertComparison] = []
    all_diffs: list[np.ndarray] = []

    for i in range(n_reviewers):
        for j in range(i + 1, n_reviewers):
            comp = pairwise_comparison(
                np.asarray(annotations[reviewers[i]]),
                np.asarray(annotations[reviewers[j]]),
                reviewer_a=reviewers[i],
                reviewer_b=reviewers[j],
            )
            comparisons.append(comp)
            all_diffs.append(
                np.asarray(annotations[reviewers[i]], dtype=float)
                - np.asarray(annotations[reviewers[j]], dtype=float)
            )

    pooled = np.concatenate(all_diffs)
    overall_sd = float(np.std(pooled, ddof=1)) if len(pooled) > 1 else 0.0

    return ExpertVariabilityReport(
        n_beats=n_beats,
        n_reviewers=n_reviewers,
        pairwise=comparisons,
        overall_sd_ms=overall_sd,
    )
