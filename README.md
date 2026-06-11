# QTc Confidence Engine

> **Not only measuring QTc. Determining whether QTc results can be trusted.**

Reliable QT/QTc Measurement for Cardiac Safety Assessment.
 
Designed to identify which ECG measurements can be trusted,
which require expert review, and why.

## Why This Exists
Most cardiac toxicity AI systems attempt to predict toxicity from molecular structures before clinical trials. This project addresses a different problem. Once a drug enters clinical development, regulatory decisions depend on ECG evidence collected from real human subjects. The critical question becomes:

Can the ECG evidence itself be trusted?

The QTc Confidence Engine quantifies measurement reliability and identifies ECGs requiring expert review.

## Current Scope:
Current development focuses on a research-grade QTc Confidence Engine.

In Scope:
- Signal quality assessment
- T-end confidence
- Reliability scoring
- Explainability
- Review prioritization

Out of Scope:
- Molecular toxicity prediction
- TdP prediction
- Clinical trial outcome prediction
- FDA approval prediction

---
## Clinical Context

In clinical cardiac safety studies, regulatory decisions may depend on QTc changes of only a few milliseconds. Measurement uncertainty can directly affect the interpretation of cardiac safety signals in clinical studies. Noise contamination, T-wave morphology changes, delineation ambiguity, and measurement variability can introduce uncertainty large enough to affect cardiac safety conclusions.
The objective of the QTc Confidence Engine is to quantify that uncertainty rather than hide it.

## Product Vision

| Competitors show | This platform shows |
|------------------|---------------------|
| QTc Value | QTc **Reliability** |
| "What is the QTc?" | "Can this QTc be **trusted**?" |

**Reliability is the product. Confidence is evidence. QTc is only the measurement.**

---

## Demo Application

The interactive demo is a Streamlit application with five views:

### 1. Reliability Overview (Landing Page)

Executive-level reliability monitoring:
- **KPI cards** — Mean Confidence, Trusted ECG Rate, Review Rate, Unreliable Rate
- **Reliability Health Summary** — plain-language study quality assessment
- **Top Reliability Risks** — auto-detected issues driving confidence reduction
- **Study Reliability Status** — Green / Yellow / Red with explanation

### 2. Review Queue

The most operationally valuable screen:
- **Priority queue** — sorted by lowest confidence first
- **Filters** — Subject, Decision, Primary Driver, Confidence Range
- **Review Workload Summary** — quantified review burden

### 3. Measurement Validation

Detailed investigation screen:
- **Confidence Score** — dominant visual element (0–100%)
- **Decision** — Auto Accept / Manual Review / Measurement Unreliable
- **Confidence Drivers** — Signal Quality, Beat Consistency, T-End Confidence, QT Stability, Noise Impact
- **Score Decomposition** — transparent penalty breakdown
- **Explanation** — plain-language reasons
- **Reliability Context** — this ECG vs. study average and percentile

### 4. ECG Comparison

The "aha" moment:
- Two ECGs with **nearly identical QTc** but **completely different reliability**
- **Reliability Drivers Comparison** — grouped bar chart
- **Operational Impact** — consequences for review workflow

### 5. Reliability Analytics

Study-level reliability intelligence:
- **Auto-generated insights** — top drivers, threshold violations, trends
- **Reliability Driver Ranking** — contributors to confidence reduction
- **Distribution charts** — confidence, signal quality, T-end confidence
- **Confidence Trend Over Time** — with threshold lines
- **Study Impact Assessment** — operational consequences
- **Study-Level Reliability Metrics** — 9-row summary table

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
├── tests/                     # Unit tests (162+)
├── scripts/                   # Helper scripts
└── pyproject.toml
```

---

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Run reliability platform demo
streamlit run app/validation_engine.py

# Run tests
pytest --cov=ecg_analytics --cov-report=term-missing tests/
```

---

## License

MIT
