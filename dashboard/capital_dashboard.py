# File: dashboard/capital_dashboard.py
# Purpose: Live capital & equity dashboard
# Run: streamlit run dashboard/capital_dashboard.py

import streamlit as st
import pandas as pd
import plotly.express as px
from pathlib import Path

st.set_page_config(
    page_title="Live Capital Dashboard",
    layout="wide"
)

# Auto refresh every 5 seconds
st.experimental_autorefresh(interval=5000)

st.title("💼 Live Capital & Risk Dashboard")

DATA_DIR = Path("data")

trade_file = DATA_DIR / "tradehistory.csv"
regime_file = DATA_DIR / "regime_analytics.csv"
portfolio_file = DATA_DIR / "portfolio_snapshots.csv"

# =====================
# LOAD DATA
# =====================

def safe_load_csv(path):
    if path.exists():
        df = pd.read_csv(path)
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
        return df
    return pd.DataFrame()

trades = safe_load_csv(trade_file)
regimes = safe_load_csv(regime_file)
portfolio = safe_load_csv(portfolio_file)

# =====================
# METRICS
# =====================

st.subheader("📊 Current Stats")

col1, col2, col3, col4 = st.columns(4)

if not portfolio.empty:
    latest = portfolio.sort_values("timestamp").iloc[-1]
    equity = latest["equity"]
    cash = latest["cash"]
    drawdown = latest["drawdown_pct"]
    risk_mult = latest["risk_multiplier"]
else:
    equity = cash = drawdown = risk_mult = 0

with col1:
    st.metric("Equity", f"${equity:,.2f}")

with col2:
    st.metric("Cash", f"${cash:,.2f}")

with col3:
    st.metric("Drawdown", f"{drawdown:.2f}%")

with col4:
    st.metric("Risk Multiplier", f"x{risk_mult:.2f}")

# =====================
# EQUITY CURVE
# =====================

st.subheader("📈 Equity Curve")

if not portfolio.empty:
    fig = px.line(
        portfolio,
        x="timestamp",
        y="equity",
        title="Equity Over Time"
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No portfolio data yet")

# =====================
# DRAWDOWN
# =====================

st.subheader("📉 Drawdown")

if not portfolio.empty:
    fig = px.area(
        portfolio,
        x="timestamp",
        y="drawdown_pct",
        title="Drawdown (%)"
    )
    st.plotly_chart(fig, use_container_width=True)

# =====================
# P&L DISTRIBUTION
# =====================

st.subheader("💰 Trade P&L Distribution")

if not trades.empty:
    fig = px.histogram(
        trades,
        x="net_pnl",
        nbins=50,
        title="Net P&L per Trade"
    )
    st.plotly_chart(fig, use_container_width=True)

# =====================
# RISK & REGIME OVERLAY
# =====================

st.subheader("🧠 Risk & Regime Events")

if not regimes.empty:
    risk_events = regimes[regimes["type"] == "RISK_THROTTLE"]

    if not risk_events.empty:
        fig = px.step(
            risk_events,
            x="timestamp",
            y="risk_multiplier",
            title="Risk Multiplier Changes"
        )
        st.plotly_chart(fig, use_container_width=True)

# =====================
# RAW TABLES
# =====================

with st.expander("📄 Raw Data"):
    st.write("Portfolio Snapshots")
    st.dataframe(portfolio.tail(50), use_container_width=True)

    st.write("Recent Trades")
    st.dataframe(trades.tail(50), use_container_width=True)
