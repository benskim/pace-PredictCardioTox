# QTc Measurement Validation Engine

> **We do not only calculate QTc. We quantify whether a QTc result should be trusted.**

A **measurement reliability platform** that produces an explainable, auditable
confidence score for every QTc measurement — enabling pharmaceutical sponsors,
CROs, and ECG core labs to distinguish trusted measurements from those requiring
manual review.

---

## Product Vision

| Competitors show | This product shows |
|------------------|-------------------|
| QTc Value | QTc **Reliability** |
| "What is the QTc?" | "Can this QTc be **trusted**?" |

**Confidence is the hero metric, not QTc.**

---

## Demo Application

The interactive demo is a Streamlit application with three views:

### 1. Measurement Validation (Primary Screen)

- **Confidence Score** — dominant visual element (0–100%)
- **Decision** — Auto Accept / Manual Review Recommended / Measurement Unreliable
- **QTcF** — secondary, small
- **Confidence Drivers** — Signal Quality, Beat Consistency, T-End Confidence, Noise Impact, QT Stability
- **Score Decomposition** — transparent penalty breakdown
- **Explanation** — plain-language reasons in clinician-friendly language

### 2. Side-by-Side Reliability Comparison

The "aha" moment: two ECGs with **nearly identical QTc values** but **completely
different reliability scores**. Demonstrates why measurement confidence matters
more than the measurement itself.

### 3. Research Analytics

Study-level reliability metrics:
- Confidence distribution
- Review required rate
- Signal quality distribution
- Confidence vs QTcF scatter
- Confidence trend over time
- Study-level reliability summary table

### Run the Demo

```bash
pip install -e ".[dev]"
streamlit run app/validation_engine.py
```

---

## Confidence Scoring Philosophy

The score is:
- **Consistent** — same inputs always produce the same output
- **Explainable** — every point deducted has a named reason
- **Transparent** — full penalty breakdown visible to the user
- **Auditable** — deterministic, rule-based logic (no black-box ML)

```
Confidence = Base Score (100)
           − Noise Penalty
           − Beat Variability Penalty
           − T-End Ambiguity Penalty
           − Formula Disagreement Penalty
```

### Sub-Scores (0–100 each)

| Sub-score | Weight | What it measures |
|-----------|--------|------------------|
| Signal Quality | 20% | SNR, flatline fraction, drift, kurtosis |
| T-End Stability | 25% | Agreement across 4 T-end methods (tangent, threshold, derivative, wavelet) |
| Morphology Risk | 15% | T-wave shape difficulty (normal → merged T-U) |
| Formula Agreement | 15% | QTc spread across Fridericia / Bazett / Framingham / Hodges |
| Beat Stability | 25% | Beat-to-beat QT coefficient of variation |

### Interpretation Tiers

| Score | Tier | Decision |
|-------|------|----------|
| ≥ 85 | High Confidence | Auto Accept |
| 60–84 | Moderate | Manual Review Recommended |
| < 60 | Low Confidence | Measurement Unreliable |

---

## Repository Structure

```
predictcardiotox-qtc-research/
├── app/
│   ├── validation_engine.py   # Streamlit demo application
│   └── demo_data.py           # Deterministic demo data generator
├── src/ecg_analytics/
│   ├── confidence/            # Measurement Confidence Engine
│   ├── tend/                  # T-end multi-method agreement
│   ├── morphology/            # T-wave morphology classification
│   ├── preprocessing/         # Filters, noise, signal quality
│   ├── qt/                    # QT measurement pipeline
│   ├── qtc/                   # QTc formulas + longitudinal tracking
│   ├── datasets/              # QTDB, LUDB, CSE adapters
│   ├── delineation/           # 1-D U-Net segmentation
│   ├── validation/            # Clinical validation, expert variability
│   └── visualization/         # Publication-quality plots
├── notebooks/                 # Research notebooks (01–16)
├── tests/                     # Unit tests (162 tests)
├── scripts/                   # Helper scripts
└── pyproject.toml
```

---

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run validation engine demo
streamlit run app/validation_engine.py

# Run tests
pytest --cov=ecg_analytics --cov-report=term-missing tests/
```

---

## Supported QTc Formulas

| Formula | Equation | Notes |
|---------|----------|-------|
| **Fridericia** | QT / RR^(1/3) | **Default reporting formula** |
| Bazett | QT / √RR | Most widely used historically |
| Framingham | QT + 154·(1 − RR) | Linear correction |
| Hodges | QT + 1.75·(HR − 60) | Heart-rate based |

---

## Target Datasets

| Dataset | Records | Annotations | Source |
|---------|---------|-------------|--------|
| PhysioNet QT Database | ~100 | Expert QT fiducials | PhysioNet |
| LUDB | 200 | Detailed P/QRS/T boundaries (12-lead) | PhysioNet |
| CSE Multilead | Variable | Reference measurements | User-provided WFDB |

---

## License

MIT
