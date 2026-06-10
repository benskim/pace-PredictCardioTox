"""Cardiac Safety Reliability Platform — Streamlit Application.

Product positioning: "Not only measuring QTc.
Determining whether QTc results can be trusted."

A reliability operations platform for cardiac safety assessment.

Run with: streamlit run app/validation_engine.py
"""

from __future__ import annotations

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from demo_data import (
    MeasurementRecord,
    generate_high_confidence_record,
    generate_low_confidence_record,
    generate_study_dataset,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Cardiac Safety Reliability Platform",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
    .block-container { padding-top: 0.5rem; }

    /* Hero banner */
    .platform-hero {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
        color: #ffffff;
        padding: 1.5rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
    }
    .platform-hero h1 {
        font-size: 1.6rem;
        margin: 0 0 0.25rem 0;
        font-weight: 800;
        letter-spacing: -0.02em;
    }
    .platform-hero .subtitle {
        font-size: 1rem;
        color: #a3bffa;
        margin-bottom: 0.5rem;
    }
    .platform-hero .tagline {
        font-size: 0.85rem;
        color: #8899aa;
        font-style: italic;
    }

    /* Confidence hero metric */
    .confidence-hero {
        text-align: center;
        padding: 2rem 1rem;
        border-radius: 16px;
        margin-bottom: 1rem;
    }
    .confidence-hero .score {
        font-size: 5rem;
        font-weight: 800;
        line-height: 1;
        margin-bottom: 0.25rem;
    }
    .confidence-hero .label {
        font-size: 1.4rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }

    /* Decision badge */
    .decision-badge {
        text-align: center;
        padding: 1.2rem;
        border-radius: 12px;
        font-size: 1.3rem;
        font-weight: 700;
    }

    /* QTc secondary card */
    .qtc-card {
        text-align: center;
        padding: 1.2rem;
        border-radius: 12px;
        background: #f8f9fa;
        border: 1px solid #e9ecef;
    }
    .qtc-card .value {
        font-size: 2rem;
        font-weight: 700;
        color: #495057;
    }
    .qtc-card .unit {
        font-size: 0.9rem;
        color: #868e96;
    }

    /* Driver bars */
    .driver-row {
        display: flex;
        align-items: center;
        margin-bottom: 0.5rem;
    }
    .driver-label {
        width: 160px;
        font-weight: 500;
        font-size: 0.9rem;
    }
    .driver-value {
        width: 40px;
        text-align: right;
        font-weight: 700;
        font-size: 0.9rem;
        margin-left: 0.5rem;
    }

    /* Breakdown table */
    .breakdown-row {
        display: flex;
        justify-content: space-between;
        padding: 0.4rem 0;
        border-bottom: 1px solid #f1f3f5;
    }
    .breakdown-row:last-child {
        border-bottom: none;
        font-weight: 700;
    }

    /* Comparison highlight */
    .comparison-highlight {
        background: #fff3cd;
        border: 2px solid #ffc107;
        border-radius: 12px;
        padding: 1rem;
        text-align: center;
        margin-top: 1rem;
    }

    /* Status indicators */
    .status-green { color: #2b8a3e; font-weight: 700; }
    .status-yellow { color: #e67700; font-weight: 700; }
    .status-red { color: #c92a2a; font-weight: 700; }

    /* Risk card */
    .risk-card {
        background: #f8f9fa;
        border-left: 4px solid #e67700;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
    }

    /* Insight card */
    .insight-card {
        background: #edf2ff;
        border-left: 4px solid #364fc7;
        padding: 0.8rem 1rem;
        margin-bottom: 0.5rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.9rem;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
</style>
""",
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------
def confidence_color(score: float) -> str:
    if score >= 85:
        return "#2b8a3e"
    if score >= 60:
        return "#e67700"
    return "#c92a2a"


def confidence_bg(score: float) -> str:
    if score >= 85:
        return "#d3f9d8"
    if score >= 60:
        return "#fff3bf"
    return "#ffe3e3"


def decision_color(decision: str) -> tuple[str, str]:
    if decision == "Auto Accept":
        return "#2b8a3e", "#d3f9d8"
    if decision == "Manual Review Recommended":
        return "#e67700", "#fff3bf"
    return "#c92a2a", "#ffe3e3"


def driver_color(value: float) -> str:
    if value >= 80:
        return "#2b8a3e"
    if value >= 60:
        return "#e67700"
    return "#c92a2a"


def render_platform_hero() -> None:
    st.markdown(
        """
        <div class="platform-hero">
            <h1>Cardiac Safety Reliability Platform</h1>
            <div class="subtitle">Quantifying Confidence in QTc Measurements</div>
            <div class="tagline">
                Not only measuring QTc. Determining whether QTc results can be trusted.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_confidence_hero(record: MeasurementRecord) -> None:
    color = confidence_color(record.confidence_score)
    bg = confidence_bg(record.confidence_score)
    tier_label = (
        "Trusted"
        if record.confidence_score >= 85
        else ("Review Required" if record.confidence_score >= 60 else "Low Confidence")
    )
    st.markdown(
        f"""
        <div class="confidence-hero" style="background:{bg}; border: 2px solid {color};">
            <div style="font-size:0.85rem; color:#555; font-weight:600; margin-bottom:0.5rem;">
                MEASUREMENT CONFIDENCE
            </div>
            <div class="score" style="color:{color};">{record.confidence_score:.0f}%</div>
            <div class="label" style="color:{color};">{tier_label}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_badge(record: MeasurementRecord) -> None:
    fg, bg = decision_color(record.decision)
    st.markdown(
        f"""
        <div class="decision-badge" style="background:{bg}; color:{fg}; border:2px solid {fg};">
            {record.decision}
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_qtc_card(record: MeasurementRecord) -> None:
    st.markdown(
        f"""
        <div class="qtc-card">
            <div style="font-size:0.8rem; color:#868e96; font-weight:600;">QTcF</div>
            <div class="value">{record.qtcf_ms:.0f} <span class="unit">ms</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_drivers(record: MeasurementRecord) -> None:
    drivers = [
        ("Signal Quality", record.signal_quality),
        ("Beat Consistency", record.beat_consistency),
        ("T-End Confidence", record.t_end_confidence),
        ("QT Stability", record.qt_stability),
        ("Noise Impact", record.noise_impact),
    ]
    for name, value in drivers:
        color = driver_color(value)
        pct = value / 100 * 100
        st.markdown(
            f"""
            <div class="driver-row">
                <span class="driver-label">{name}</span>
                <div style="flex:1; background:#f1f3f5; border-radius:4px; height:20px;">
                    <div style="width:{pct}%; background:{color}; height:100%; border-radius:4px;"></div>
                </div>
                <span class="driver-value" style="color:{color};">{value:.0f}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_breakdown(record: MeasurementRecord) -> None:
    rows = [
        ("Base Score", f"+{record.base_score:.0f}"),
        ("Noise Penalty", f"-{record.noise_penalty:.1f}"),
        ("Beat Variability Penalty", f"-{record.beat_variability_penalty:.1f}"),
        ("T-End Ambiguity Penalty", f"-{record.t_end_ambiguity_penalty:.1f}"),
        ("Formula Disagreement Penalty", f"-{record.formula_disagreement_penalty:.1f}"),
        ("Final Confidence", f"{record.confidence_score:.1f}"),
    ]
    for label, val in rows:
        weight = "font-weight:700;" if label == "Final Confidence" else ""
        st.markdown(
            f"""<div class="breakdown-row" style="{weight}">
                <span>{label}</span><span>{val}</span>
            </div>""",
            unsafe_allow_html=True,
        )


def render_explainability(record: MeasurementRecord) -> None:
    if record.confidence_score >= 85:
        header = "High confidence because:"
    elif record.confidence_score >= 60:
        header = "Moderate confidence because:"
    else:
        header = "Low confidence because:"

    st.markdown(f"**{header}**")
    for reason in record.reasons:
        st.markdown(f"- {reason}")


def _primary_driver(record: MeasurementRecord) -> str:
    drivers = {
        "T-End Ambiguity": record.t_end_ambiguity_penalty,
        "Signal Noise": record.noise_penalty,
        "Beat Variability": record.beat_variability_penalty,
        "Formula Disagreement": record.formula_disagreement_penalty,
    }
    return max(drivers, key=drivers.get)


# ---------------------------------------------------------------------------
# Hero banner (always visible)
# ---------------------------------------------------------------------------
render_platform_hero()

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.markdown(
    """
    <div style="text-align:center; margin-bottom:1rem;">
        <strong style="font-size:1.1rem;">Navigation</strong>
    </div>
    """,
    unsafe_allow_html=True,
)

page = st.sidebar.radio(
    "View",
    [
        "Reliability Overview",
        "Review Queue",
        "Measurement Validation",
        "ECG Comparison",
        "Reliability Analytics",
    ],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="font-size:0.7rem; color:#868e96; text-align:center;">
    <strong>Workflow</strong><br>
    Overview &rarr; Prioritization &rarr; Investigation<br>
    &rarr; Explanation &rarr; Population-Level Insight
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Generate study dataset (cached)
# ---------------------------------------------------------------------------
if "dataset" not in st.session_state:
    st.session_state.dataset = generate_study_dataset(n_records=200)

dataset = st.session_state.dataset
df = pd.DataFrame(
    [
        {
            "Record": r.record_id,
            "Subject": r.subject_id,
            "Visit": r.timepoint,
            "QTcF (ms)": r.qtcf_ms,
            "Confidence": r.confidence_score,
            "Decision": r.decision,
            "Signal Quality": r.signal_quality,
            "Beat Consistency": r.beat_consistency,
            "T-End Confidence": r.t_end_confidence,
            "Noise Impact": r.noise_impact,
            "QT Stability": r.qt_stability,
            "Primary Driver": _primary_driver(r),
        }
        for r in dataset
    ]
)

# Pre-compute study metrics
mean_confidence = df["Confidence"].mean()
trusted_rate = (df["Decision"] == "Auto Accept").mean() * 100
review_rate = (df["Decision"] == "Manual Review Recommended").mean() * 100
unreliable_rate = (df["Decision"] == "Measurement Unreliable").mean() * 100
review_count = int((df["Decision"] != "Auto Accept").sum())
unreliable_count = int((df["Decision"] == "Measurement Unreliable").sum())

# ---------------------------------------------------------------------------
# Page: Reliability Overview
# ---------------------------------------------------------------------------
if page == "Reliability Overview":
    st.markdown("## Reliability Overview")
    st.markdown(
        "<p style='color:#868e96;'>Executive-level reliability monitoring. "
        "Can we trust the ECG evidence supporting this study?</p>",
        unsafe_allow_html=True,
    )

    # KPI cards
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mean Confidence", f"{mean_confidence:.1f}%")
    col2.metric("Trusted ECG Rate", f"{trusted_rate:.1f}%")
    col3.metric("Review Required Rate", f"{review_rate:.1f}%")
    col4.metric("Unreliable ECG Rate", f"{unreliable_rate:.1f}%")

    st.markdown("---")

    # Reliability Health Summary + Study Status
    col_health, col_status = st.columns([2, 1])

    with col_health:
        st.markdown("#### Reliability Health Summary")
        if mean_confidence >= 80:
            st.markdown("Overall ECG evidence quality is **acceptable**.")
            st.markdown("Most measurements exceed reliability thresholds.")
        elif mean_confidence >= 65:
            st.markdown("Overall ECG evidence quality requires **attention**.")
            st.markdown("A meaningful proportion of measurements have reduced reliability.")
        else:
            st.markdown("Overall ECG evidence quality is **concerning**.")
            st.markdown("Many measurements fall below reliability thresholds.")

        st.markdown(f"**{unreliable_rate:.0f}%** of ECGs require review.")

    with col_status:
        st.markdown("#### Study Reliability Status")
        if mean_confidence >= 80 and unreliable_rate < 15:
            st.markdown(
                '<p class="status-green" style="font-size:2rem;">GREEN</p>', unsafe_allow_html=True
            )
            st.markdown("Evidence quality supports cardiac safety conclusions.")
        elif mean_confidence >= 65 and unreliable_rate < 25:
            st.markdown(
                '<p class="status-yellow" style="font-size:2rem;">YELLOW</p>',
                unsafe_allow_html=True,
            )
            st.markdown("Evidence quality acceptable with increased review burden.")
        else:
            st.markdown(
                '<p class="status-red" style="font-size:2rem;">RED</p>', unsafe_allow_html=True
            )
            st.markdown("Evidence quality insufficient for reliable conclusions.")

    st.markdown("---")

    # Top Reliability Risks
    st.markdown("#### Top Reliability Risks")

    driver_impact = (
        df.groupby("Primary Driver")
        .agg(
            count=("Record", "count"),
            mean_conf=("Confidence", "mean"),
        )
        .sort_values("count", ascending=False)
    )

    top_driver = driver_impact.index[0]
    top_driver_pct = driver_impact.iloc[0]["count"] / len(df) * 100

    noise_records = df[df["Noise Impact"] < 70]
    noise_pct = len(noise_records) / len(df) * 100

    low_conf_visits = df[df["Confidence"] < 60].groupby("Visit").size()
    concentrated_visit = low_conf_visits.idxmax() if len(low_conf_visits) > 0 else "N/A"

    st.markdown(
        f'<div class="risk-card"><strong>{top_driver}</strong> is the leading '
        f"reliability issue ({top_driver_pct:.0f}% of flagged ECGs).</div>",
        unsafe_allow_html=True,
    )
    if len(low_conf_visits) > 0:
        st.markdown(
            f'<div class="risk-card">Low-confidence ECGs are concentrated in '
            f"<strong>{concentrated_visit}</strong>.</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div class="risk-card">Signal noise contributes to '
        f"<strong>{noise_pct:.0f}%</strong> of confidence reduction.</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Page: Review Queue
# ---------------------------------------------------------------------------
elif page == "Review Queue":
    st.markdown("## Review Queue")
    st.markdown(
        "<p style='color:#868e96;'>What should I review first? "
        "Priority queue sorted by lowest confidence.</p>",
        unsafe_allow_html=True,
    )

    # Summary KPIs
    col1, col2, col3 = st.columns(3)
    col1.metric("Total ECGs", f"{len(df)}")
    col2.metric("Review Required", f"{review_count}")
    col3.metric("Unreliable ECGs", f"{unreliable_count}")

    st.markdown("---")

    # Filters
    st.markdown("#### Filters")
    filter_col1, filter_col2, filter_col3, filter_col4 = st.columns(4)

    with filter_col1:
        subjects = ["All"] + sorted(df["Subject"].unique().tolist())
        sel_subject = st.selectbox("Subject", subjects)
    with filter_col2:
        decisions = ["All", "Manual Review Recommended", "Measurement Unreliable"]
        sel_decision = st.selectbox("Decision", decisions)
    with filter_col3:
        drivers = ["All"] + sorted(df["Primary Driver"].unique().tolist())
        sel_driver = st.selectbox("Primary Driver", drivers)
    with filter_col4:
        conf_range = st.slider("Confidence Range", 0, 100, (0, 100))

    # Apply filters
    queue_df = df[df["Decision"] != "Auto Accept"].copy()
    if sel_subject != "All":
        queue_df = queue_df[queue_df["Subject"] == sel_subject]
    if sel_decision != "All":
        queue_df = queue_df[queue_df["Decision"] == sel_decision]
    if sel_driver != "All":
        queue_df = queue_df[queue_df["Primary Driver"] == sel_driver]
    queue_df = queue_df[
        (queue_df["Confidence"] >= conf_range[0]) & (queue_df["Confidence"] <= conf_range[1])
    ]

    # Sort by lowest confidence first
    queue_df = queue_df.sort_values("Confidence", ascending=True)

    st.markdown("---")
    st.markdown("#### Priority Queue")
    st.markdown(f"*Showing {len(queue_df)} ECGs requiring attention*")

    # Display table
    display_cols = ["Subject", "Visit", "QTcF (ms)", "Confidence", "Decision", "Primary Driver"]
    st.dataframe(
        queue_df[display_cols].reset_index(drop=True),
        use_container_width=True,
        height=400,
    )

    st.markdown("---")

    # Review Workload Summary
    st.markdown("#### Review Workload Summary")
    driver_workload = queue_df["Primary Driver"].value_counts()
    top_workload_driver = driver_workload.index[0] if len(driver_workload) > 0 else "N/A"

    st.markdown(f"**{len(queue_df)}** ECGs require review.")
    if len(driver_workload) > 0:
        st.markdown(
            f"Most review burden originates from **{top_workload_driver}** "
            f"({driver_workload.iloc[0]} ECGs)."
        )

# ---------------------------------------------------------------------------
# Page: Measurement Validation
# ---------------------------------------------------------------------------
elif page == "Measurement Validation":
    st.markdown("## Measurement Validation")
    st.markdown(
        "<p style='color:#868e96;'>Why is this ECG reliable or unreliable? "
        "Detailed investigation screen.</p>",
        unsafe_allow_html=True,
    )

    # Demo selector
    demo_mode = st.selectbox(
        "Demo Scenario",
        ["High Confidence (Auto Accept)", "Low Confidence (Review Required)"],
        label_visibility="collapsed",
    )

    if "High" in demo_mode:
        record = generate_high_confidence_record()
    else:
        record = generate_low_confidence_record()

    # Primary layout: 3 columns
    col_conf, col_decision, col_qtc = st.columns([2, 1.5, 1])

    with col_conf:
        render_confidence_hero(record)

    with col_decision:
        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
        render_decision_badge(record)
        st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="qtc-card" style="margin-top:0.5rem;">
                <div style="font-size:0.75rem; color:#868e96;">Record</div>
                <div style="font-weight:600;">{record.record_id}</div>
                <div style="font-size:0.75rem; color:#868e96;">
                    {record.subject_id} | {record.timepoint}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_qtc:
        st.markdown("<div style='height:1rem;'></div>", unsafe_allow_html=True)
        render_qtc_card(record)
        st.markdown(
            f"""
            <div class="qtc-card" style="margin-top:0.5rem;">
                <div style="font-size:0.8rem; color:#868e96; font-weight:600;">HR</div>
                <div class="value" style="font-size:1.5rem;">
                    {record.hr_bpm:.0f} <span class="unit">bpm</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Confidence Drivers + Breakdown + Explainability
    col_drivers, col_breakdown, col_explain = st.columns([1.2, 1, 1])

    with col_drivers:
        st.markdown("#### Confidence Drivers")
        render_drivers(record)

    with col_breakdown:
        st.markdown("#### Score Decomposition")
        render_breakdown(record)

    with col_explain:
        st.markdown("#### Explanation")
        render_explainability(record)

    st.markdown("---")

    # Reliability Context
    st.markdown("#### Reliability Context")
    ctx_col1, ctx_col2, ctx_col3 = st.columns(3)

    with ctx_col1:
        st.metric("This ECG Confidence", f"{record.confidence_score:.0f}%")
    with ctx_col2:
        st.metric("Study Average", f"{mean_confidence:.0f}%")
    with ctx_col3:
        percentile = (df["Confidence"] < record.confidence_score).mean() * 100
        if percentile >= 90:
            ctx_label = f"Top {100 - percentile:.0f}% Reliability"
        elif percentile >= 50:
            ctx_label = f"Above Median ({percentile:.0f}th percentile)"
        else:
            ctx_label = f"Below Median ({percentile:.0f}th percentile)"
        st.metric("Study Rank", ctx_label)

# ---------------------------------------------------------------------------
# Page: ECG Comparison
# ---------------------------------------------------------------------------
elif page == "ECG Comparison":
    st.markdown("## ECG Comparison")
    st.markdown(
        "<p style='color:#868e96;'>Why do similar QTc values have different reliability?</p>",
        unsafe_allow_html=True,
    )

    record_a = generate_high_confidence_record(record_id="ECG-A-001", qtcf_ms=451.0)
    record_b = generate_low_confidence_record(record_id="ECG-B-001", qtcf_ms=452.0)

    # Highlight
    st.markdown(
        """
        <div class="comparison-highlight">
            <strong>Nearly identical QTc values. Completely different reliability.</strong><br>
            <span style="color:#555;">
                This is why measurement confidence matters more than the measurement itself.
            </span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### ECG A")
        render_confidence_hero(record_a)
        render_qtc_card(record_a)
        st.markdown("")
        render_decision_badge(record_a)

    with col_b:
        st.markdown("### ECG B")
        render_confidence_hero(record_b)
        render_qtc_card(record_b)
        st.markdown("")
        render_decision_badge(record_b)

    st.markdown("---")

    # Reliability Drivers Comparison
    st.markdown("#### Reliability Drivers Comparison")

    comparison_data = {
        "Driver": [
            "Signal Quality",
            "Noise Impact",
            "Beat Consistency",
            "T-End Confidence",
            "QT Stability",
        ],
        "ECG A": [
            record_a.signal_quality,
            record_a.noise_impact,
            record_a.beat_consistency,
            record_a.t_end_confidence,
            record_a.qt_stability,
        ],
        "ECG B": [
            record_b.signal_quality,
            record_b.noise_impact,
            record_b.beat_consistency,
            record_b.t_end_confidence,
            record_b.qt_stability,
        ],
    }
    comparison_df = pd.DataFrame(comparison_data)

    fig_comp = go.Figure()
    fig_comp.add_trace(
        go.Bar(
            name="ECG A (Trusted)",
            x=comparison_df["Driver"],
            y=comparison_df["ECG A"],
            marker_color="#2b8a3e",
        )
    )
    fig_comp.add_trace(
        go.Bar(
            name="ECG B (Unreliable)",
            x=comparison_df["Driver"],
            y=comparison_df["ECG B"],
            marker_color="#c92a2a",
        )
    )
    fig_comp.update_layout(
        barmode="group",
        height=300,
        margin=dict(t=20, b=40, l=40, r=20),
        yaxis_title="Score (0-100)",
    )
    st.plotly_chart(fig_comp, use_container_width=True)

    st.markdown("---")

    # Operational Impact
    st.markdown("#### Operational Impact")
    st.markdown(
        '<div class="risk-card"><strong>ECG B requires manual review</strong> — '
        "confidence below acceptable threshold.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="risk-card"><strong>ECG B increases review workload</strong> — '
        "adds to queue of ECGs requiring expert assessment.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="risk-card"><strong>ECG B introduces uncertainty</strong> into '
        "cardiac safety assessment — QTcF 452 ms cannot be trusted without review.</div>",
        unsafe_allow_html=True,
    )

# ---------------------------------------------------------------------------
# Page: Reliability Analytics
# ---------------------------------------------------------------------------
elif page == "Reliability Analytics":
    st.markdown("## Reliability Analytics")
    st.markdown(
        "<p style='color:#868e96;'>Study-level reliability intelligence. "
        "How does measurement reliability affect the study?</p>",
        unsafe_allow_html=True,
    )

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Mean Confidence", f"{mean_confidence:.1f}%")
    col2.metric("Trusted ECG Rate", f"{trusted_rate:.1f}%")
    col3.metric("Review Required Rate", f"{review_rate:.1f}%")
    col4.metric("Unreliable Rate", f"{unreliable_rate:.1f}%")

    st.markdown("---")

    # Reliability Intelligence
    st.markdown("#### Reliability Intelligence")

    # Auto-generated insights
    driver_counts = df["Primary Driver"].value_counts()
    top_driver_name = driver_counts.index[0]
    top_driver_pct = driver_counts.iloc[0] / len(df) * 100

    low_conf_df = df[df["Confidence"] < 60]
    low_conf_visits = low_conf_df.groupby("Visit").size()
    increase_visit = ""
    if len(low_conf_visits) > 1:
        increase_visit = low_conf_visits.idxmax()

    avg_signal_quality = df["Signal Quality"].mean()

    st.markdown(
        f'<div class="insight-card"><strong>{top_driver_name}</strong> accounts for '
        f"<strong>{top_driver_pct:.0f}%</strong> of confidence reduction.</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        f'<div class="insight-card"><strong>{unreliable_rate:.0f}%</strong> of ECGs fall '
        "below acceptable reliability thresholds.</div>",
        unsafe_allow_html=True,
    )
    if increase_visit:
        st.markdown(
            f'<div class="insight-card">Low-confidence ECGs increased after '
            f"<strong>{increase_visit}</strong>.</div>",
            unsafe_allow_html=True,
        )
    st.markdown(
        f'<div class="insight-card">Signal quality remains '
        f"{'stable' if avg_signal_quality >= 70 else 'variable'} across most measurements "
        f"(mean: {avg_signal_quality:.0f}).</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")

    # Charts
    chart_col1, chart_col2 = st.columns(2)

    with chart_col1:
        st.markdown("#### Confidence Distribution")
        fig_hist = px.histogram(
            df,
            x="Confidence",
            nbins=25,
            color_discrete_sequence=["#364fc7"],
            labels={"Confidence": "Measurement Confidence (%)"},
        )
        fig_hist.add_vline(
            x=85, line_dash="dash", line_color="#2b8a3e", annotation_text="Auto Accept Threshold"
        )
        fig_hist.add_vline(
            x=60, line_dash="dash", line_color="#e67700", annotation_text="Review Threshold"
        )
        fig_hist.update_layout(showlegend=False, margin=dict(t=20, b=40, l=40, r=20), height=300)
        st.plotly_chart(fig_hist, use_container_width=True)

    with chart_col2:
        st.markdown("#### Decision Distribution")
        decision_counts = df["Decision"].value_counts().reset_index()
        decision_counts.columns = ["Decision", "Count"]
        color_map = {
            "Auto Accept": "#2b8a3e",
            "Manual Review Recommended": "#e67700",
            "Measurement Unreliable": "#c92a2a",
        }
        fig_pie = px.pie(
            decision_counts,
            values="Count",
            names="Decision",
            color="Decision",
            color_discrete_map=color_map,
        )
        fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
        st.plotly_chart(fig_pie, use_container_width=True)

    st.markdown("---")

    # Reliability Driver Ranking
    st.markdown("#### Reliability Driver Ranking")
    st.markdown("*Contributors to confidence reduction, ranked by frequency:*")

    driver_ranking = driver_counts.reset_index()
    driver_ranking.columns = ["Driver", "ECGs Affected"]
    driver_ranking["% of Total"] = (driver_ranking["ECGs Affected"] / len(df) * 100).round(1)
    driver_ranking.index = range(1, len(driver_ranking) + 1)
    st.dataframe(driver_ranking, use_container_width=True)

    st.markdown("---")

    # More distribution charts
    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.markdown("#### Signal Quality Distribution")
        fig_sq = px.histogram(df, x="Signal Quality", nbins=20, color_discrete_sequence=["#5c7cfa"])
        fig_sq.update_layout(showlegend=False, margin=dict(t=20, b=40, l=40, r=20), height=280)
        st.plotly_chart(fig_sq, use_container_width=True)

    with chart_col4:
        st.markdown("#### T-End Confidence Distribution")
        fig_te = px.histogram(
            df, x="T-End Confidence", nbins=20, color_discrete_sequence=["#845ef7"]
        )
        fig_te.update_layout(showlegend=False, margin=dict(t=20, b=40, l=40, r=20), height=280)
        st.plotly_chart(fig_te, use_container_width=True)

    # Confidence trend
    st.markdown("---")
    st.markdown("#### Confidence Trend Over Time")
    timepoint_order = [
        "Screening",
        "Day -1 Pre-dose",
        "Day 1 Pre-dose",
        "Day 1 1h Post",
        "Day 1 2h Post",
        "Day 1 4h Post",
        "Day 1 8h Post",
        "Day 1 12h Post",
        "Day 7 Pre-dose",
        "Day 7 2h Post",
    ]
    df_trend = df.copy()
    df_trend["Visit"] = pd.Categorical(df_trend["Visit"], categories=timepoint_order, ordered=True)
    trend_df = (
        df_trend.groupby("Visit", observed=True)["Confidence"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    trend_df.columns = ["Visit", "Mean Confidence", "SD", "N"]

    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=trend_df["Visit"],
            y=trend_df["Mean Confidence"],
            mode="lines+markers",
            line=dict(color="#364fc7", width=2),
            marker=dict(size=8),
            name="Mean Confidence",
        )
    )
    fig_trend.add_hline(y=85, line_dash="dash", line_color="#2b8a3e")
    fig_trend.add_hline(y=60, line_dash="dash", line_color="#e67700")
    fig_trend.update_layout(
        yaxis_title="Mean Confidence (%)",
        xaxis_title="",
        margin=dict(t=20, b=60, l=40, r=20),
        height=320,
        showlegend=False,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # Study Impact Assessment
    st.markdown("#### Study Impact Assessment")
    if mean_confidence >= 80:
        st.markdown(
            '<div class="insight-card">ECG evidence reliability remains '
            "<strong>acceptable</strong>. Cardiac safety conclusions are supported.</div>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="insight-card">ECG evidence reliability requires '
            "<strong>attention</strong>. Some conclusions may need additional support.</div>",
            unsafe_allow_html=True,
        )

    if review_rate > 25:
        st.markdown(
            '<div class="risk-card">Review burden is <strong>increasing</strong> — '
            f"{review_rate:.0f}% of ECGs require manual assessment.</div>",
            unsafe_allow_html=True,
        )

    if increase_visit:
        st.markdown(
            f'<div class="risk-card">Specific visit windows require additional attention: '
            f"<strong>{increase_visit}</strong>.</div>",
            unsafe_allow_html=True,
        )

    # Study metrics table
    st.markdown("---")
    st.markdown("#### Study-Level Reliability Metrics")
    metrics_data = {
        "Metric": [
            "Total Measurements",
            "Mean Confidence Score",
            "Median Confidence Score",
            "Trusted ECG Rate",
            "Manual Review Rate",
            "Unreliable Rate",
            "Mean Signal Quality",
            "Mean Beat Consistency",
            "Mean T-End Confidence",
        ],
        "Value": [
            f"{len(df)}",
            f"{mean_confidence:.1f}%",
            f"{df['Confidence'].median():.1f}%",
            f"{trusted_rate:.1f}%",
            f"{review_rate:.1f}%",
            f"{unreliable_rate:.1f}%",
            f"{df['Signal Quality'].mean():.1f}",
            f"{df['Beat Consistency'].mean():.1f}",
            f"{df['T-End Confidence'].mean():.1f}",
        ],
    }
    st.dataframe(pd.DataFrame(metrics_data), hide_index=True, use_container_width=True)
