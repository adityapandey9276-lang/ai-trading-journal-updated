import streamlit as st
import pandas as pd
from utils.database import get_trades
from models.ai_engine import (train_model, best_setup, worst_setup,
                               detect_mistakes, performance_insights, compute_stats)

def show(user):
    st.markdown("<div class='page-header'>🧠 AI Insights <span>— Powered by Machine Learning</span></div>", unsafe_allow_html=True)

    trades = get_trades(user["id"])
    if not trades or len(trades) < 5:
        st.markdown("""
        <div class='mp-card' style='text-align:center; padding:3rem;'>
            <div style='font-size:2.5rem; margin-bottom:1rem;'>🧠</div>
            <div style='font-family:Orbitron,sans-serif; color:#FFD700;'>AI Needs More Data</div>
            <div style='color:#8A8A9A; margin-top:.5rem;'>Log at least 5 trades to unlock AI insights.</div>
        </div>""", unsafe_allow_html=True)
        return

    df = pd.DataFrame(trades)
    df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)

    model, encoders, feat_names = train_model(df)

    # ── Best / Worst Setup ───────────────────────────────────
    col1, col2 = st.columns(2)
    with col1:
        b = best_setup(df)
        if b:
            st.markdown(f"""
            <div class='mp-card'>
                <div style='font-family:Orbitron,sans-serif; color:#00E676; font-size:.9rem; margin-bottom:1rem;'>🏆 BEST SETUP</div>
                <div style='font-size:1.4rem; color:#FFD700; font-weight:700;'>{b.get('symbol','')} · {b.get('timeframe','')} · {b.get('strategy','')}</div>
                <div class='gold-divider'></div>
                <div style='display:flex; gap:2rem; margin-top:.8rem;'>
                    <div><div style='color:#8A8A9A; font-size:.75rem;'>WIN RATE</div><div style='color:#00E676; font-family:Orbitron,sans-serif;'>{b.get('win_rate',0):.0f}%</div></div>
                    <div><div style='color:#8A8A9A; font-size:.75rem;'>TOTAL PnL</div><div style='color:#00E676; font-family:Orbitron,sans-serif;'>${b.get('total_pnl',0):.2f}</div></div>
                    <div><div style='color:#8A8A9A; font-size:.75rem;'>TRADES</div><div style='color:#FFD700; font-family:Orbitron,sans-serif;'>{int(b.get('trades',0))}</div></div>
                </div>
                <div style='margin-top:1rem; color:#8A8A9A; font-size:.85rem;'>✅ Focus on this setup for best results.</div>
            </div>""", unsafe_allow_html=True)

    with col2:
        w = worst_setup(df)
        if w:
            st.markdown(f"""
            <div class='mp-card'>
                <div style='font-family:Orbitron,sans-serif; color:#FF1744; font-size:.9rem; margin-bottom:1rem;'>⚠️ WORST SETUP</div>
                <div style='font-size:1.4rem; color:#FFD700; font-weight:700;'>{w.get('symbol','')} · {w.get('timeframe','')} · {w.get('strategy','')}</div>
                <div class='gold-divider'></div>
                <div style='display:flex; gap:2rem; margin-top:.8rem;'>
                    <div><div style='color:#8A8A9A; font-size:.75rem;'>WIN RATE</div><div style='color:#FF1744; font-family:Orbitron,sans-serif;'>{w.get('win_rate',0):.0f}%</div></div>
                    <div><div style='color:#8A8A9A; font-size:.75rem;'>TOTAL PnL</div><div style='color:#FF1744; font-family:Orbitron,sans-serif;'>${w.get('total_pnl',0):.2f}</div></div>
                    <div><div style='color:#8A8A9A; font-size:.75rem;'>TRADES</div><div style='color:#FFD700; font-family:Orbitron,sans-serif;'>{int(w.get('trades',0))}</div></div>
                </div>
                <div style='margin-top:1rem; color:#8A8A9A; font-size:.85rem;'>❌ Avoid or review this setup carefully.</div>
            </div>""", unsafe_allow_html=True)

    # ── Performance Insights ─────────────────────────────────
    insights = performance_insights(df)
    if insights:
        st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Orbitron,sans-serif; color:#FFD700; font-size:.9rem; margin-bottom:1rem;'>💡 PERFORMANCE INSIGHTS</div>", unsafe_allow_html=True)
        for ins in insights:
            st.markdown(f"<div style='padding:.5rem 0; border-bottom:1px solid rgba(255,215,0,0.08);'>{ins}</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Mistake Detection ────────────────────────────────────
    mistakes = detect_mistakes(df)
    if mistakes:
        st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Orbitron,sans-serif; color:#FF1744; font-size:.9rem; margin-bottom:1rem;'>🚨 MISTAKE DETECTION</div>", unsafe_allow_html=True)
        for m in mistakes:
            level = m.get("level", "warning")
            st.markdown(f"""
            <div class='alert-{level}' style='margin:.5rem 0;'>
                <b>{m['type']}</b><br>
                <span style='font-size:.88rem;'>{m['detail']}</span>
            </div>""", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.markdown("""
        <div class='alert-success'>✅ No major trading mistakes detected. Keep it up!</div>
        """, unsafe_allow_html=True)

    # ── Model Stats ──────────────────────────────────────────
    if model:
        s = compute_stats(df)
        st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Orbitron,sans-serif; color:#FFD700; font-size:.9rem; margin-bottom:1rem;'>🤖 AI MODEL STATUS</div>", unsafe_allow_html=True)
        mc1, mc2, mc3, mc4 = st.columns(4)
        mc1.markdown(f"<div class='metric-card'><div class='metric-value' style='font-size:1.3rem;'>{s['total']}</div><div class='metric-label'>Training Samples</div></div>", unsafe_allow_html=True)
        mc2.markdown(f"<div class='metric-card'><div class='metric-value' style='font-size:1.3rem; color:#00E676;'>Active</div><div class='metric-label'>Model Status</div></div>", unsafe_allow_html=True)
        mc3.markdown(f"<div class='metric-card'><div class='metric-value' style='font-size:1.3rem;'>GBM</div><div class='metric-label'>Algorithm</div></div>", unsafe_allow_html=True)
        mc4.markdown(f"<div class='metric-card'><div class='metric-value' style='font-size:1.3rem;'>9</div><div class='metric-label'>Features</div></div>", unsafe_allow_html=True)
        st.markdown("<div style='color:#8A8A9A; font-size:.82rem; margin-top:1rem;'>Model retrains automatically with each session using your historical data.</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # ── Win Probability Calculator ───────────────────────────
    st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
    st.markdown("<div style='font-family:Orbitron,sans-serif; color:#FFD700; font-size:.9rem; margin-bottom:1rem;'>🎯 WIN PROBABILITY CALCULATOR</div>", unsafe_allow_html=True)
    if model:
        from models.ai_engine import predict_win_prob
        from views.trade_log import SYMBOLS, TIMEFRAMES, STRATEGIES, DIRECTIONS
        pc1, pc2, pc3 = st.columns(3)
        with pc1: p_sym = st.selectbox("Symbol",    SYMBOLS,     key="pc_sym")
        with pc2: p_tf  = st.selectbox("Timeframe", TIMEFRAMES,  key="pc_tf")
        with pc3: p_str = st.selectbox("Strategy",  STRATEGIES,  key="pc_str")
        pc4, pc5, pc6 = st.columns(3)
        with pc4: p_dir = st.selectbox("Direction", DIRECTIONS,  key="pc_dir")
        with pc5: p_rr  = st.number_input("R:R",    value=1.5, format="%.2f", key="pc_rr")
        with pc6: p_conf= st.slider("Confidence", 1, 10, 7, key="pc_conf")

        if st.button("🔮 Predict", key="predict_btn"):
            from datetime import date
            prob = predict_win_prob(model, encoders, feat_names, p_sym, p_tf, p_str, p_dir, 0.01, p_rr, p_conf, str(date.today()))
            if prob is not None:
                color = "#00E676" if prob >= 60 else ("#FFD700" if prob >= 40 else "#FF1744")
                emoji = "✅" if prob >= 60 else ("⚠️" if prob >= 40 else "❌")
                st.markdown(f"""
                <div style='text-align:center; padding:1.5rem;'>
                    <div style='font-size:3rem;'>{emoji}</div>
                    <div style='font-family:Orbitron,sans-serif; font-size:2.5rem; color:{color};'>{prob}%</div>
                    <div style='color:#8A8A9A;'>Predicted Win Probability</div>
                </div>""", unsafe_allow_html=True)
    else:
        st.info("Log at least 10 trades with both WIN and LOSS results to activate the predictor.")
    st.markdown("</div>", unsafe_allow_html=True)
