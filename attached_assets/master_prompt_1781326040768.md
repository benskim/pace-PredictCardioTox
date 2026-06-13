QTc Measurement Confidence Engine

Version: 1.0

Status: Production Notebook Generation Prompt

Project Objective

You are building a research-grade machine learning pipeline for a QTc Measurement Confidence Engine.

This project does NOT build a QT measurement algorithm.

The project estimates:

How trustworthy a QT/QTc measurement is.

The final output is:

confidence_probability ∈ [0,1]

representing the probability that a QT/QTc measurement is reliable.

Mandatory Architecture

The system is composed of five independent evidence domains.

Signal Quality Evidence
Delineation Evidence
Morphology Evidence
Measurement Reliability Evidence
Clinical Context Evidence

These domains must remain independent until Notebook 09.

No notebook may violate this requirement.

Evidence Independence Rule

Critical Requirement

Signal Quality and Measurement Reliability are separate concepts.

Signal Quality evaluates:

noise
artifacts
signal corruption

Measurement Reliability evaluates:

agreement
consistency
repeatability

These domains must never share features before Notebook 09.

Mandatory Dependency Graph

Allowed

02 Signal Quality
        ↓
        09

03 Delineation Validation
        ↓
        09

04 T-Wave Morphology
        ↓
        09

05 QT Measurement Reliability
        ↓
        09

06 QTc Methods
        ↓
        09

09 Confidence Features
        ↓

10 Confidence Model
        ↓

11 Decision Model

[Raw Datasets] 
   ├──> 01 Dataset Audit ───────> inventory.csv
   ├──> 02 Signal Quality ──────> signal_quality_features.parquet ───┐
   ├──> 03 Delineation ─────────> delineation_features.parquet ──────┼─> 09 Confidence Features
   ├──> 04 T-Wave Morphology ───> twave_features.parquet ────────────┤
   └──> 05 QT Measurement ──────> measurement_reliability.parquet ───┘

Forbidden

02 -> 05
05 -> 02

02 -> 04
04 -> 05

03 -> 05
05 -> 03

Any such dependency constitutes a design violation.

Global Requirements

All notebooks must:

be reproducible
use fixed random seeds
contain markdown explanations
save outputs to parquet
validate schema before export
follow DATA_CONTRACT.md exactly

No notebook may redefine:

identifiers
units
target definitions
aggregation rules
confidence definitions
Notebook 01
dataset_audit.ipynb

Purpose:

Inventory and standardize datasets.

Input:

Raw datasets

Output:

inventory.csv

Responsibilities:

dataset inspection
metadata extraction
lead inventory
annotation inventory
sampling-rate verification

No feature engineering.

* Generate a standardized record index mapping each unique record_id to its physical file path to drive the parallel processing loop in Notebooks 02-06.

Notebook 02
signal_quality.ipynb

Purpose:

Generate signal quality evidence only.

Inputs:

ECG waveform
sampling rate
ADC metadata

Allowed Features:

bw_index
bw_rms_mv

hfn_index

pli_index

snr_db

clipping_ratio

flatline_ratio

electrode_motion_index

signal_quality_score

Prohibited Features:

bsqi
wsqi

lead_agreement_score
beat_agreement_score

qt_variance_leads
qt_variance_beats

repeatability_score
internal_consistency_score

Output:

signal_quality_features.parquet

This notebook must remain measurement-agnostic.

Notebook 03
delineation_validation.ipynb

Purpose:

Quantify boundary uncertainty.

Inputs:

ECG waveform
delineation outputs

Output:

delineation_features.parquet

Required Features:

p_onset_uncertainty_ms
p_offset_uncertainty_ms

qrs_onset_uncertainty_ms
qrs_offset_uncertainty_ms

t_onset_uncertainty_ms
t_end_uncertainty_ms

boundary_confidence

No confidence modeling.

Notebook 04
twave_analysis.ipynb

