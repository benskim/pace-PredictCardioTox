---
name: QTc API Quirks
description: Correct field names and signatures for ecg_analytics library APIs used in notebooks.
---

## Key API Field Names

### BeatStabilityResult (beat_stability.py)
- `.stability_score` ✓
- `.iqr_qt_ms` ✓ (NOT `.iqr`)
- `.cv` ✓
- `.mean_qt_ms`, `.median_qt_ms`, `.sd_qt_ms`

### FormulaAgreementResult (formula_agreement.py)
- `.agreement_score` ✓ (NOT `.score`)
- `.spread_ms`, `.mean_qtc_ms`, `.sd_qtc_ms`, `.qtc_values`

### TEndAgreement (tend/agreement.py)
- `.stability_score` ✓
- `.stability_metrics` dict: keys = mean_ms, sd_ms, iqr_ms, range_ms
- `.method_results` dict: tangent, threshold, derivative, wavelet
- `.valid_results_ms` dict

### QTcShiftResult (qtc/longitudinal.py)
- `.exceeds_threshold` ✓ (NOT `.exceeds_10ms` or `.exceeds_20ms`)

### QTMeasurement (qt/measurement.py)
- `.r_peak`, `.q_onset`, `.t_end`, `.t_peak`
- `.qt_samples`, `.qt_ms`, `.rr_ms`

### signal_quality_index() returns
- snr_db, kurtosis, baseline_drift, flatline_fraction
- Does NOT include bw_index, hfn_index, pli_index — these must be computed separately

### compute_all_qtc() returns dict
- Keys: "fridericia", "bazett", "framingham", "hodges"
- Hodges HR is derived internally from RR

## np.average weight shape mismatch
When computing wsqi with `np.average(qt_arr, weights=weights)`, ensure
`len(qt_arr) == len(weights)`. Slice both to `min_len = min(len(qt_arr), len(rr_arr))`.
