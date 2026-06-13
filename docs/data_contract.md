# Data Contract — QTc Confidence Engine

This document specifies every public data schema in the `ecg_analytics` library.
All notebooks and the Streamlit app must conform to these contracts.

---

## 1. Core Record Schema

### `ECGRecord`
**Module:** `ecg_analytics.datasets.base`

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | `str` | Unique ID within dataset (e.g. `"sel100"`) |
| `signal` | `np.ndarray` shape `(n_samples, n_leads)` | Raw ADC samples, mV |
| `fs` | `float` | Sampling frequency in Hz |
| `lead_names` | `list[str]` | Lead channel names (e.g. `["II", "V5"]`) |
| `annotations` | `list[Annotation]` | Fiducial-point annotations |
| `metadata` | `dict` | Arbitrary key–value extras (units, comments) |

**Derived properties (read-only):**

| Property | Returns | Formula |
|----------|---------|---------|
| `duration_s` | `float` | `signal.shape[0] / fs` |
| `n_leads` | `int` | `signal.shape[1]` (or 1 if 1-D) |
| `lead(idx=0)` | `np.ndarray` 1-D | Single-lead slice |

---

### `Annotation`
**Module:** `ecg_analytics.datasets.base`

| Field | Type | Description |
|-------|------|-------------|
| `sample` | `int` | Sample index (0-based) |
| `symbol` | `str` | PhysioNet symbol: `"p"`, `"N"`, `"t"`, `")"` etc. |
| `label` | `str` | Human label: `"T-peak"`, `"T-end"`, `"QRS-onset"` |
| `lead` | `int` | Lead index (0-based), default `0` |

---

## 2. Signal Quality Schema

### `signal_quality_index()` → `dict[str, float]`
**Module:** `ecg_analytics.preprocessing.quality`

| Key | Unit | Description |
|-----|------|-------------|
| `snr_db` | dB | Estimated signal-to-noise ratio |
| `kurtosis` | — | Fisher kurtosis; high values indicate spike artifacts |
| `baseline_drift` | mV | Range of low-frequency envelope (2-second smooth) |
| `flatline_fraction` | [0, 1] | Fraction of samples with near-zero derivative |

**Inputs:** `signal: np.ndarray`, `fs: float`

---

## 3. Confidence Score Schema

### `ConfidenceResult`
**Module:** `ecg_analytics.confidence.confidence_score`

| Field | Type | Range | Description |
|-------|------|-------|-------------|
| `score` | `float` | [0, 100] | Final composite confidence score |
| `tier` | `str` | see tiers | Interpretation tier |
| `sub_scores` | `dict[str, float]` | [0, 100] each | Component scores |
| `weights` | `dict[str, float]` | sums to 1.0 | Applied weights per component |

**Sub-score keys** (all [0, 100]):

| Key | Weight (default) | Source function |
|-----|-----------------|----------------|
| `signal_quality` | 0.20 | `signal_quality_subscore()` |
| `tend_stability` | 0.25 | `tend_stability_subscore()` |
| `morphology` | 0.15 | `morphology_risk_subscore()` |
| `formula_agreement` | 0.15 | `formula_agreement_score()` |
| `beat_stability` | 0.25 | `beat_stability_score()` |

**Tier mapping:**

| `tier` string | Score range | Clinical decision |
|--------------|-------------|------------------|
| `"high"` | ≥ 90 | Auto Accept |
| `"review"` | 70 – 89 | Review Recommended |
| `"manual_review"` | < 70 | Manual Review Required |

---

### `BeatStabilityResult`
**Module:** `ecg_analytics.confidence.beat_stability`

| Field | Type | Description |
|-------|------|-------------|
| `score` | `float` | Beat stability sub-score [0, 100] |
| `mean_qt` | `float` | Mean QT across beats (ms) |
| `median_qt` | `float` | Median QT (ms) |
| `sd_qt` | `float` | Standard deviation of QT (ms) |
| `iqr_qt` | `float` | Interquartile range of QT (ms) |
| `cv_qt` | `float` | Coefficient of variation |
| `n_beats` | `int` | Number of beats analysed |

---

### `FormulaAgreementResult`
**Module:** `ecg_analytics.confidence.formula_agreement`

| Field | Type | Description |
|-------|------|-------------|
| `score` | `float` | Agreement sub-score [0, 100] |
| `qtc_values` | `dict[str, float]` | QTcF, QTcB, QTcFram, QTcH (ms) |
| `max_spread_ms` | `float` | Max − Min QTc across formulas (ms) |

---

## 4. QTc Formulas Schema

### `compute_all_qtc(qt_ms, rr_ms)` → `dict[str, float]`
**Module:** `ecg_analytics.qtc.formulas`

| Key | Formula | Notes |
|-----|---------|-------|
| `fridericia` | QT / RR^(1/3) | Default; preferred for drug trials |
| `bazett` | QT / √RR | Over-corrects at high HR |
| `framingham` | QT + 0.154×(1−RR) | Linear correction |
| `hodges` | QT + 1.75×(HR−60) | HR-explicit form |

**Units:** `qt_ms` in ms, `rr_ms` in ms, returns ms.

---

### `QTcShiftResult`
**Module:** `ecg_analytics.qtc.longitudinal`

