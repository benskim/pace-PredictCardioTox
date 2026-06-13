# Master Prompt — QTc Confidence Engine

## Project Identity

**Repository:** `predictcardiotox-qtc-research`
**Version:** 0.2.0
**Mission:** Quantify whether QTc ECG measurements can be trusted, not just what they are.

> "Not only measuring QTc. Determining whether QTc results can be trusted."

---

## Problem Statement

In Phase I/II/III cardiac safety studies, regulatory decisions (ICH E14) may rest on QTc changes of only a few milliseconds. Conventional analysis pipelines report a single QTc value without communicating the reliability of that value. Noise contamination, T-wave morphology ambiguity, beat-to-beat variability, and delineation uncertainty can each introduce measurement error large enough to reverse a cardiac safety conclusion.

**The QTc Confidence Engine does not predict toxicity.** It quantifies whether a given ECG measurement is trustworthy, explains why it may not be, and prioritises expert review accordingly.

---

## Scope

### In Scope
| Domain | Deliverable |
|--------|-------------|
| Signal quality assessment | SQI (SNR, kurtosis, baseline drift, flatline fraction) |
| Wave delineation | 1-D U-Net segmentation; T-end multi-method agreement |
| T-wave analysis | T-end detection (tangent, derivative, wavelet, threshold) |
| QT measurement | Beat selection, interval measurement, tangent method |
| QTc correction | Fridericia, Bazett, Framingham, Hodges; formula agreement |
| Longitudinal tracking | QTc shift (ΔQTcF), subject drift summary |
| Confidence scoring | Composite 0–100 score; explainable penalty decomposition |
| Clinical validation | Bland–Altman analysis; expert variability; cross-dataset metrics |
| Review prioritisation | Tier-based decision + actionable queue output |
| Interactive demo | Streamlit Reliability Platform (5 views) |

### Out of Scope
- Molecular toxicity prediction (QSAR, in-silico hERG)
- TdP (Torsades de Pointes) risk prediction
- Clinical trial outcome or FDA approval prediction
- Real-time ECG acquisition or device integration

---

## Repository Layout

```
predictcardiotox-qtc-research/
├── app/                        # Streamlit reliability platform
│   ├── validation_engine.py    # 5-view dashboard entry point
│   └── demo_data.py            # Deterministic synthetic demo generator
├── src/ecg_analytics/          # Core library (pip-installable)
│   ├── confidence/             # Composite confidence scoring engine
│   ├── datasets/               # ECGRecord adapters (QTDB, LUDB, CSE)
│   ├── delineation/            # 1-D U-Net wave segmentation
│   ├── morphology/             # T-wave morphology classifier
│   ├── preprocessing/          # Filters, noise injection, SQI
│   ├── qt/                     # T-end detection, QT measurement
│   ├── qtc/                    # QTc formulas + longitudinal tracking
│   ├── tend/                   # Multi-method T-end agreement
│   ├── validation/             # Clinical metrics, expert variability
│   └── visualization/          # ECG, delineation, noise, validation plots
├── notebooks/                  # Research notebooks 01–16
├── tests/                      # pytest suite (162+ unit tests)
├── scripts/                    # PhysioNet download helpers
└── docs/                       # Architecture + spec documents
```

---

## Notebook Curriculum (01–16)

| # | Notebook | Domain |
|---|----------|--------|
| 01 | Dataset Exploration | ECGRecord loading, QTDB/LUDB/CSE adapters |
| 02 | Signal Quality | SQI computation, SNR estimation |
| 03 | Wave Delineation | U-Net inference, mask decoding |
| 04 | T-Wave Analysis | T-peak/T-wave region extraction |
| 05 | Tangent Method | T-end detection via tangent intersection |
| 06 | QT Measurement | Beat-level QT interval measurement |
| 07 | QTc Calculations | All four correction formulas |
| 08 | QTc Shift Tracking | Longitudinal ΔQTcF, subject drift |
| 09 | LUDB Validation | Delineation accuracy on LUDB ground truth |
| 10 | Cross-Dataset Validation | QT/QTc metrics across QTDB, LUDB, CSE |
| 11 | Noise Robustness | SNR degradation vs. measurement error |
| 12 | Error Analysis | Bland–Altman, error distribution plots |
| 13 | Measurement Confidence | Full composite confidence score demo |
| 14 | Expert Variability | Inter-rater agreement analysis |
| 15 | Beat Variability | Beat-stability sub-score demonstration |
| 16 | Clinical Validation | Bias, LoA, coverage at ±5/10/20 ms |

---

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Language | Python ≥ 3.12 |
| Signal Processing | `neurokit2`, `scipy`, `wfdb` |
| Deep Learning | `torch` (1-D U-Net, Bayesian T-end) |
| Data | `numpy`, `pandas`, `pyarrow` |
| Visualisation | `matplotlib`, `plotly` |
| App | `streamlit` ≥ 1.35 |
| Datasets | PhysioNet QTDB, LUDB, CSE (via `wfdb`) |
| Build | `setuptools`, `pyproject.toml` |
| Testing | `pytest`, `pytest-cov` |
| Linting | `ruff` |

---

## Guiding Principles

1. **Reliability is the product** — QTc value is secondary to measurement trust.
2. **Explainability is mandatory** — every confidence point deducted must have a named reason.
3. **Determinism over black-box ML** — confidence score logic is rule-based and auditable.
4. **Clinical relevance** — thresholds and metrics align with ICH E14 / regulatory norms.
5. **Research grade** — notebooks are executable, reproducible, and self-contained demos.
