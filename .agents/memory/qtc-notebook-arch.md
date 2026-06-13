---
name: QTc Notebook Architecture
description: 11-notebook pipeline structure, evidence independence rules, output artifacts, and ML dependencies.
---

## Pipeline Structure

11 notebooks replacing original 16. Generator script: `generate_notebooks.py`.

| # | Notebook | Output Artifact |
|---|---|---|
| 01 | dataset_audit | inventory.csv, clinical_context.parquet |
| 02 | signal_quality | signal_quality_features.parquet |
| 03 | delineation_validation | delineation_features.parquet |
| 04 | twave_analysis | twave_features.parquet |
| 05 | qt_measurement | qt_measurements.parquet, measurement_reliability.parquet |
| 06 | qtc_methods | qtc_comparison.parquet |
| 07 | cross_dataset_validation | cross_dataset_results.parquet |
| 08 | failure_modes | failure_modes.parquet |
| 09 | confidence_features | confidence_features.parquet |
| 10 | confidence_model | confidence_predictions.parquet |
| 11 | decision_model | decision_results.parquet |

## Evidence Independence Rule
- 02 (signal quality) and 05 (measurement reliability) are strictly independent
- 09 is the FIRST notebook allowed to merge all streams
- Forbidden features in 02: bsqi, wsqi, lead_agreement_score, qt_ms, etc.
- Forbidden features in 05: bw_index, snr_db, signal_quality_score, etc.

## ML Stack
- XGBoost: available (v3.2.0)
- LightGBM: NOT available (libgomp.so.1 missing) — use HistGradientBoostingClassifier
- SHAP: available (v0.52.0)
- sklearn: available

## Column Name Gotcha
In notebook 09, `mean_beat_agreement_score` is renamed to `mean_beat_agreement` in the rename_map.
Notebook 11 must use `mean_beat_agreement` (not `mean_beat_agreement_score`).

## Output Path
Notebooks use `../outputs/` (relative to notebooks/ dir).
Actual path: `/home/runner/workspace/outputs/`.