| Field | Type | Description |
|-------|------|-------------|
| `subject_id` | `str` | Subject identifier |
| `baseline_qtc` | `float` | Baseline QTcF (ms) |
| `peak_qtc` | `float` | Maximum post-dose QTcF (ms) |
| `delta_qtc` | `float` | ΔQTcF = peak − baseline (ms) |
| `exceeds_10ms` | `bool` | ΔQTcF > 10 ms flag |
| `exceeds_20ms` | `bool` | ΔQTcF > 20 ms flag (regulatory concern) |

---

## 5. Validation Metrics Schema

### `delineation_metrics(predicted, reference, fs)` → `dict[str, float]`

| Key | Unit | Description |
|-----|------|-------------|
| `mae_ms` | ms | Mean absolute error |
| `median_error_ms` | ms | Median signed error |
| `p95_error_ms` | ms | 95th percentile absolute error |
| `mean_error_ms` | ms | Mean signed error (bias) |
| `std_error_ms` | ms | Standard deviation of errors |

### `qt_metrics(predicted, reference)` → `dict[str, float]`

| Key | Unit | Description |
|-----|------|-------------|
| `mae_ms` | ms | Mean absolute error |
| `rmse_ms` | ms | Root mean squared error |
| `mean_error_ms` | ms | Signed bias |
| `std_error_ms` | ms | SD of errors |

### `qtc_metrics(predicted, reference)` → `dict[str, float]`
Same keys as `qt_metrics`.

### `longitudinal_metrics(predicted_delta, reference_delta)` → `dict[str, float]`

| Key | Unit | Description |
|-----|------|-------------|
| `delta_qtc_mae_ms` | ms | MAE on ΔQTcF |
| `delta_qtc_rmse_ms` | ms | RMSE on ΔQTcF |
| `delta_qtc_mean_error_ms` | ms | Signed bias on ΔQTcF |

---

## 6. Clinical Validation Schema

### `BlandAltmanResult`
**Module:** `ecg_analytics.validation.clinical`

| Field | Type | Description |
|-------|------|-------------|
| `bias` | `float` | Mean(predicted − reference), ms |
| `sd` | `float` | SD of differences, ms |
| `loa_lower` | `float` | bias − 1.96 × SD, ms |
| `loa_upper` | `float` | bias + 1.96 × SD, ms |
| `coverage_5ms` | `float` | Fraction within ±5 ms [0, 1] |
| `coverage_10ms` | `float` | Fraction within ±10 ms [0, 1] |
| `coverage_20ms` | `float` | Fraction within ±20 ms [0, 1] |
| `n` | `int` | Number of paired measurements |

---

## 7. Demo / App Schema

### `MeasurementRecord`
**Module:** `app.demo_data`

| Field | Type | Description |
|-------|------|-------------|
| `record_id` | `str` | ECG record ID (e.g. `"ECG-A-001"`) |
| `subject_id` | `str` | Subject code (e.g. `"SUBJ-101"`) |
| `timepoint` | `str` | Study timepoint label |
| `lead` | `str` | Lead name (e.g. `"II"`) |
| `qt_ms` | `float` | Raw QT interval (ms) |
| `rr_ms` | `float` | RR interval (ms) |
| `hr_bpm` | `float` | Heart rate (bpm) |
| `qtcf_ms` | `float` | Fridericia-corrected QTc (ms) |
| `qtcb_ms` | `float` | Bazett-corrected QTc (ms) |
| `signal_quality` | `float` | Sub-score [0, 100] |
| `beat_consistency` | `float` | Sub-score [0, 100] |
| `t_end_confidence` | `float` | Sub-score [0, 100] |
| `noise_impact` | `float` | Sub-score [0, 100] |
| `qt_stability` | `float` | Sub-score [0, 100] |
| `confidence_score` | `float` | Composite score [0, 100] |
| `decision` | `str` | `"Auto Accept"` / `"Manual Review Recommended"` / `"Measurement Unreliable"` |
| `base_score` | `float` | Always 100.0 |
| `noise_penalty` | `float` | Penalty deducted [0, 100] |
| `beat_variability_penalty` | `float` | Penalty deducted [0, 100] |
| `t_end_ambiguity_penalty` | `float` | Penalty deducted [0, 100] |
| `formula_disagreement_penalty` | `float` | Penalty deducted [0, 100] |
| `reasons` | `list[str]` | Plain-language explainability strings |

---

## 8. Notebook Cell Structure Contract

Every research notebook must follow this cell ordering:

| Cell # | Type | Required Content |
|--------|------|-----------------|
| 0 | Markdown | `# NN — Title` + 1-paragraph description |
| 1 | Code | `sys.path.insert(0, '../src')` path setup |
| 2+ | Code | Imports from `ecg_analytics.*` |
| next | Markdown | Section header (`## Section`) |
| next | Code | Implementation / demonstration |
| last | Code | Summary output or visualisation |

**Validation rules:**
- All cells must have a valid `id` field matching `^[a-zA-Z0-9-_]+$`
- `nbformat_minor` must be ≥ 5
- No cell may rely on external data files unless the download is commented out with a note
- All figures must use `plt.tight_layout()` or Plotly
