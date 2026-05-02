import streamlit as st
import pandas as pd
from datetime import date
import yfinance as yf
from utils.database import add_trade, get_trades, delete_trade, calc_pnl
from models.ai_engine import train_model, predict_win_prob

SYMBOLS    = ["XAUUSD","EURUSD","GBPUSD","USDJPY","BTCUSD","ETHUSD","NAS100","US30","GBPJPY","AUDUSD","USDCAD","CUSTOM"]
TIMEFRAMES = ["1M","5M","15M","30M","1H","4H","1D","1W"]
STRATEGIES = [
    "CHOCH FIB RETEST",
    "MULTIPLE CANDLE DIVERSION",
    "ORDER BLOCK",
    "SUPPORT & RESISTANCE",
    "LIQUIDITY SWEEP",
    "EMA CROSS",
    "TREND CANDLESTICK DIVERSION",
    "FVG (Fair Value Gap)",
    "TRENDLINE BREAKOUT",
    "15 MIN BREAKOUT",
    "CHOCH WITH 9 EMA",
    "W & M PATTERN",
    "BOS (Break of Structure)",
    "SUPPLY & DEMAND ZONE",
    "ICT MACRO",
    "DOUBLE TOP / BOTTOM",
    "CUSTOM",
]
DIRECTIONS = ["LONG","SHORT"]

def get_yfinance_ticker(symbol):
    """Map symbol to yfinance ticker."""
    mapping = {
        "EURUSD": "EURUSD=X",
        "GBPUSD": "GBPUSD=X",
        "USDJPY": "USDJPY=X",
        "GBPJPY": "GBPJPY=X",
        "AUDUSD": "AUDUSD=X",
        "USDCAD": "USDCAD=X",
        "XAUUSD": "GC=F",  # Gold
        "BTCUSD": "BTC-USD",
        "ETHUSD": "ETH-USD",
        "NAS100": "^IXIC",  # Nasdaq
        "US30": "^DJI",  # Dow Jones
    }
    return mapping.get(symbol, symbol)  # For CUSTOM, use as is

@st.cache_data(ttl=60)
def fetch_current_price(symbol):
    """Fetch current price from yfinance."""
    try:
        ticker = get_yfinance_ticker(symbol)
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            return round(data['Close'].iloc[-1], 2)
    except Exception:
        pass
    return None

