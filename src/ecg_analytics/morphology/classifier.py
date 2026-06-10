"""Rule-based T-wave morphology classifier.

Classification is based on signal-processing features (not ML), keeping
the logic fully explainable.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.signal import find_peaks

MORPHOLOGY_TYPES = [
    "normal",
    "flat",
    "low_amplitude",
    "biphasic",
    "notched",
    "merged_tu",
]


@dataclass
class MorphologyResult:
    """Classification result for a single T-wave.

    Attributes
    ----------
    morphology : str
        One of :data:`MORPHOLOGY_TYPES`.
    features : dict[str, float]
        Feature values used for classification (for explainability).
    confidence : float
        Rule confidence (0–1).  Higher values indicate clearer morphology.
    """

    morphology: str
    features: dict[str, float]
    confidence: float


def classify_t_wave(
    signal: np.ndarray,
    t_start: int,
    t_end: int,
    fs: float,
    baseline: float = 0.0,
    flat_amplitude_mv: float = 0.05,
    low_amplitude_mv: float = 0.10,
    notch_prominence_fraction: float = 0.15,
) -> MorphologyResult:
    """Classify a T-wave segment into one of the supported morphology types.

    Parameters
    ----------
    signal : np.ndarray
        Full 1-D ECG signal.
    t_start, t_end : int
        Sample indices bounding the T-wave region.
    fs : float
        Sampling frequency (Hz).
    baseline : float
        Isoelectric baseline voltage.
    flat_amplitude_mv : float
        Peak-to-baseline amplitude below this → "flat".
    low_amplitude_mv : float
        Peak-to-baseline amplitude below this (but above flat) → "low_amplitude".
    notch_prominence_fraction : float
        Fractional prominence required to classify a dip as a notch.

    Returns
    -------
    MorphologyResult
    """
    t_start = max(0, t_start)
    t_end = min(len(signal), t_end)
    segment = signal[t_start:t_end].astype(float)

    if len(segment) < 5:
        return MorphologyResult(
            morphology="flat",
            features={"amplitude": 0.0, "n_peaks": 0, "zero_crossings": 0},
            confidence=0.5,
        )

    # Basic features
    peak_val = float(np.max(segment))
    trough_val = float(np.min(segment))
    amplitude = max(abs(peak_val - baseline), abs(trough_val - baseline))
    peak_to_peak = peak_val - trough_val

    # Zero crossings (relative to baseline)
    centered = segment - baseline
    sign_changes = np.where(np.diff(np.sign(centered)))[0]
    n_zero_crossings = len(sign_changes)

    # Peaks in the segment
    peaks, peak_props = find_peaks(segment, distance=max(3, len(segment) // 10))
    troughs, _ = find_peaks(-segment, distance=max(3, len(segment) // 10))
    n_peaks = len(peaks)
    n_troughs = len(troughs)

    features: dict[str, float] = {
        "amplitude": amplitude,
        "peak_to_peak": peak_to_peak,
        "n_peaks": float(n_peaks),
        "n_troughs": float(n_troughs),
        "zero_crossings": float(n_zero_crossings),
    }

    # --- Classification rules ---

    # Flat
    if amplitude < flat_amplitude_mv:
        return MorphologyResult(morphology="flat", features=features, confidence=0.9)

    # Low amplitude
    if amplitude < low_amplitude_mv:
        return MorphologyResult(morphology="low_amplitude", features=features, confidence=0.85)

    # Biphasic: has at least one zero-crossing and significant amplitude on both sides
    if n_zero_crossings >= 1 and n_peaks >= 1 and n_troughs >= 1:
        positive_amp = abs(peak_val - baseline)
        negative_amp = abs(trough_val - baseline)
        ratio = min(positive_amp, negative_amp) / max(positive_amp, negative_amp)
        if ratio > 0.2:
            features["biphasic_ratio"] = ratio
            return MorphologyResult(morphology="biphasic", features=features, confidence=0.8)

    # Notched: multiple peaks with a dip between them
    if n_peaks >= 2:
        sorted_peak_vals = sorted(segment[peaks], reverse=True)
        if len(sorted_peak_vals) >= 2:
            dip_region = segment[peaks[0]:peaks[-1] + 1] if peaks[-1] > peaks[0] else segment
            dip_depth = float(np.max(segment[peaks]) - np.min(dip_region))
            notch_thresh = notch_prominence_fraction * amplitude
            if dip_depth > notch_thresh:
                features["notch_depth"] = dip_depth
                return MorphologyResult(
                    morphology="notched", features=features, confidence=0.75
                )

    # Merged T-U: look for a secondary hump after the main peak
    if n_peaks >= 2 and len(segment) > 10:
        main_peak_idx = peaks[np.argmax(segment[peaks])]
        later_peaks = [p for p in peaks if p > main_peak_idx + len(segment) // 5]
        if len(later_peaks) > 0:
            secondary_amp = float(np.max(segment[later_peaks]) - baseline)
            if secondary_amp > 0.1 * amplitude:
                features["secondary_peak_amp"] = secondary_amp
                return MorphologyResult(
                    morphology="merged_tu", features=features, confidence=0.7
                )

    # Normal
    return MorphologyResult(morphology="normal", features=features, confidence=0.9)
