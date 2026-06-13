# Decision Model Specification — QTc Confidence Engine

## Overview

The Decision Model translates a **Measurement Confidence Score** (0–100) into
an actionable clinical disposition for each ECG record. It defines:

1. Decision tiers and thresholds
2. Review queue prioritisation logic
3. Study-level reliability status
4. Regulatory alignment notes

---

## 1. Record-Level Decision Tiers

Every ECG record receives exactly one of three decisions based on the composite confidence score.

### Library Model (`ConfidenceResult.tier`)

| Tier string | Score range | Meaning |
|-------------|-------------|---------|
| `"high"` | ≥ 90 | High confidence; may proceed without review |
| `"review"` | 70 – 89 | Moderate confidence; review recommended |
| `"manual_review"` | < 70 | Low confidence; manual review required |

### App / Demo Model (`MeasurementRecord.decision`)

The Streamlit demo uses a slightly different threshold set to produce more
operationally interesting distributions on the 200-record synthetic dataset:

| Decision string | Score range | Action |
|-----------------|-------------|--------|
| `"Auto Accept"` | ≥ 85 | Accepted automatically; no review needed |
| `"Manual Review Recommended"` | 60 – 84 | Queued for analyst review |
| `"Measurement Unreliable"` | < 60 | Flagged as untrustworthy; excluded or escalated |

> **Implementation note:** The library model (90/70 thresholds) is the
> research-grade standard. The demo model (85/60) is tuned for visual
> clarity in the interactive dashboard. Future production deployments
> should adopt the library thresholds and calibrate on real data.

---

## 2. Confidence Score Formula

```
Confidence = Σ (sub_score_i × weight_i)  /  Σ weight_i
           = clamp([0, 100])
```

### Default Weights

| Sub-score | Weight | Rationale |
|-----------|--------|-----------|
| `beat_stability` | 0.25 | Most direct indicator of measurement reproducibility |
| `tend_stability` | 0.25 | T-end ambiguity is the dominant QTc error source |
| `signal_quality` | 0.20 | Noise drives all downstream uncertainty |
| `formula_agreement` | 0.15 | Correction formula spread indicates HR instability |
| `morphology` | 0.15 | T-wave shape risk affects delineation reliability |

Weights must sum to 1.0. Custom weights may be passed as `weights: dict` to
`measurement_confidence()`.

---

## 3. Demo Penalty Decomposition

The app uses an additive-penalty form for interpretability:

```
Confidence = Base Score (100)
           − Noise Penalty         [0–35]
           − Beat Variability Penalty  [0–22]
           − T-End Ambiguity Penalty   [0–18]
           − Formula Disagreement Penalty [0–12]
```

Penalty ranges for each decision tier:

| Decision | Noise | Beat Var. | T-End Amb. | Formula Disagr. | Typical Total |
|----------|-------|-----------|------------|-----------------|---------------|
| Auto Accept (≥85) | 1–6 | 0.5–3 | 0.5–2.5 | 0–2 | 2–14 |
| Manual Review (60–84) | 6–15 | 3–10 | 2–8 | 1–6 | 12–39 |
| Unreliable (<60) | 20–35 | 12–22 | 8–18 | 5–12 | 45–87 |

---

## 4. Review Queue Prioritisation

ECGs requiring human attention are sorted by **ascending confidence score** (lowest confidence first), ensuring the most uncertain measurements receive first review.

**Filtering dimensions available in the queue:**
- Subject ID
- Decision tier (`Manual Review Recommended` / `Measurement Unreliable`)
- Primary driver (the penalty with largest contribution)
- Confidence range (slider, 0–100)

**Primary driver** is the sub-score penalty with the highest absolute value:

```python
primary_driver = argmax({
    "T-End Ambiguity":      t_end_ambiguity_penalty,
    "Signal Noise":         noise_penalty,
    "Beat Variability":     beat_variability_penalty,
    "Formula Disagreement": formula_disagreement_penalty,
})
```

---

## 5. Study-Level Reliability Status

Computed across all records in a study cohort:

| Metric | Definition |
|--------|-----------|
| `mean_confidence` | Mean confidence score across all records |
| `trusted_rate` | Fraction with decision = `"Auto Accept"` |
| `review_rate` | Fraction with decision = `"Manual Review Recommended"` |
| `unreliable_rate` | Fraction with decision = `"Measurement Unreliable"` |
| `review_count` | Count of records not Auto Accepted |

**Status colours (study-level):**

| Status | Condition | Interpretation |
|--------|-----------|----------------|
| GREEN | `mean_confidence ≥ 80` AND `unreliable_rate < 15%` | Evidence quality supports cardiac safety conclusions |
| YELLOW | `mean_confidence ≥ 65` AND `unreliable_rate < 25%` | Acceptable quality with increased review burden |
| RED | Otherwise | Evidence quality insufficient for reliable conclusions |

---

## 6. Regulatory Alignment

### ICH E14 Relevance
- ΔQTcF > 10 ms triggers regulatory attention; confidence score flags uncertain measurements before they affect the delta calculation.
- ΔQTcF > 20 ms is a formal safety concern threshold; any unreliable ECG contributing to this delta should be excluded or re-measured.

### Acceptable Error Budgets (clinical norms)

| Metric | Acceptable | Excellent |
|--------|------------|-----------|
| Bland–Altman Bias | < 5 ms | < 2 ms |
| LoA width | < 20 ms | < 10 ms |
| Coverage ±10 ms | > 85% | > 95% |

---

## 7. Decision Flow Diagram

```
ECG Signal
    │
    ▼
Signal Quality Assessment ──────► signal_quality sub-score
    │
    ▼
Wave Delineation (U-Net)
    │
    ▼
Multi-Method T-End Agreement ───► tend_stability sub-score
    │                         ──► formula_agreement sub-score
    ▼
Beat Selection & QT Measurement
    │
    ▼
Beat Stability Analysis ────────► beat_stability sub-score
    │
    ▼
T-Wave Morphology Classification ► morphology sub-score
    │
    ▼
Weighted Composite Score
    │
    ├─ ≥ 90 (≥ 85 demo) ──► "Auto Accept"
    ├─ 70–89 (60–84 demo) ─► "Manual Review Recommended"
    └─ < 70 (< 60 demo) ───► "Measurement Unreliable"
```