def show(user):
    st.markdown("<div class='page-header'>📝 Log Trade <span>— Record your trade with full details</span></div>", unsafe_allow_html=True)

    trades_raw  = get_trades(user["id"])
    df_existing = pd.DataFrame(trades_raw) if trades_raw else pd.DataFrame()

    model, encoders, feat_names = (None, None, None)
    if len(df_existing) >= 10:
        model, encoders, feat_names = train_model(df_existing)

    tab1, tab2 = st.tabs(["➕ New Trade", "📋 Trade History"])

    # ── Tab 1: Log Form ──────────────────────────────────────
    with tab1:
        st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Orbitron,sans-serif;color:#FFD700;font-size:.9rem;margin-bottom:1.2rem;'>TRADE DETAILS</div>", unsafe_allow_html=True)

        r1c1, r1c2, r1c3 = st.columns(3)
        with r1c1:
            trade_date = st.date_input("📅 Date", value=date.today())
        with r1c2:
            sym_opt = st.selectbox("💱 Symbol", SYMBOLS)
            if sym_opt == "CUSTOM":
                symbol = st.text_input("Custom Symbol", value=st.session_state.get("custom_symbol", ""))
                st.session_state["custom_symbol"] = symbol
            else:
                symbol = sym_opt
                st.session_state["custom_symbol"] = ""

        with r1c3:
            direction = st.selectbox("📍 Direction", DIRECTIONS)

        symbol = symbol.strip().upper() if symbol else symbol

        current_price = None
        if symbol:
            current_price = fetch_current_price(symbol)
            if current_price:
                if st.session_state.get("last_price_symbol") != symbol:
                    st.session_state["fetched_entry"] = current_price
                    st.session_state["last_price_symbol"] = symbol
                st.markdown(f"""
                <div style='display:flex;align-items:center;justify-content:space-between;
                            background:rgba(255,255,255,0.02);border:1px solid rgba(255,215,0,0.18);
                            border-radius:12px;padding:.9rem 1rem;margin:.7rem 0;color:#F0F0F0;'>
                    <div style='font-size:.9rem;color:#8A8A9A;'>Live price for <b>{symbol}</b></div>
                    <div style='font-size:1.1rem;font-weight:700;color:#00E676;'>${current_price}</div>
                </div>""", unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='background:rgba(255,23,68,0.08);border:1px solid rgba(255,23,68,0.2);
                            border-radius:12px;padding:.8rem 1rem;margin:.7rem 0;color:#F0F0F0;'>
                    Unable to fetch live price for <b>{symbol}</b>.
                    Please check the symbol or internet connection.
                </div>""", unsafe_allow_html=True)

        price_col, button_col = st.columns([4,1])
        with price_col:
            if symbol and current_price is None:
                st.info("Live symbol lookup is enabled. Press refresh or verify the symbol.")
        with button_col:
            if st.button("📈 Refresh Price", key="fetch_price"):
                current_price = fetch_current_price(symbol)
                if current_price:
                    st.session_state["fetched_entry"] = current_price
                    st.session_state["last_price_symbol"] = symbol
                    st.success(f"Updated live price for {symbol}: {current_price}")
                else:
                    st.error("Failed to fetch live price. Check symbol or internet.")

        r2c1, r2c2, r2c3 = st.columns(3)
        with r2c1:
            timeframe = st.selectbox("⏱️ Timeframe", TIMEFRAMES)
        with r2c2:
            strat_opt = st.selectbox("🎯 Strategy", STRATEGIES)
            strategy  = st.text_input("Custom Strategy") if strat_opt == "CUSTOM" else strat_opt
        with r2c3:
            result = st.selectbox("🏁 Result", ["WIN","LOSS","BE"])

        r3c1, r3c2, r3c3, r3c4 = st.columns(4)
        with r3c1: entry = st.number_input("🎯 Entry Price", min_value=0.0, value=st.session_state.get("fetched_entry", 0.0), format="%.2f")
        with r3c2: sl    = st.number_input("🛑 Stop Loss",   min_value=0.0, format="%.2f")
        with r3c3: tp    = st.number_input("✅ Take Profit", min_value=0.0, format="%.2f")
        with r3c4: lot   = st.number_input("📦 Lot Size",    min_value=0.001, value=0.01, format="%.3f")

        # ── Auto P&L Calculator ──────────────────────────────
        auto_pnl, auto_rr = calc_pnl(entry, sl, tp, lot, direction, result)

        pnl_color = "#00E676" if auto_pnl >= 0 else "#FF1744"
        rr_color  = "#FFD700" if auto_rr >= 2 else ("#F0F0F0" if auto_rr >= 1 else "#FF1744")

        if entry > 0 and sl > 0 and tp > 0:
            st.markdown(f"""
            <div style='background:rgba(255,215,0,0.05);border:1px solid rgba(255,215,0,0.2);
                        border-radius:10px;padding:.9rem 1.2rem;margin:.6rem 0;
                        display:flex;gap:2.5rem;align-items:center;'>
                <div>
                    <div style='font-size:.72rem;color:#8A8A9A;text-transform:uppercase;letter-spacing:.08em;'>Auto P&L</div>
                    <div style='font-family:Orbitron,sans-serif;font-size:1.4rem;font-weight:700;color:{pnl_color};'>
                        {"+" if auto_pnl >= 0 else ""}${auto_pnl:,.2f}
                    </div>
                </div>
                <div>
                    <div style='font-size:.72rem;color:#8A8A9A;text-transform:uppercase;letter-spacing:.08em;'>Risk : Reward</div>
                    <div style='font-family:Orbitron,sans-serif;font-size:1.4rem;font-weight:700;color:{rr_color};'>
                        1 : {auto_rr}
                    </div>
                </div>
                <div style='font-size:.75rem;color:#8A8A9A;border-left:1px solid rgba(255,215,0,0.15);padding-left:1.2rem;'>
                    ⚡ Calculated automatically<br>from entry / SL / TP / lot
                </div>
            </div>""", unsafe_allow_html=True)

        r4c1, r4c2 = st.columns(2)
        with r4c1:
            manual_pnl = st.number_input("💵 P&L Override ($) — leave 0 to use auto", value=0.0, format="%.2f")
        with r4c2:
            st.markdown("<div style='padding-top:1.9rem;font-size:.82rem;color:#8A8A9A;'>Auto-calculated above. Override only if broker P&L differs.</div>", unsafe_allow_html=True)

        final_pnl = manual_pnl if manual_pnl != 0.0 else auto_pnl
        final_rr  = auto_rr

        confidence = st.slider("🎯 Confidence Level (1–10)", 1, 10, 7)
        notes      = st.text_area("📝 Notes / Observations",
                        placeholder="Confluences, market structure, emotions, what went right/wrong…",
                        height=90)

        # AI prediction
        if model and symbol and strategy and timeframe:
            prob = predict_win_prob(model, encoders, feat_names, symbol, timeframe, strategy,
                                   direction, lot, final_rr, confidence, str(trade_date))
            if prob is not None:
                color = "#00E676" if prob >= 60 else ("#FFD700" if prob >= 40 else "#FF1744")
                emoji = "✅" if prob >= 60 else ("⚠️" if prob >= 40 else "❌")
                st.markdown(f"""
                <div class='alert-{"success" if prob>=60 else ("warning" if prob>=40 else "danger")}'>
                    {emoji} <b>AI Win Probability:
                    <span style='color:{color};font-family:Orbitron,sans-serif;'>{prob}%</span></b>
                    &nbsp;—&nbsp; Based on your historical data for this setup.
                </div>""", unsafe_allow_html=True)

        st.markdown("<div style='margin:.8rem 0;'></div>", unsafe_allow_html=True)
        col_btn, _ = st.columns([1, 3])
        with col_btn:
            if st.button("💾 SAVE TRADE", use_container_width=True):
                if not symbol or not strategy:
                    st.error("Please fill in Symbol and Strategy.")
                else:
                    add_trade(
                        user_id=user["id"],
                        date=str(trade_date),
                        symbol=symbol, timeframe=timeframe, strategy=strategy,
                        direction=direction, entry=entry, sl=sl, tp=tp,
                        lot=lot, result=result, pnl=final_pnl, rr=final_rr,
                        confidence=confidence, notes=notes
                    )
                    st.markdown("<div class='alert-success'>✅ Trade logged successfully!</div>", unsafe_allow_html=True)
                    st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    # ── Tab 2: History ───────────────────────────────────────
    with tab2:
        if df_existing.empty:
            st.info("No trades yet.")
            return

        st.markdown("<div class='mp-card'>", unsafe_allow_html=True)

        fc1, fc2, fc3 = st.columns(3)
        with fc1:
            syms = ["All"] + sorted(df_existing["symbol"].unique().tolist())
            sym_filter = st.selectbox("Filter by Symbol", syms, key="hist_sym")
        with fc2:
            strats = ["All"] + sorted(df_existing["strategy"].unique().tolist())
            strat_filter = st.selectbox("Filter by Strategy", strats, key="hist_strat")
        with fc3:
            res_filter = st.selectbox("Filter by Result", ["All","WIN","LOSS","BE"], key="hist_res")

        df_view = df_existing.copy()
        if sym_filter   != "All": df_view = df_view[df_view["symbol"]   == sym_filter]
        if strat_filter != "All": df_view = df_view[df_view["strategy"] == strat_filter]
        if res_filter   != "All": df_view = df_view[df_view["result"]   == res_filter]

        st.markdown(f"<div style='color:#8A8A9A;font-size:.85rem;margin-bottom:.8rem;'>Showing {len(df_view)} trades</div>", unsafe_allow_html=True)

        cols_show = ["id","date","symbol","timeframe","strategy","direction","lot","result","pnl","rr","confidence","notes"]
        cols_avail = [c for c in cols_show if c in df_view.columns]
        display_df = df_view[cols_avail].copy()
        display_df["pnl"] = pd.to_numeric(display_df["pnl"], errors="coerce").round(2)
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
        del_id = st.number_input("Enter Trade ID to Delete", min_value=1, step=1)
        if st.button("🗑️ Delete Trade", type="secondary"):
            delete_trade(del_id, user["id"])
            st.success("Trade deleted.")
            st.rerun()

        csv = display_df.to_csv(index=False).encode()
        st.download_button("⬇️ Export CSV", data=csv, file_name="my_trades.csv", mime="text/csv")
        st.markdown("</div>", unsafe_allow_html=True)
