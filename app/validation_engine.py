"""QTc Measurement Validation Engine — Streamlit Application.

Product positioning: "We do not only calculate QTc.
We quantify whether a QTc result should be trusted."

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
    page_title="QTc Measurement Validation Engine",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — Confidence is the hero, not QTc
# ---------------------------------------------------------------------------
st.markdown(
    """
<style>
    /* Remove default padding */
    .block-container { padding-top: 1rem; }

    /* Hero confidence metric */
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
        return "#2b8a3e"  # green
    if score >= 60:
        return "#e67700"  # amber
    return "#c92a2a"  # red


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
        ("Noise Impact", record.noise_impact),
        ("QT Stability", record.qt_stability),
    ]
    for name, value in drivers:
        color = driver_color(value)
        pct = value / 100 * 100
        st.markdown(
            f"""
            <div class="driver-row">
                <span class="driver-label">{name}</span>
                <div style="flex:1; background:#f1f3f5; border-radius:4px; height:20px; position:relative;">
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
        icon = ""
    elif record.confidence_score >= 60:
        header = "Moderate confidence because:"
        icon = ""
    else:
        header = "Low confidence because:"
        icon = ""

    st.markdown(f"**{icon} {header}**")
    for reason in record.reasons:
        st.markdown(f"- {reason}")


# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
st.sidebar.title("QTc Validation Engine")
st.sidebar.markdown("---")
page = st.sidebar.radio(
    "View",
    [
        "Measurement Validation",
        "Side-by-Side Comparison",
        "Research Analytics",
    ],
    label_visibility="collapsed",
)

st.sidebar.markdown("---")
st.sidebar.markdown(
    """
    <div style="font-size:0.75rem; color:#868e96; text-align:center;">
    <strong>Product Philosophy</strong><br>
    We do not only calculate QTc.<br>
    We quantify whether a QTc result<br>
    should be trusted.
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Page: Measurement Validation (Primary)
# ---------------------------------------------------------------------------
if page == "Measurement Validation":
    st.markdown(
        "<h2 style='margin-bottom:0.25rem;'>Measurement Validation</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#868e96; margin-top:0;'>Single-record reliability assessment</p>",
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
                <div style="font-size:0.75rem; color:#868e96;">{record.subject_id} | {record.timepoint}</div>
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
                <div class="value" style="font-size:1.5rem;">{record.hr_bpm:.0f} <span class="unit">bpm</span></div>
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

# ---------------------------------------------------------------------------
# Page: Side-by-Side Comparison
# ---------------------------------------------------------------------------
elif page == "Side-by-Side Comparison":
    st.markdown(
        "<h2 style='margin-bottom:0.25rem;'>Reliability Comparison</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#868e96; margin-top:0;'>"
        "Same QTc value. Completely different reliability.</p>",
        unsafe_allow_html=True,
    )

    record_a = generate_high_confidence_record(record_id="ECG-A-001", qtcf_ms=451.0)
    record_b = generate_low_confidence_record(record_id="ECG-B-001", qtcf_ms=452.0)

    # The "aha" moment highlight
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
        st.markdown("---")
        st.markdown("**Confidence Drivers**")
        render_drivers(record_a)
        st.markdown("---")
        st.markdown("**Score Decomposition**")
        render_breakdown(record_a)
        st.markdown("---")
        render_explainability(record_a)

    with col_b:
        st.markdown("### ECG B")
        render_confidence_hero(record_b)
        render_qtc_card(record_b)
        st.markdown("")
        render_decision_badge(record_b)
        st.markdown("---")
        st.markdown("**Confidence Drivers**")
        render_drivers(record_b)
        st.markdown("---")
        st.markdown("**Score Decomposition**")
        render_breakdown(record_b)
        st.markdown("---")
        render_explainability(record_b)

# ---------------------------------------------------------------------------
# Page: Research Analytics
# ---------------------------------------------------------------------------
elif page == "Research Analytics":
    st.markdown(
        "<h2 style='margin-bottom:0.25rem;'>Research Analytics</h2>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<p style='color:#868e96; margin-top:0;'>Study-level measurement reliability metrics</p>",
        unsafe_allow_html=True,
    )

    # Generate study dataset
    dataset = generate_study_dataset(n_records=200)
    df = pd.DataFrame(
        [
            {
                "Record": r.record_id,
                "Subject": r.subject_id,
                "Timepoint": r.timepoint,
                "QTcF (ms)": r.qtcf_ms,
                "Confidence": r.confidence_score,
                "Decision": r.decision,
                "Signal Quality": r.signal_quality,
                "Beat Consistency": r.beat_consistency,
                "T-End Confidence": r.t_end_confidence,
                "Noise Impact": r.noise_impact,
                "QT Stability": r.qt_stability,
            }
            for r in dataset
        ]
    )

    # KPI row
    col1, col2, col3, col4 = st.columns(4)
    auto_accept_rate = (df["Decision"] == "Auto Accept").mean() * 100
    review_rate = (df["Decision"] == "Manual Review Recommended").mean() * 100
    unreliable_rate = (df["Decision"] == "Measurement Unreliable").mean() * 100
    mean_confidence = df["Confidence"].mean()

    col1.metric("Mean Confidence", f"{mean_confidence:.1f}%")
    col2.metric("Auto Accept Rate", f"{auto_accept_rate:.1f}%")
    col3.metric("Review Required Rate", f"{review_rate:.1f}%")
    col4.metric("Unreliable Rate", f"{unreliable_rate:.1f}%")

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
        fig_hist.update_layout(
            showlegend=False,
            margin=dict(t=20, b=40, l=40, r=20),
            height=300,
        )
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
        fig_pie.update_layout(
            margin=dict(t=20, b=20, l=20, r=20),
            height=300,
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    chart_col3, chart_col4 = st.columns(2)

    with chart_col3:
        st.markdown("#### Signal Quality Distribution")
        fig_sq = px.histogram(
            df,
            x="Signal Quality",
            nbins=20,
            color_discrete_sequence=["#5c7cfa"],
        )
        fig_sq.update_layout(
            showlegend=False,
            margin=dict(t=20, b=40, l=40, r=20),
            height=280,
        )
        st.plotly_chart(fig_sq, use_container_width=True)

    with chart_col4:
        st.markdown("#### T-End Confidence Distribution")
        fig_te = px.histogram(
            df,
            x="T-End Confidence",
            nbins=20,
            color_discrete_sequence=["#845ef7"],
        )
        fig_te.update_layout(
            showlegend=False,
            margin=dict(t=20, b=40, l=40, r=20),
            height=280,
        )
        st.plotly_chart(fig_te, use_container_width=True)

    chart_col5, chart_col6 = st.columns(2)

    with chart_col5:
        st.markdown("#### Noise Impact Distribution")
        fig_ni = px.histogram(
            df,
            x="Noise Impact",
            nbins=20,
            color_discrete_sequence=["#f06595"],
        )
        fig_ni.update_layout(
            showlegend=False,
            margin=dict(t=20, b=40, l=40, r=20),
            height=280,
        )
        st.plotly_chart(fig_ni, use_container_width=True)

    with chart_col6:
        st.markdown("#### Confidence vs QTcF")
        fig_scatter = px.scatter(
            df,
            x="QTcF (ms)",
            y="Confidence",
            color="Decision",
            color_discrete_map=color_map,
            opacity=0.7,
        )
        fig_scatter.update_layout(
            margin=dict(t=20, b=40, l=40, r=20),
            height=280,
        )
        st.plotly_chart(fig_scatter, use_container_width=True)

    st.markdown("---")

    # Confidence trend by timepoint
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
    df["Timepoint"] = pd.Categorical(df["Timepoint"], categories=timepoint_order, ordered=True)
    trend_df = (
        df.groupby("Timepoint", observed=True)["Confidence"]
        .agg(["mean", "std", "count"])
        .reset_index()
    )
    trend_df.columns = ["Timepoint", "Mean Confidence", "SD", "N"]

    fig_trend = go.Figure()
    fig_trend.add_trace(
        go.Scatter(
            x=trend_df["Timepoint"],
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

    # Study-level metrics summary table
    st.markdown("#### Study-Level Reliability Metrics")
    metrics_data = {
        "Metric": [
            "Total Measurements",
            "Mean Confidence Score",
            "Median Confidence Score",
            "Auto Accept Rate",
            "Manual Review Rate",
            "Unreliable Rate",
            "Mean Signal Quality",
            "Mean Beat Consistency",
            "Mean T-End Confidence",
        ],
        "Value": [
            f"{len(df)}",
            f"{df['Confidence'].mean():.1f}%",
            f"{df['Confidence'].median():.1f}%",
            f"{auto_accept_rate:.1f}%",
            f"{review_rate:.1f}%",
            f"{unreliable_rate:.1f}%",
            f"{df['Signal Quality'].mean():.1f}",
            f"{df['Beat Consistency'].mean():.1f}",
            f"{df['T-End Confidence'].mean():.1f}",
        ],
    }
    st.dataframe(pd.DataFrame(metrics_data), hide_index=True, use_container_width=True)
