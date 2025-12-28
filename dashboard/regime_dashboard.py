# File: dashboard/regime_dashboard.py
# Purpose: Regime analytics dashboard (read-only)
# Run with: streamlit run dashboard/regime_dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Trading Regime Analytics",
    layout="wide"
)

st.title("📊 Trading Regime Analytics Dashboard")

# =========================
# LOAD DATA
# =========================

DATA_PATH = Path("data/regime_analytics.csv")

if not DATA_PATH.exists():
    st.error("❌ regime_analytics.csv not found")
    st.stop()

df = pd.read_csv(DATA_PATH)

df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)

# =========================
# SIDEBAR FILTERS
# =========================

st.sidebar.header("Filters")

event_types = st.sidebar.multiselect(
    "Event Types",
    options=df["type"].unique(),
    default=df["type"].unique().tolist()
)

start_date = st.sidebar.date_input(
    "Start Date",
    value=df["timestamp"].min().date()
)

end_date = st.sidebar.date_input(
    "End Date",
    value=df["timestamp"].max().date()
)

mask = (
    df["type"].isin(event_types)
    & (df["timestamp"].dt.date >= start_date)
    & (df["timestamp"].dt.date <= end_date)
)

df = df[mask]

# =========================
# SUMMARY METRICS
# =========================

st.subheader("📌 Summary")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Events", len(df))

with col2:
    st.metric("Drift Events", (df["type"] == "DRIFT").sum())

with col3:
    st.metric("Risk Throttles", (df["type"] == "RISK_THROTTLE").sum())

with col4:
    st.metric("ML Gated OFF", ((df["type"] == "ML_GATE") & (df["ml_weight"] == 0)).sum())

# =========================
# DRIFT ANALYSIS
# =========================

st.subheader("📉 Drift Severity Over Time")

drift_df = df[df["type"] == "DRIFT"]

if not drift_df.empty:
    fig = px.line(
        drift_df,
        x="timestamp",
        y="severity",
        markers=True,
        title="Drift Severity"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No drift events in selected range")

# =========================
# RISK THROTTLING
# =========================

st.subheader("🛑 Risk Multiplier Timeline")

risk_df = df[df["type"] == "RISK_THROTTLE"]

if not risk_df.empty:
    fig = px.step(
        risk_df,
        x="timestamp",
        y="risk_multiplier",
        title="Risk Multiplier Changes"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No risk throttling events")

# =========================
# ML GATING
# =========================

st.subheader("🧠 ML Gating")

ml_df = df[df["type"] == "ML_GATE"]

if not ml_df.empty:
    fig = px.scatter(
        ml_df,
        x="timestamp",
        y="ml_weight",
        color="ml_weight",
        title="ML Weight Over Time",
        color_continuous_scale="RdYlGn"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No ML gating events")

# =========================
# TRADE PERFORMANCE BY REGIME
# =========================

st.subheader("💰 Trade Outcomes by Regime")

trade_df = df[df["type"] == "TRADE"]

if not trade_df.empty:
    trade_df["drift_active"] = trade_df["regime"].apply(
        lambda r: r.get("drift", {}).get("drift") if isinstance(r, dict) else False
    )

    fig = px.box(
        trade_df,
        x="drift_active",
        y="net_pnl",
        title="P&L Distribution (Drift vs Normal)",
        labels={"drift_active": "Drift Active"}
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No trade data")

# =========================
# RAW EVENT TABLE
# =========================

st.subheader("📄 Raw Regime Events")

st.dataframe(
    df.sort_values("timestamp", ascending=False),
    use_container_width=True,
    height=400
)