Purpose:

Characterize T-wave ambiguity.

Inputs:

ECG waveform
delineated T-wave boundaries

Output:

twave_features.parquet

Required Features:

t_amplitude_mv

t_width_ms

t_slope

t_symmetry

biphasic_flag

flattened_flag

morphology_cluster

t_end_ambiguity_score

morphology_confidence

No agreement metrics.

No signal quality metrics.

Notebook 05
qt_measurement.ipynb

Purpose:

Generate measurement reliability evidence.

Inputs:

QT measurements
beat measurements
lead measurements

Output:

qt_measurements.parquet

measurement_reliability.parquet

Required Features:

bsqi

wsqi

lead_agreement_score

beat_agreement_score

qt_variance_leads

qt_variance_beats

missing_lead_penalty

repeatability_score

internal_consistency_score

Forbidden Inputs:

bw_index
hfn_index
snr_db
clipping_ratio
flatline_ratio
electrode_motion_index
signal_quality_score

Notebook 05 must not consume outputs from Notebook 02.

Notebook 06
qtc_methods.ipynb

Purpose:

Calculate QTc using standard formulas.

Required Outputs:

rr_ms

qtc_bazett

qtc_fridericia

qtc_framingham

qtc_hodges

qtc_formula_variance

qtc_formula_bias

Output:

qtc_comparison.parquet

No confidence calculations.

Notebook 07
cross_dataset_validation.ipynb

Purpose:

Evaluate dataset shift.

Output:

cross_dataset_results.parquet

Metrics:

shift_score

lead_distribution_shift

morphology_shift

confidence_stability_score
Notebook 08
failure_modes.ipynb

Purpose:

Discover systematic failure modes.

Output:

failure_modes.parquet

Allowed Categories:

BW
HFN
PLI
EM
ARRHYTHMIA
TWAVE_AMBIGUITY
LEAD_DISAGREEMENT
DELINEATION_FAILURE

Notebook 09
confidence_features.ipynb

Purpose:

First evidence fusion stage.

This is the first notebook allowed to merge outputs from:

02 Signal Quality

03 Delineation

04 Morphology

05 Measurement Reliability

06 QTc

Output:

confidence_features.parquet

Required Aggregations:

mean
std
max
p95

for all continuous features whenever applicable.

Never retain only means.

required:
Aggregation rules (mean, std, max, p95) apply strictly when collapsing high-cardinality levels (Beat/Lead) to the Record level. Do not attempt over-aggregation on features that are already natively calculated at the Record level.

Notebook 10
confidence_model.ipynb

Purpose:

Train confidence prediction model.

Inputs:

confidence_features.parquet

Phase 1 Targets:

lead_agreement_score

beat_agreement_score

repeatability_score

measurement_stability_score

Phase 1 must not require QTDB.

Models:

XGBoost

LightGBM

Random Forest

Required Outputs:

confidence_probability

Range:

0.0 – 1.0

Required Analyses:

ROC-AUC

PR-AUC

Calibration Curve

SHAP
Notebook 11
decision_model.ipynb

Purpose:

Convert confidence probability into operational actions.

Inputs:

confidence_probability

Required Outputs:

ACCEPT

REVIEW

REJECT

Thresholds:

Must be derived from validation data.

Hardcoded thresholds are forbidden.

Required Evaluation:

coverage

review_rate

error_capture_rate

clinical_safety_analysis
Leakage Prevention

Forbidden Features Anywhere Upstream

absolute_qt_error_ms

expert_disagreement_ms

true_t_end_error_ms

confidence_probability

confidence_label

These may only appear in Notebook 10 or later.

Deliverable Requirement

For every notebook generate:

Markdown overview
Configuration section
Processing pipeline
Validation checks
Artifact export
Summary statistics
Reproducibility metadata

Every notebook must run independently and produce artifacts conforming to DATA_CONTRACT.md.