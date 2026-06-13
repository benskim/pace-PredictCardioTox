# Confidence Model Specification — QTc Confidence Engine

## Overview

The Confidence Model produces an explainable, composite **Measurement Confidence Score** (0–100) by aggregating five sub-scores, each quantifying a distinct source of QTc measurement uncertainty.

**Governing equation:**
```
Confidence = clamp(Σ (sub_score_i × weight_i) / Σ weight_i, 0, 100)
```

**Entry point:** `ecg_analytics.confidence.measurement_confidence()`

---

## 1. Sub-Score: Signal Quality

**Module:** `ecg_analytics.confidence.signal_quality`
**Function:** `signal_quality_subscore(signal, fs) → float`
**Default weight:** 0.20

### What it measures
Raw ECG signal integrity prior to any processing. High noise renders all downstream analysis unreliable regardless of algorithm quality.

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `signal` | `np.ndarray` | 1-D ECG lead (mV) |
| `fs` | `float` | Sampling frequency (Hz) |

### Internal SQI Features

| Feature | High quality | Low quality |
|---------|-------------|-------------|
| `snr_db` | > 20 dB | < 10 dB |
| `kurtosis` | Moderate (spiky ECG) | Very high (artifacts) or ≈ 0 (white noise) |
| `baseline_drift` | < 0.1 mV | > 0.5 mV |
| `flatline_fraction` | < 0.01 | > 0.10 |

### Score interpretation
- **90–100:** Clean signal; negligible noise contribution
- **60–89:** Moderate noise; manageable with filtering
- **0–59:** High noise; downstream measurements unreliable

---

## 2. Sub-Score: T-End Stability

**Module:** `ecg_analytics.confidence.tend_stability`
**Function:** `tend_stability_subscore(method_results) → float`
**Default weight:** 0.25

### What it measures
Agreement among four independent T-end detection algorithms. Divergence indicates genuine morphological ambiguity (flat T, bifid T, low-amplitude T) that no single algorithm can resolve reliably.

### Detection methods

| Method | Module | Approach |
|--------|--------|----------|
| Tangent | `ecg_analytics.tend.tangent` | Tangent line intersection |
| Derivative | `ecg_analytics.tend.derivative` | First derivative zero-crossing |
| Wavelet | `ecg_analytics.tend.wavelet` | CWT modulus maxima |
| Threshold | `ecg_analytics.tend.threshold` | Amplitude threshold descent |

### Agreement metric
`max_spread = max(method_results) − min(method_results)` in samples.

| Spread | Sub-score | Clinical meaning |
|--------|-----------|-----------------|
| < 10 samples | 90–100 | Methods agree; T-end is unambiguous |
| 10–30 samples | 60–89 | Moderate disagreement; review advised |
| > 30 samples | 0–59 | High disagreement; T-wave boundary uncertain |

### Input schema
`method_results: dict[str, int]` — sample index per method name:
```python
{
    "tangent":    405,
    "derivative": 412,
    "wavelet":    398,
    "threshold":  410,
}
```

---

## 3. Sub-Score: Morphology Risk

**Module:** `ecg_analytics.confidence.morphology_risk`
**Function:** `morphology_risk_subscore(t_wave_signal) → float`
**Default weight:** 0.15

### What it measures
T-wave shape risk. Certain morphologies (flat, notched, biphasic, inverted) introduce systematic T-end localisation error that cannot be resolved by algorithm choice alone.

### T-Wave Morphology Classes

| Class | Risk level | Score adjustment |
|-------|-----------|-----------------|
| `"normal"` | Low | 95–100 |
| `"tall_peaked"` | Low | 90–100 |
| `"flat"` | High | 30–60 |
| `"notched"` | High | 40–65 |
| `"biphasic"` | Very high | 15–40 |
| `"inverted"` | High | 35–60 |
| `"low_amplitude"` | High | 25–55 |

**Classifier module:** `ecg_analytics.morphology.classify_t_wave()`

---

## 4. Sub-Score: Formula Agreement

**Module:** `ecg_analytics.confidence.formula_agreement`
**Function:** `formula_agreement_score(qt_ms, rr_ms) → FormulaAgreementResult`
**Default weight:** 0.15

### What it measures
Spread among the four QTc correction formulas. High spread indicates the heart rate is not in steady state (HR hysteresis), making all correction formulas unreliable simultaneously.

### Formulas compared

| Name | Formula |
|------|---------|
| Fridericia | QTcF = QT / RR^(1/3) |
| Bazett | QTcB = QT / √RR |
| Framingham | QTcFram = QT + 0.154 × (1 − RR) |
| Hodges | QTcH = QT + 1.75 × (HR − 60) |

Where RR is in seconds and QT in ms.

