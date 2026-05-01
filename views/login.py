import streamlit as st
from utils.auth import login_user
from utils.database import create_user

def show():
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] {
        background: radial-gradient(ellipse at 20% 50%, rgba(255,215,0,0.04) 0%, #050810 60%) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.4, 1])
    with col2:
        st.markdown("""
        <div style='text-align:center; padding:2.5rem 0 2rem;'>
            <div style='font-family:Orbitron,sans-serif; font-size:2.2rem; font-weight:900;
                        color:#FFD700; text-shadow:0 0 40px rgba(255,215,0,0.5);
                        letter-spacing:.12em; line-height:1.2;'>
                💰 THE MONEY<br>PUZZELS
            </div>
            <div style='font-family:"Share Tech Mono",monospace; font-size:.7rem;
                        color:#555; letter-spacing:.3em; margin-top:.5rem;'>
                AI TRADING JOURNAL SYSTEM
            </div>
        </div>
        """, unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["🔐 Login", "📝 Sign Up"])

        with tab1:
            st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
            with st.form("login_form", clear_on_submit=False):
                email    = st.text_input("📧 Email", placeholder="you@example.com")
                password = st.text_input("🔒 Password", type="password", placeholder="••••••••")
                submitted = st.form_submit_button("LOGIN →", use_container_width=True)
                if submitted:
                    ok, msg = login_user(email, password)
                    if ok:
                        st.success(f"✅ {msg}")
                        st.rerun()
                    elif "pending" in msg:
                        st.markdown(f"""
                        <div class='alert-warning' style='margin-top:.5rem;'>
                            ⏳ <b>Account Pending Approval</b><br>
                            Your account is awaiting admin review. You'll be able to login once approved.
                        </div>""", unsafe_allow_html=True)
                    elif "rejected" in msg:
                        st.markdown(f"""
                        <div class='alert-danger' style='margin-top:.5rem;'>
                            ❌ <b>Account Rejected</b><br>
                            Your registration was not approved. Please contact support.
                        </div>""", unsafe_allow_html=True)
                    else:
                        st.error(f"❌ {msg}")
            st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("""
            <div class='alert-warning' style='font-size:.82rem; margin-top:.5rem;'>
                <b>Demo Admin:</b> admin@themoneypuzzels.com / Admin@123
            </div>
            """, unsafe_allow_html=True)

        with tab2:
            st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
            with st.form("signup_form", clear_on_submit=True):
                name  = st.text_input("👤 Full Name", placeholder="Your Name")
                email = st.text_input("📧 Email", placeholder="you@example.com")
                pw1   = st.text_input("🔒 Password", type="password", placeholder="Min. 6 chars")
                pw2   = st.text_input("🔒 Confirm Password", type="password", placeholder="Repeat password")
                submitted = st.form_submit_button("CREATE ACCOUNT →", use_container_width=True)
                if submitted:
                    if not email or not pw1:
                        st.error("All fields required.")
                    elif pw1 != pw2:
                        st.error("Passwords do not match.")
                    elif len(pw1) < 6:
                        st.error("Password must be at least 6 characters.")
                    else:
                        ok, msg = create_user(email, pw1, full_name=name)
                        if ok:
                            st.markdown(f"""
                            <div class='alert-warning' style='margin-top:.3rem;'>
                                🟡 <b>Registration Submitted!</b><br>
                                Your account is <b>pending admin approval</b>.<br>
                                You will be able to login once an admin approves your account.
                            </div>""", unsafe_allow_html=True)
                        else:
                            st.error(f"❌ {msg}")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("""
        <div style='text-align:center; margin-top:2rem; font-size:.72rem; color:#3A3A4A;'>
            © 2025 THE MONEY PUZZELS · All rights reserved
        </div>
        """, unsafe_allow_html=True)
