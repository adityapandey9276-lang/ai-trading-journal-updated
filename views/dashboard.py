import streamlit as st
import pandas as pd
from utils.database import get_trades, get_alerts, mark_alerts_read
from models.ai_engine import compute_stats
from utils.charts import equity_curve, pnl_bar, win_rate_gauge, symbol_pie

def show(user):
    trades = get_trades(user["id"])
    alerts = get_alerts(user["id"])

    # ── Page header ─────────────────────────────────────────
    name = user.get("full_name") or user["email"].split("@")[0]
    st.markdown(f"""
    <div class='page-header'>
        📊 Dashboard
        <span> — Welcome back, {name}</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Alerts ──────────────────────────────────────────────
    if alerts:
        with st.expander(f"🔔 {len(alerts)} Smart Alert(s) — Click to view & dismiss", expanded=True):
            for a in alerts:
                level = "danger" if a["type"] in ("OVERTRADE","STREAK") else "warning"
                st.markdown(f"<div class='alert-{level}'>{a['message']}</div>", unsafe_allow_html=True)
            if st.button("✅ Mark all as read"):
                mark_alerts_read(user["id"])
                st.rerun()

    if not trades:
        st.markdown("""
        <div class='mp-card' style='text-align:center; padding:3rem;'>
            <div style='font-size:3rem; margin-bottom:1rem;'>📋</div>
            <div style='font-family:Orbitron,sans-serif; color:#FFD700; font-size:1.1rem; margin-bottom:.5rem;'>No Trades Yet</div>
            <div style='color:#8A8A9A;'>Head to <b>Log Trade</b> to record your first trade.</div>
        </div>
        """, unsafe_allow_html=True)
        return

    df = pd.DataFrame(trades)
    df["pnl"]  = pd.to_numeric(df["pnl"],  errors="coerce").fillna(0)
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    s = compute_stats(df)

    # ── KPI Row ─────────────────────────────────────────────
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        delta_color = "delta-up" if s["total_pnl"] >= 0 else "delta-down"
        sign = "+" if s["total_pnl"] >= 0 else ""
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>${s['total_pnl']:,.2f}</div>
            <div class='metric-label'>Total PnL</div>
            <div class='metric-delta {delta_color}'>{sign}${s['total_pnl']:,.2f}</div>
        </div>""", unsafe_allow_html=True)
    with k2:
        wr_color = "delta-up" if s["win_rate"] >= 50 else "delta-down"
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{s['win_rate']}%</div>
            <div class='metric-label'>Win Rate</div>
            <div class='metric-delta {wr_color}'>{s['wins']}W / {s['losses']}L</div>
        </div>""", unsafe_allow_html=True)
    with k3:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value'>{s['total']}</div>
            <div class='metric-label'>Total Trades</div>
            <div class='metric-delta' style='color:#8A8A9A;'>Lifetime</div>
        </div>""", unsafe_allow_html=True)
    with k4:
        dd_color = "delta-down" if s["max_drawdown"] < 0 else "delta-up"
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value' style='font-size:1.4rem;'>${s['max_drawdown']:,.2f}</div>
            <div class='metric-label'>Max Drawdown</div>
            <div class='metric-delta {dd_color}'>Worst dip</div>
        </div>""", unsafe_allow_html=True)
    with k5:
        avg_color = "delta-up" if s["avg_win"] > abs(s["avg_loss"] or 0) else "delta-down"
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value' style='font-size:1.4rem;'>${s['avg_win']:,.2f}</div>
            <div class='metric-label'>Avg Win</div>
            <div class='metric-delta {avg_color}'>Avg Loss: ${s['avg_loss']:,.2f}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin:.8rem 0;'></div>", unsafe_allow_html=True)

    # ── Charts Row 1 ────────────────────────────────────────
    c1, c2 = st.columns([2.5, 1])
    with c1:
        st.markdown("<div class='mp-card' style='padding:1rem;'>", unsafe_allow_html=True)
        st.plotly_chart(equity_curve(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        st.markdown("<div class='mp-card' style='padding:1rem;'>", unsafe_allow_html=True)
        st.plotly_chart(win_rate_gauge(s["win_rate"]), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Charts Row 2 ────────────────────────────────────────
    c3, c4 = st.columns(2)
    with c3:
        st.markdown("<div class='mp-card' style='padding:1rem;'>", unsafe_allow_html=True)
        st.plotly_chart(pnl_bar(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)
    with c4:
        st.markdown("<div class='mp-card' style='padding:1rem;'>", unsafe_allow_html=True)
        st.plotly_chart(symbol_pie(df), use_container_width=True, config={"displayModeBar": False})
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Recent Trades Table ──────────────────────────────────
    st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:Orbitron,sans-serif; color:#FFD700; font-size:.95rem; margin-bottom:1rem;'>📋 RECENT TRADES</div>", unsafe_allow_html=True)
    recent = df.head(10)[["date","symbol","timeframe","strategy","direction","lot","result","pnl"]].copy()
    recent["result"] = recent["result"].apply(
        lambda r: f"🟢 WIN" if r == "WIN" else "🔴 LOSS"
    )
    recent["pnl"] = recent["pnl"].apply(lambda x: f"+${x:.2f}" if x >= 0 else f"-${abs(x):.2f}")
    st.dataframe(recent, use_container_width=True, hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)