### Spread → Score mapping

| Max spread (ms) | Score | Interpretation |
|-----------------|-------|----------------|
| < 5 ms | 90–100 | Formulas agree; HR steady |
| 5–15 ms | 60–89 | Minor disagreement; possible HR fluctuation |
| 15–30 ms | 30–59 | Significant disagreement; correction uncertain |
| > 30 ms | 0–29 | Formulas contradict; HR not in steady state |

### Output

```python
FormulaAgreementResult(
    score=float,            # [0, 100]
    qtc_values=dict,        # {"fridericia": ms, "bazett": ms, ...}
    max_spread_ms=float,    # max − min across formulas
)
```

---

## 5. Sub-Score: Beat Stability

**Module:** `ecg_analytics.confidence.beat_stability`
**Function:** `beat_stability_score(qt_intervals_ms) → BeatStabilityResult`
**Default weight:** 0.25

### What it measures
Beat-to-beat consistency of QT intervals within a single ECG epoch. High variability indicates ectopic beats, PVCs, atrial fibrillation, or measurement noise contaminating the averaged estimate.

### Inputs

| Parameter | Type | Description |
|-----------|------|-------------|
| `qt_intervals_ms` | `np.ndarray` | Per-beat QT measurements (ms) |

### Stability metrics

| Metric | Good | Poor |
|--------|------|------|
| CV (coefficient of variation) | < 0.02 | > 0.05 |
| IQR | < 10 ms | > 25 ms |
| SD | < 5 ms | > 15 ms |

### Score mapping

| CV | Score | Interpretation |
|----|-------|----------------|
| < 0.01 | 95–100 | Extremely stable; textbook ECG |
| 0.01–0.02 | 80–94 | Good stability |
| 0.02–0.04 | 60–79 | Moderate variability |
| 0.04–0.06 | 35–59 | High variability; suspect ectopics |
| > 0.06 | 0–34 | Unreliable; AF or dominant noise |

### Output

```python
BeatStabilityResult(
    score=float,        # [0, 100]
    mean_qt=float,      # ms
    median_qt=float,    # ms
    sd_qt=float,        # ms
    iqr_qt=float,       # ms
    cv_qt=float,        # dimensionless
    n_beats=int,
)
```

---

## 6. Composite Score Assembly

```python
from ecg_analytics.confidence import measurement_confidence

result = measurement_confidence(
    signal_quality=sq_score,        # float [0, 100]
    tend_stability=ts_score,        # float [0, 100]
    morphology=morph_score,         # float [0, 100]
    formula_agreement=fa_score,     # float [0, 100]
    beat_stability=bs_score,        # float [0, 100]
    weights=None,                   # uses DEFAULT_WEIGHTS
)

# result.score   → float [0, 100]
# result.tier    → "high" | "review" | "manual_review"
# result.sub_scores → {"signal_quality": ..., "tend_stability": ..., ...}
# result.weights → {"signal_quality": 0.20, ...}
```

---

## 7. Explainability Contract

Every confidence result must be accompanied by human-readable reasons. The reason
generation follows these rules:

**High confidence reasons (score ≥ 85):**
- Each sub-score ≥ 85 generates a positive statement (e.g. "Low baseline noise detected")
- Fallback: "Moderate signal quality with acceptable variability"

**Low/medium confidence reasons (score < 85):**
- Each sub-score < 60 generates a warning (e.g. "High baseline noise detected")
- Fallback: "Multiple moderate quality concerns"

**Reason strings must:**
1. Be plain English, max 60 characters
2. Reference the specific sub-score domain (noise, T-end, beat, formula)
3. Not contain raw numbers or internal variable names

---

## 8. Validation Benchmarks

The confidence model is validated against these reference benchmarks:

| Dataset | Target | Metric |
|---------|--------|--------|
| QTDB | MAE < 10 ms | T-end delineation |
| LUDB | MAE < 8 ms | T-end delineation |
| CSE | MAE < 12 ms | T-end delineation |
| Clinical (bias) | < 5 ms | Bland–Altman bias |
| Clinical (±10 ms coverage) | > 85% | Coverage fraction |

A measurement is considered well-calibrated when its confidence score correlates
positively with its Bland–Altman agreement against expert reference annotations.

---

## 9. Extension Points

| Extension | Interface |
|-----------|-----------|
| Custom sub-score | Pass `weights` dict to `measurement_confidence()` |
| New T-end method | Add to `tend/` module; update `compute_agreement()` |
| New morphology class | Add case to `morphology/classifier.py` |
| Population-level calibration | Fit threshold multipliers on labelled dataset |
| Bayesian uncertainty | Replace point-estimate T-end with MC Dropout posterior |
