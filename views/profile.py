import streamlit as st
from utils.database import update_profile, get_trades
from models.ai_engine import compute_stats
import pandas as pd

def show(user):
    st.markdown("<div class='page-header'>⚙️ Profile <span>— Account settings</span></div>", unsafe_allow_html=True)

    trades = get_trades(user["id"])
    df = pd.DataFrame(trades) if trades else pd.DataFrame()

    col1, col2 = st.columns([1.3, 2])

    with col1:
        initials = (user.get("full_name") or user["email"])[:2].upper()
        st.markdown(f"""
        <div class='mp-card' style='text-align:center; padding:2rem;'>
            <div style='width:80px; height:80px; border-radius:50%; background:linear-gradient(135deg,#B8960C,#FFD700);
                        display:flex; align-items:center; justify-content:center;
                        font-family:Orbitron,sans-serif; font-size:1.8rem; font-weight:700;
                        color:#050810; margin:0 auto 1rem;'>
                {initials}
            </div>
            <div style='font-family:Orbitron,sans-serif; font-size:1rem; color:#FFD700;'>
                {user.get('full_name') or 'Trader'}
            </div>
            <div style='color:#8A8A9A; font-size:.85rem; margin-top:.3rem;'>{user['email']}</div>
            <div style='margin-top:.8rem;'>
                <span class='badge badge-{"admin" if user["role"]=="admin" else "win"}'>
                    {"⚙️ Admin" if user["role"]=="admin" else "📊 Trader"}
                </span>
            </div>
        </div>""", unsafe_allow_html=True)

        if not df.empty:
            df["pnl"] = pd.to_numeric(df["pnl"], errors="coerce").fillna(0)
            s = compute_stats(df)
            st.markdown(f"""
            <div class='mp-card'>
                <div style='font-family:Orbitron,sans-serif; color:#FFD700; font-size:.8rem; margin-bottom:1rem;'>YOUR STATS</div>
                <div style='display:flex; flex-direction:column; gap:.6rem;'>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='color:#8A8A9A;'>Total Trades</span>
                        <span style='color:#FFD700; font-family:Orbitron,sans-serif;'>{s['total']}</span>
                    </div>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='color:#8A8A9A;'>Win Rate</span>
                        <span style='color:{"#00E676" if s["win_rate"]>=50 else "#FF1744"}; font-family:Orbitron,sans-serif;'>{s['win_rate']}%</span>
                    </div>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='color:#8A8A9A;'>Total PnL</span>
                        <span style='color:{"#00E676" if s["total_pnl"]>=0 else "#FF1744"}; font-family:Orbitron,sans-serif;'>${s['total_pnl']:,.2f}</span>
                    </div>
                    <div style='display:flex; justify-content:space-between;'>
                        <span style='color:#8A8A9A;'>Best Trade</span>
                        <span style='color:#00E676; font-family:Orbitron,sans-serif;'>${s['best_trade']:,.2f}</span>
                    </div>
                </div>
            </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Orbitron,sans-serif; color:#FFD700; font-size:.9rem; margin-bottom:1.2rem;'>EDIT PROFILE</div>", unsafe_allow_html=True)

        with st.form("profile_form"):
            new_name = st.text_input("Full Name", value=user.get("full_name",""))
            st.markdown("<div style='color:#8A8A9A; font-size:.82rem; margin:1rem 0 .5rem;'>Change Password (leave blank to keep current)</div>", unsafe_allow_html=True)
            new_pw1 = st.text_input("New Password",     type="password", placeholder="••••••••")
            new_pw2 = st.text_input("Confirm Password", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("💾 SAVE CHANGES", use_container_width=True)
            if submitted:
                if new_pw1 and new_pw1 != new_pw2:
                    st.error("Passwords do not match.")
                elif new_pw1 and len(new_pw1) < 6:
                    st.error("Password must be at least 6 characters.")
                else:
                    update_profile(user["id"], new_name, new_pw1 if new_pw1 else None)
                    st.session_state["user"]["full_name"] = new_name
                    st.success("✅ Profile updated!")
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

        # Data export
        st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Orbitron,sans-serif; color:#FFD700; font-size:.9rem; margin-bottom:1rem;'>📦 DATA EXPORT</div>", unsafe_allow_html=True)
        if not df.empty:
            csv = df.to_csv(index=False).encode()
            st.download_button("⬇️ Export All Trades (CSV)", data=csv,
                               file_name="all_trades_export.csv", mime="text/csv",
                               use_container_width=True)
        else:
            st.info("No trades to export.")
        st.markdown("</div>", unsafe_allow_html=True)
