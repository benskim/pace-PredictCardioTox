# PredictCardioTox — QTc Analytics Research Workspace

A **Codespaces-ready**, notebook-driven research environment for evaluating the
scientific reliability of QT interval measurement and QTc analytics in clinical
trial safety studies.

> **Primary question:** *Can this QT/QTc measurement be trusted?*
>
> The workspace answers this by evaluating measurement reliability across datasets,
> noise conditions, and patient populations — and producing an explainable
> **Measurement Confidence Score** for every QTc result.

---

## Scientific Approach

The workspace implements a **hybrid signal-processing + explainable-ML** pipeline:

```
ECG → preprocessing → wave delineation (1-D U-Net)
    → T-wave region extraction → geometric tangent method
    → T-end determination → QT measurement
    → QTc calculation (Fridericia / Bazett / Framingham / Hodges)
    → longitudinal shift analytics
    → measurement confidence scoring
```

The final T-end decision is always **explainable** — the tangent method provides
a geometric rationale rather than a black-box prediction.

### QTc Confidence Engine

Every measurement is accompanied by a **Measurement Confidence Score** (0–100)
aggregated from five explainable sub-scores:

| Sub-score | Weight | What it measures |
|-----------|--------|------------------|
| Signal Quality | 20 % | SNR, flatline, drift, kurtosis |
| T-End Stability | 25 % | Agreement across 4 T-end methods (tangent, threshold, derivative, wavelet) |
| Morphology Risk | 15 % | T-wave shape difficulty (normal → merged T-U) |
| Formula Agreement | 15 % | QTc spread across Fridericia / Bazett / Framingham / Hodges |
| Beat Stability | 25 % | Beat-to-beat QT coefficient of variation |

**Interpretation tiers:**

| Score | Tier | Action |
|-------|------|--------|
| 90–100 | High Confidence | Accept measurement |
| 70–89 | Review Recommended | Flag for secondary review |
| < 70 | Manual Review Required | Do not use without expert validation |

## Research Priorities

| Priority | Focus Area |
|----------|-----------|
| 1 | T-wave Delineation |
| 2 | T-end Determination |
| 3 | QT Measurement |
| 4 | QTc Shift Tracking |
| 5 | Noise-Robust R-Peak Detection |

---

## Quick Start (Codespaces)

1. Open this repository in **GitHub Codespaces**.
2. The dev container installs Python 3.12 and all dependencies automatically.
3. Start Jupyter Lab:

```bash
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser
```

### Local Setup

```bash
python -m pip install -e ".[dev]"
pytest
```

---

## Repository Structure

```
predictcardiotox-qtc-research/
├── .devcontainer/          # Codespaces / dev container config
├── notebooks/
│   ├── 01_dataset_exploration.ipynb
│   ├── 02_signal_quality.ipynb
│   ├── 03_wave_delineation.ipynb
│   ├── 04_t_wave_analysis.ipynb
│   ├── 05_tangent_method.ipynb
│   ├── 06_qt_measurement.ipynb
│   ├── 07_qtc_calculations.ipynb
│   ├── 08_qtc_shift_tracking.ipynb
│   ├── 09_ludb_validation.ipynb
│   ├── 10_cross_dataset_validation.ipynb
│   ├── 11_noise_robustness.ipynb
│   └── 12_error_analysis.ipynb
├── src/ecg_analytics/
│   ├── datasets/           # QTDB, LUDB, CSE adapters (common ECGRecord API)
│   ├── preprocessing/      # Filters, noise injection, signal quality
│   ├── delineation/        # 1-D U-Net segmentation model
│   ├── qt/                 # Tangent method, T-end, QT measurement
│   ├── qtc/                # QTc formulas + longitudinal shift tracking
│   ├── tend/               # T-end multi-method agreement (tangent, threshold, derivative, wavelet)
│   ├── morphology/         # T-wave morphology classification and risk scoring
│   ├── confidence/         # Measurement Confidence Engine (composite 0–100 score)
│   ├── validation/         # Metrics, pipeline, clinical validation, expert variability
│   └── visualization/      # Publication-quality plots
├── tests/                  # Unit tests
├── scripts/                # Helper scripts
├── data/                   # Local data (git-ignored)
└── reports/                # Generated reports
```

