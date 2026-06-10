"""Multi-method T-end agreement and stability analysis.

Runs all four T-end methods on the same beat and computes inter-method
agreement statistics to produce a *T-End Stability Score*.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from .derivative import derivative_t_end
from .tangent import tangent_t_end
from .threshold import threshold_t_end
from .wavelet import wavelet_t_end

METHOD_REGISTRY: dict[str, type] = {
    "tangent": type(None),  # placeholder; callables stored below
    "threshold": type(None),
    "derivative": type(None),
    "wavelet": type(None),
}

_METHOD_FUNCTIONS = {
    "tangent": tangent_t_end,
    "threshold": threshold_t_end,
    "derivative": derivative_t_end,
    "wavelet": wavelet_t_end,
}


@dataclass
class TEndAgreement:
    """Results of running multiple T-end methods on a single beat.

    Attributes
    ----------
    method_results : dict[str, int | None]
        T-end sample index per method (``None`` if method failed).
    valid_results_ms : dict[str, float]
        T-end in ms for methods that produced a result.
    stability_metrics : dict[str, float]
        Mean, SD, IQR, max-min difference (ms).
    stability_score : float
        0–100 score (higher = more agreement).
    """

    method_results: dict[str, int | None] = field(default_factory=dict)
    valid_results_ms: dict[str, float] = field(default_factory=dict)
    stability_metrics: dict[str, float] = field(default_factory=dict)
    stability_score: float = 0.0


def tend_stability_metrics(values_ms: list[float]) -> dict[str, float]:
    """Compute T-end stability statistics from a list of T-end positions (ms).

    Returns
    -------
    dict with ``mean_ms``, ``sd_ms``, ``iqr_ms``, ``range_ms``.
    """
    arr = np.array(values_ms)
    if len(arr) < 2:
        return {
            "mean_ms": float(arr[0]) if len(arr) == 1 else 0.0,
            "sd_ms": 0.0,
            "iqr_ms": 0.0,
            "range_ms": 0.0,
        }
    return {
        "mean_ms": float(np.mean(arr)),
        "sd_ms": float(np.std(arr, ddof=1)),
        "iqr_ms": float(np.percentile(arr, 75) - np.percentile(arr, 25)),
        "range_ms": float(np.max(arr) - np.min(arr)),
    }


def tend_stability_score(metrics: dict[str, float], n_valid: int, n_total: int = 4) -> float:
    """Convert stability metrics into a 0–100 score.

    Scoring logic (fully explainable):
      - Base: fraction of methods that produced a result × 50
      - SD penalty: lose up to 30 points as SD increases beyond 5 ms
      - Range penalty: lose up to 20 points as range exceeds 10 ms
    """
    if n_valid == 0:
        return 0.0

    coverage = n_valid / n_total
    base = coverage * 50.0

    sd = metrics.get("sd_ms", 0.0)
    # Penalty: 0 at sd=0, 30 at sd>=15
    sd_penalty = min(30.0, sd * 2.0)

    rng = metrics.get("range_ms", 0.0)
    # Penalty: 0 at range=0, 20 at range>=20
    range_penalty = min(20.0, rng * 1.0)

    score = base + (50.0 - sd_penalty - range_penalty) * coverage
    return float(np.clip(score, 0.0, 100.0))


def compute_agreement(
    signal: np.ndarray,
    t_peak: int,
    fs: float,
    baseline: float = 0.0,
    search_window_ms: float = 200.0,
) -> TEndAgreement:
    """Run all T-end methods and compute agreement statistics.

    Parameters
    ----------
    signal : np.ndarray
        1-D ECG signal.
    t_peak : int
        Sample index of the T-wave peak.
    fs : float
        Sampling frequency in Hz.
    baseline : float
        Isoelectric baseline voltage.
    search_window_ms : float
        Search window (ms) passed to each method.

    Returns
    -------
    TEndAgreement
    """
    results: dict[str, int | None] = {}
    valid_ms: dict[str, float] = {}

    common_kwargs = {
        "signal": signal,
        "t_peak": t_peak,
        "fs": fs,
        "search_window_ms": search_window_ms,
    }

    results["tangent"] = tangent_t_end(baseline=baseline, **common_kwargs)
    results["threshold"] = threshold_t_end(baseline=baseline, **common_kwargs)
    results["derivative"] = derivative_t_end(**common_kwargs)
    results["wavelet"] = wavelet_t_end(**common_kwargs)

    for method, sample_idx in results.items():
        if sample_idx is not None:
            valid_ms[method] = sample_idx / fs * 1000

    values = list(valid_ms.values())
    metrics = tend_stability_metrics(values)
    score = tend_stability_score(metrics, n_valid=len(values), n_total=4)

    return TEndAgreement(
        method_results=results,
        valid_results_ms=valid_ms,
        stability_metrics=metrics,
        stability_score=score,
    )
