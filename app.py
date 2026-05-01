import streamlit as st
from utils.database import init_db, get_pending_users
from utils.auth import check_session
from views import login, dashboard, trade_log, analytics, ai_insights, admin, profile

st.set_page_config(
    page_title="THE MONEY PUZZELS | AI Trading Journal",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded",
)

def load_css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Exo+2:wght@300;400;500;600;700;800;900&family=Orbitron:wght@400;700;900&family=Share+Tech+Mono&display=swap');

    :root {
        --gold:       #FFD700;
        --gold-light: #FFE566;
        --gold-dark:  #B8960C;
        --bg-primary: #050810;
        --bg-card:    #0D1117;
        --bg-glass:   rgba(255,215,0,0.04);
        --border:     rgba(255,215,0,0.15);
        --border-glow:rgba(255,215,0,0.4);
        --text-primary:   #F0F0F0;
        --text-secondary: #8A8A9A;
        --green:  #00E676;
        --red:    #FF1744;
        --blue:   #00B0FF;
        --purple: #D500F9;
    }

    html, body, [data-testid="stAppViewContainer"] {
        min-height: 100vh;
        background: radial-gradient(circle at top left, rgba(255,215,0,0.12), transparent 24%),
                    radial-gradient(circle at top right, rgba(0,176,255,0.12), transparent 18%),
                    linear-gradient(135deg, #050810 0%, #0a0f1c 35%, #050810 100%) !important;
        background-attachment: fixed !important;
        font-family: 'Exo 2', sans-serif !important;
        color: var(--text-primary) !important;
        perspective: 1200px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #07091A 0%, #050810 100%) !important;
        border-right: 1px solid var(--border) !important;
    }
    [data-testid="stSidebar"] * { color: var(--text-primary) !important; }

    /* Hide default streamlit chrome */
    #MainMenu, footer, header { visibility: hidden !important; }
    .block-container { padding: 1.5rem 2rem !important; }

    /* Cards */
    .mp-card {
        background: rgba(12, 15, 25, 0.92);
        border: 1px solid rgba(255,215,0,0.16);
        border-radius: 18px;
        padding: 1.6rem;
        margin-bottom: 1.2rem;
        position: relative;
        overflow: hidden;
        transition: border-color .25s, box-shadow .25s, transform .25s;
        box-shadow: 0 18px 55px rgba(0,0,0,0.35);
        transform-style: preserve-3d;
        backdrop-filter: blur(12px);
    }
    .mp-card:hover {
        border-color: rgba(255,215,0,0.45);
        box-shadow: 0 28px 85px rgba(255,215,0,0.12);
        transform: translateY(-8px);
    }
    .mp-card::before {
        content:'';
        position:absolute; top:0; left:0; right:0; height:2px;
        background: linear-gradient(90deg, transparent, var(--gold), transparent);
    }
    .mp-card::after {
        content:'';
        position:absolute; inset:0;
        background: linear-gradient(135deg, rgba(255,255,255,0.05), transparent 48%, rgba(255,255,255,0.03));
        pointer-events:none;
        mix-blend-mode: screen;
    }

    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #0D1117 0%, #111827 100%);
        border: 1px solid var(--border);
        border-radius: 10px;
        padding: 1.2rem 1.5rem;
        text-align: center;
        transition: all .3s;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        position: relative;
        overflow: hidden;
    }
    .metric-card::before {
        content: '';
        position: absolute;
        top: 0; left: 0; right: 0; bottom: 0;
        background: linear-gradient(135deg, rgba(255,215,0,0.05) 0%, transparent 50%);
        pointer-events: none;
    }
    .metric-card:hover {
        border-color: var(--gold);
        box-shadow: 0 8px 30px rgba(255,215,0,0.2);
        transform: translateY(-5px);
    }
    .metric-value {
        font-family:'Orbitron',sans-serif;
        font-size: 2rem;
        font-weight: 700;
        color: var(--gold);
        letter-spacing: .04em;
    }
    .metric-label {
        font-family: 'Exo 2', sans-serif;
        font-size: .82rem;
        color: var(--text-secondary);
        text-transform: uppercase;
        letter-spacing: .12em;
        margin-top: .4rem;
        font-weight: 500;
    }
    .metric-delta { font-size:.82rem; margin-top:.3rem; font-weight:600; }
    .delta-up   { color: var(--green); }
    .delta-down { color: var(--red);   }

    /* Buttons */
    .stButton>button {
        background: linear-gradient(135deg, var(--gold-dark), var(--gold)) !important;
        color: #050810 !important;
        font-family: 'Exo 2', sans-serif !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        letter-spacing: .1em !important;
        border: none !important;
        border-radius: 8px !important;
        padding: .65rem 1.8rem !important;
        transition: all .3s !important;
        text-transform: uppercase !important;
        box-shadow: 0 4px 15px rgba(255,215,0,0.3) !important;
        position: relative !important;
        overflow: hidden !important;
    }
    .stButton>button::before {
        content: '';
        position: absolute;
        top: 0; left: -100%;
        width: 100%; height: 100%;
        background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
        transition: left 0.5s;
    }
    .stButton>button:hover::before {
        left: 100%;
    }
    .stButton>button:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 8px 25px rgba(255,215,0,0.5) !important;
    }

    /* Inputs */
    .stTextInput>div>div>input,
    .stSelectbox>div>div,
    .stNumberInput>div>div>input,
    .stTextArea>div>div>textarea {
        background: rgba(12, 17, 28, 0.95) !important;
        border: 1px solid rgba(255,215,0,0.18) !important;
        color: var(--text-primary) !important;
        border-radius: 14px !important;
        font-family: 'Exo 2', sans-serif !important;
        font-size: 1rem !important;
        box-shadow: inset 0 0 18px rgba(255,215,0,0.04);
        transition: border-color .25s, box-shadow .25s, transform .25s;
    }
    .stTextInput>div>div>input:focus,
    .stTextArea>div>div>textarea:focus,
    .stNumberInput>div>div>input:focus {
        border-color: var(--gold) !important;
        box-shadow: 0 0 0 2px rgba(255,215,0,0.16) !important;
        transform: translateY(-1px) !important;
    }
    /* Input labels */
    .stTextInput label, .stSelectbox label, .stNumberInput label,
    .stTextArea label, .stDateInput label, .stSlider label {
        font-family: 'Exo 2', sans-serif !important;
        font-weight: 600 !important;
        font-size: .88rem !important;
        color: #C0C0D0 !important;
        letter-spacing: .05em !important;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        background: rgba(13, 17, 24, 0.96) !important;
        border-bottom: 1px solid rgba(255,215,0,0.12) !important;
        border-radius: 14px 14px 0 0 !important;
        box-shadow: inset 0 -1px 0 rgba(255,215,0,0.06);
    }
    .stTabs [data-baseweb="tab"] {
        color: var(--text-secondary) !important;
        font-family: 'Exo 2', sans-serif !important;
        font-weight: 700 !important;
        font-size: .95rem !important;
        letter-spacing: .08em !important;
        padding: .75rem 1rem !important;
        transition: color .25s, transform .25s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        transform: translateY(-1px) !important;
    }
    .stTabs [aria-selected="true"] {
        color: var(--gold) !important;
        border-bottom: 3px solid var(--gold) !important;
    }

    /* DataFrames */
    .stDataFrame { border: 1px solid var(--border) !important; border-radius: 10px !important; }
    .stDataFrame th {
        font-family: 'Exo 2', sans-serif !important;
        font-weight: 700 !important;
        color: #FFD700 !important;
        text-transform: uppercase !important;
        letter-spacing: .06em !important;
        font-size: .82rem !important;
    }
    .stDataFrame td {
        font-family: 'Share Tech Mono', monospace !important;
        font-size: .9rem !important;
    }

    /* Alerts */
    .stAlert { border-radius: 10px !important; border-left: 4px solid var(--gold) !important; }

    /* Scrollbar */
    ::-webkit-scrollbar { width:6px; height:6px; }
    ::-webkit-scrollbar-track { background: var(--bg-primary); }
    ::-webkit-scrollbar-thumb { background: var(--gold-dark); border-radius:3px; }

    /* Logo area */
    .brand-logo {
        font-family: 'Orbitron', sans-serif;
        font-weight: 900;
        font-size: 1.05rem;
        letter-spacing: .12em;
        color: var(--gold);
        text-shadow: 0 0 20px rgba(255,215,0,0.4);
        line-height: 1.3;
    }
    .brand-sub {
        font-family: 'Share Tech Mono', monospace;
        font-size: .65rem;
        color: var(--text-secondary);
        letter-spacing: .2em;
        text-transform: uppercase;
    }

    /* Page headers */
    .page-header {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.55rem;
        font-weight: 700;
        color: var(--gold);
        margin-bottom: 1.5rem;
        padding-bottom: .8rem;
        border-bottom: 1px solid var(--border);
        letter-spacing: .06em;
    }
    .page-header span {
        color: var(--text-secondary);
        font-size: .92rem;
        font-family: 'Exo 2', sans-serif;
        font-weight: 400;
    }

    /* Badge */
    .badge {
        display:inline-block; padding:.2rem .6rem;
        border-radius:20px; font-size:.75rem; font-weight:700;
        letter-spacing:.06em; text-transform:uppercase;
        font-family: 'Exo 2', sans-serif;
    }
    .badge-win  { background:rgba(0,230,118,.15); color:var(--green); border:1px solid rgba(0,230,118,.3); }
    .badge-loss { background:rgba(255,23,68,.15);  color:var(--red);   border:1px solid rgba(255,23,68,.3);  }
    .badge-admin{ background:rgba(255,215,0,.15);  color:var(--gold);  border:1px solid rgba(255,215,0,.3);  }

    /* Gold divider */
    .gold-divider {
        height: 1px;
        background: linear-gradient(90deg, transparent, var(--gold), transparent);
        margin: 1.5rem 0;
        opacity: .5;
    }

    /* Alert boxes */
    .alert-danger {
        background: rgba(255,23,68,.08);
        border: 1px solid rgba(255,23,68,.3);
        border-left: 4px solid var(--red);
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: .5rem 0;
    }
    .alert-warning {
        background: rgba(255,215,0,.06);
        border: 1px solid var(--border);
        border-left: 4px solid var(--gold);
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: .5rem 0;
    }
    .alert-success {
        background: rgba(0,230,118,.08);
        border: 1px solid rgba(0,230,118,.3);
        border-left: 4px solid var(--green);
        border-radius: 8px;
        padding: 1rem 1.5rem;
        margin: .5rem 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ─── Init ──────────────────────────────────────────────────────
init_db()
load_css()

# ─── Router ────────────────────────────────────────────────────
if "user" not in st.session_state:
    login.show()
else:
    user = st.session_state["user"]

    with st.sidebar:
        st.markdown("""
        <div style='text-align:center; padding:1rem 0 1.5rem;'>
            <div class='brand-logo'>💰 THE MONEY<br>PUZZELS</div>
            <div class='brand-sub'>AI Trading Journal</div>
        </div>
        <div class='gold-divider'></div>
        """, unsafe_allow_html=True)

        role_label = "⚙️ Admin" if user["role"] == "admin" else "📊 Trader"
        st.markdown(f"""
        <div style='font-size:.88rem; color:#8A8A9A; padding:.3rem 0 .8rem;'>
            👤 <b style='color:#E0E0E0;'>{user['email']}</b><br>
            <span style='color:#FFD700;font-size:.75rem;text-transform:uppercase;
                         letter-spacing:.1em;font-family:"Exo 2",sans-serif;font-weight:700;'>
                {role_label}
            </span>
        </div>""", unsafe_allow_html=True)

        # Show pending badge for admin
        if user["role"] == "admin":
            pending = get_pending_users()
            if pending:
                st.markdown(f"""
                <div style='background:rgba(255,215,0,.1);border:1px solid rgba(255,215,0,.3);
                             border-radius:8px;padding:.4rem .8rem;margin-bottom:.5rem;
                             font-size:.8rem;color:#FFD700;font-weight:700;'>
                    🔔 {len(pending)} Pending Approval{"s" if len(pending)>1 else ""}
                </div>""", unsafe_allow_html=True)

        pages = {
            "📊 Dashboard":   "dashboard",
            "📝 Log Trade":    "trade_log",
            "📈 Analytics":    "analytics",
            "🧠 AI Insights":  "ai_insights",
        }
        if user["role"] == "admin":
            pages["👥 Admin Panel"] = "admin"
        pages["⚙️ Profile"] = "profile"

        if "page" not in st.session_state:
            st.session_state["page"] = "dashboard"

        for label, key in pages.items():
            is_active = st.session_state["page"] == key
            btn_style = "background:rgba(255,215,0,.12);border-left:3px solid #FFD700;" if is_active else ""
            # Render button
            if st.button(label, key=f"nav_{key}", use_container_width=True):
                st.session_state["page"] = key
                st.rerun()

        st.markdown("<div class='gold-divider'></div>", unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            del st.session_state["user"]
            st.session_state["page"] = "dashboard"
            st.rerun()

        st.markdown("<div style='position:absolute;bottom:1rem;left:0;right:0;text-align:center;font-size:.7rem;color:#3A3A4A;'>© 2025 THE MONEY PUZZELS</div>", unsafe_allow_html=True)

    # ── Page routing ──────────────────────────────────────────
    pg = st.session_state.get("page", "dashboard")
    if   pg == "dashboard":   dashboard.show(user)
    elif pg == "trade_log":   trade_log.show(user)
    elif pg == "analytics":   analytics.show(user)
    elif pg == "ai_insights": ai_insights.show(user)
    elif pg == "admin":       admin.show(user)
    elif pg == "profile":     profile.show(user)
    else:
        st.session_state["page"] = "dashboard"
        st.rerun()
