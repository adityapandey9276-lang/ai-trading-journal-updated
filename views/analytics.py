import streamlit as st
import pandas as pd
from utils.database import get_trades
from utils.charts import (equity_curve, pnl_bar, strategy_heatmap,
                           drawdown_chart, monthly_performance, win_rate_gauge)
from models.ai_engine import compute_stats

def show(user):
    st.markdown("<div class='page-header'>📈 Analytics <span>— Deep performance analysis</span></div>", unsafe_allow_html=True)

    trades = get_trades(user["id"])
    if not trades:
        st.info("No trades found. Log some trades first.")
        return

    df = pd.DataFrame(trades)
    df["pnl"]  = pd.to_numeric(df["pnl"],  errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")

    # ── Date range filter ────────────────────────────────────
    st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
    f1, f2, f3 = st.columns(3)
    with f1:
        date_from = st.date_input("From", value=pd.to_datetime(df["date"].min()).date())
    with f2:
        date_to   = st.date_input("To",   value=pd.to_datetime(df["date"].max()).date())
    with f3:
        period = st.selectbox("Quick Filter", ["All Time","This Month","This Week","Last 30 Days"])
    st.markdown("</div>", unsafe_allow_html=True)

    # Apply quick filter
    today = pd.Timestamp.now()
    if period == "This Month":
        df = df[pd.to_datetime(df["date"]).dt.month == today.month]
    elif period == "This Week":
        df = df[pd.to_datetime(df["date"]) >= today - pd.Timedelta(days=7)]
    elif period == "Last 30 Days":
        df = df[pd.to_datetime(df["date"]) >= today - pd.Timedelta(days=30)]
    else:
        df = df[(pd.to_datetime(df["date"]).dt.date >= date_from) & (pd.to_datetime(df["date"]).dt.date <= date_to)]

    if df.empty:
        st.warning("No trades in selected range.")
        return

    s = compute_stats(df)

    # ── KPI summary ──────────────────────────────────────────
    cols = st.columns(4)
    kpis = [
        ("Total PnL", f"${s['total_pnl']:,.2f}", "delta-up" if s["total_pnl"] >= 0 else "delta-down"),
        ("Win Rate",  f"{s['win_rate']}%",        "delta-up" if s["win_rate"] >= 50 else "delta-down"),
        ("Max Drawdown", f"${s['max_drawdown']:,.2f}", "delta-down"),
        ("Best Trade", f"${s['best_trade']:,.2f}", "delta-up"),
    ]
    for col, (label, val, cls) in zip(cols, kpis):
        col.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value {cls}' style='font-size:1.5rem;'>{val}</div>
            <div class='metric-label'>{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin:.8rem 0;'></div>", unsafe_allow_html=True)

    # ── Charts ───────────────────────────────────────────────
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("<div class='mp-card' style='padding:1rem;'>", unsafe_allow_html=True)
        st.plotly_chart(equity_curve(df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='mp-card' style='padding:1rem;'>", unsafe_allow_html=True)
        st.plotly_chart(drawdown_chart(df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    c3, c4 = st.columns(2)
    with c3:
        st.markdown("<div class='mp-card' style='padding:1rem;'>", unsafe_allow_html=True)
        st.plotly_chart(pnl_bar(df, group_by="date", title="Daily PnL"), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c4:
        st.markdown("<div class='mp-card' style='padding:1rem;'>", unsafe_allow_html=True)
        st.plotly_chart(monthly_performance(df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Heatmap ──────────────────────────────────────────────
    if df["strategy"].nunique() > 1 and df["symbol"].nunique() > 1:
        st.markdown("<div class='mp-card' style='padding:1rem;'>", unsafe_allow_html=True)
        st.plotly_chart(strategy_heatmap(df), use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── By Symbol ────────────────────────────────────────────
    st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:Orbitron,sans-serif; color:#FFD700; font-size:.9rem; margin-bottom:1rem;'>📊 SYMBOL BREAKDOWN</div>", unsafe_allow_html=True)
    sym_grp = df.groupby("symbol").agg(
        Trades=("result","count"),
        Wins=("result", lambda x: (x=="WIN").sum()),
        PnL=("pnl","sum"),
    ).reset_index()
    sym_grp["Win%"] = (sym_grp["Wins"]/sym_grp["Trades"]*100).round(1)
    sym_grp["PnL"]  = sym_grp["PnL"].round(2)
    st.dataframe(sym_grp.sort_values("PnL", ascending=False), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── By Strategy ──────────────────────────────────────────
    st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:Orbitron,sans-serif; color:#FFD700; font-size:.9rem; margin-bottom:1rem;'>🎯 STRATEGY BREAKDOWN</div>", unsafe_allow_html=True)
    strat_grp = df.groupby("strategy").agg(
        Trades=("result","count"),
        Wins=("result", lambda x: (x=="WIN").sum()),
        PnL=("pnl","sum"),
        AvgRR=("rr","mean"),
    ).reset_index()
    strat_grp["Win%"] = (strat_grp["Wins"]/strat_grp["Trades"]*100).round(1)
    strat_grp["PnL"]  = strat_grp["PnL"].round(2)
    strat_grp["AvgRR"]= strat_grp["AvgRR"].round(2)
    st.dataframe(strat_grp.sort_values("PnL", ascending=False), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ── By Timeframe ─────────────────────────────────────────
    st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:Orbitron,sans-serif; color:#FFD700; font-size:.9rem; margin-bottom:1rem;'>⏱️ TIMEFRAME BREAKDOWN</div>", unsafe_allow_html=True)
    tf_grp = df.groupby("timeframe").agg(
        Trades=("result","count"),
        Wins=("result", lambda x: (x=="WIN").sum()),
        PnL=("pnl","sum"),
    ).reset_index()
    tf_grp["Win%"] = (tf_grp["Wins"]/tf_grp["Trades"]*100).round(1)
    tf_grp["PnL"]  = tf_grp["PnL"].round(2)
    st.dataframe(tf_grp.sort_values("PnL", ascending=False), use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