---

## Supported QTc Formulas

| Formula | Equation | Notes |
|---------|----------|-------|
| **Fridericia** | QT / RR^(1/3) | **Default reporting formula** |
| Bazett | QT / √RR | Most widely used historically |
| Framingham | QT + 154·(1 − RR) | Linear correction |
| Hodges | QT + 1.75·(HR − 60) | Heart-rate based |

All formulas are computed simultaneously via `compute_all_qtc()`.

---

## Target Datasets

All datasets use the same interface:

```python
record = dataset.load_record(record_id)
signal = record.signal       # np.ndarray (samples, leads)
annotations = record.annotations
fs = record.fs
```

| Dataset | Records | Annotations | Source |
|----------|----------|----------|----------|
| PhysioNet QT Database (QTDB) | ~100 | Expert QT fiducials and T-end annotations | PhysioNet |
| LUDB | 200 | Detailed P/QRS/T wave boundaries (12-lead) | PhysioNet |
| MIT-BIH Noise Stress Test Database (NSTDB) | Multiple | Controlled noise recordings | PhysioNet |
| INCART Database | 75 | Arrhythmia annotations (12-lead ECG) | PhysioNet |
| PTB-XL | 21,000+ | Diagnostic labels and clinical metadata | PhysioNet |

** more details : data/target_datasets.md

---

## Validation Metrics

### Delineation
- T-end MAE (ms), Median Error, 95th Percentile Error

### QT Measurement
- QT MAE, QT RMSE

### QTc Accuracy
- QTc MAE, QTc RMSE (per formula)

### Longitudinal
- Delta-QTc Error, Subject-level drift tracking

---

## Noise Robustness Evaluation

Controlled experiments with four noise types at five SNR levels:

| Noise Type | SNR Levels |
|------------|-----------|
| Baseline Wander | 24, 18, 12, 6, 0 dB |
| Muscle Noise (EMG) | 24, 18, 12, 6, 0 dB |
| Powerline Interference | 24, 18, 12, 6, 0 dB |
| Synthetic Motion Artifact | 24, 18, 12, 6, 0 dB |

---

## Notebook Workflow

| # | Notebook | Purpose |
|---|----------|---------|
| 01 | Dataset Exploration | Load and inspect QTDB / LUDB / CSE records |
| 02 | Signal Quality | Assess SNR, baseline drift, flatline detection |
| 03 | Wave Delineation | 1-D U-Net P/QRS/T segmentation |
| 04 | T-wave Analysis | T-peak detection and region extraction |
| 05 | Tangent Method | Geometric T-end determination |
| 06 | QT Measurement | End-to-end QT interval pipeline |
| 07 | QTc Calculations | All four correction formulas |
| 08 | QTc Shift Tracking | Longitudinal delta-QTc analysis |
| 09 | LUDB Validation | Delineation accuracy against expert annotations |
| 10 | Cross-Dataset Validation | Generalizability across databases |
| 11 | Noise Robustness | Degradation under controlled noise |
| 12 | Error Analysis | Bland-Altman, distributions, outliers |
| 13 | Measurement Confidence | Confidence Engine demo with sub-score breakdown |
| 14 | Expert Variability | Inter-observer agreement metrics |
| 15 | Beat Variability | Beat-to-beat QT stability analysis |
| 16 | Clinical Validation | Bland-Altman, coverage at ±5/10/20 ms |

---

## Running Tests

```bash
pytest --cov=ecg_analytics --cov-report=term-missing tests/
```

---

## License

MIT
