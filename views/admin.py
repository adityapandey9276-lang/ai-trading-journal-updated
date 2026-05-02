import streamlit as st
import pandas as pd
from utils.database import (
    get_all_users, get_pending_users, get_trades,
    update_user_status
)
from utils.auth import require_admin
from utils.charts import leaderboard_bar, equity_curve
from models.ai_engine import compute_stats

# ── Status badge helper ────────────────────────────────────────
def _status_badge(status):
    if status == "approved":
        return "<span style='background:rgba(0,230,118,.15);color:#00E676;border:1px solid rgba(0,230,118,.3);padding:.15rem .55rem;border-radius:20px;font-size:.75rem;font-weight:600;letter-spacing:.05em;'>🟢 APPROVED</span>"
    elif status == "pending":
        return "<span style='background:rgba(255,215,0,.12);color:#FFD700;border:1px solid rgba(255,215,0,.3);padding:.15rem .55rem;border-radius:20px;font-size:.75rem;font-weight:600;letter-spacing:.05em;'>🟡 PENDING</span>"
    else:
        return "<span style='background:rgba(255,23,68,.12);color:#FF1744;border:1px solid rgba(255,23,68,.3);padding:.15rem .55rem;border-radius:20px;font-size:.75rem;font-weight:600;letter-spacing:.05em;'>🔴 REJECTED</span>"

def show(user):
    require_admin(user)

    st.markdown("<div class='page-header'>👥 Admin Panel <span>— User Approvals & Team Overview</span></div>", unsafe_allow_html=True)

    # ── Pending count badge ───────────────────────────────────
    pending = get_pending_users()
    if pending:
        st.markdown(f"""
        <div class='alert-warning' style='display:flex;align-items:center;gap:.8rem;margin-bottom:1.2rem;'>
            <span style='font-size:1.5rem;'>🔔</span>
            <span style='font-family:Rajdhani,sans-serif;font-size:1.1rem;font-weight:600;'>
                {len(pending)} user(s) waiting for approval
            </span>
        </div>""", unsafe_allow_html=True)

    all_users  = get_all_users()
    all_trades = get_trades()

    # ── KPIs ─────────────────────────────────────────────────
    approved_count = sum(1 for u in all_users if u["status"] == "approved" and u["role"] != "admin")
    pending_count  = sum(1 for u in all_users if u["status"] == "pending")
    rejected_count = sum(1 for u in all_users if u["status"] == "rejected")

    kpi_cols = st.columns(4)
    kpi_data = [
        ("👥 Total Users",    len(all_users),    ""),
        ("🟢 Approved",       approved_count,    "delta-up"),
        ("🟡 Pending",        pending_count,     ""),
        ("🔴 Rejected",       rejected_count,    "delta-down"),
    ]
    for col, (label, val, cls) in zip(kpi_cols, kpi_data):
        col.markdown(f"""
        <div class='metric-card'>
            <div class='metric-value {cls}' style='font-size:1.5rem;'>{val}</div>
            <div class='metric-label'>{label}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<div style='margin:.8rem 0;'></div>", unsafe_allow_html=True)

    tab_approval, tab_users, tab_leaderboard, tab_charts = st.tabs([
        "🔔 Approvals", "👥 All Users", "🏆 Leaderboard", "📊 Team Charts"
    ])

    # ══════════════════════════════════════════════════════════
    # TAB 1 — APPROVAL QUEUE
    # ══════════════════════════════════════════════════════════
    with tab_approval:
        st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
        st.markdown("""
        <div style='font-family:Orbitron,sans-serif;color:#FFD700;font-size:.9rem;margin-bottom:1rem;'>
            PENDING APPROVAL QUEUE
        </div>""", unsafe_allow_html=True)

        if not pending:
            st.markdown("""
            <div class='alert-success' style='text-align:center;padding:2rem;'>
                ✅ No pending approvals — all caught up!
            </div>""", unsafe_allow_html=True)
        else:
            for pu in pending:
                col_info, col_approve, col_reject = st.columns([5, 1, 1])
                with col_info:
                    joined = pu.get("created_at", "")[:10]
                    name   = pu.get("full_name") or "—"
                    st.markdown(f"""
                    <div style='padding:.5rem 0;'>
                        <div style='font-weight:600;font-size:1rem;color:#F0F0F0;'>{pu['email']}</div>
                        <div style='font-size:.8rem;color:#8A8A9A;'>Name: {name} &nbsp;|&nbsp; Joined: {joined}</div>
                    </div>""", unsafe_allow_html=True)
                with col_approve:
                    if st.button("✅ Approve", key=f"approve_{pu['id']}", use_container_width=True):
                        update_user_status(pu["id"], "approved")
                        st.success(f"✅ {pu['email']} approved!")
                        st.rerun()
                with col_reject:
                    if st.button("❌ Reject", key=f"reject_{pu['id']}", use_container_width=True):
                        update_user_status(pu["id"], "rejected")
                        st.warning(f"🚫 {pu['email']} rejected.")
                        st.rerun()

                st.markdown("<div style='border-bottom:1px solid rgba(255,215,0,0.08);margin:.3rem 0;'></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # TAB 2 — ALL USERS
    # ══════════════════════════════════════════════════════════
    with tab_users:
        st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
        st.markdown("<div style='font-family:Orbitron,sans-serif;color:#FFD700;font-size:.9rem;margin-bottom:1rem;'>ALL REGISTERED USERS</div>", unsafe_allow_html=True)

        for u in all_users:
            col_info, col_status, col_action = st.columns([5, 2, 2])
            with col_info:
                role_badge = "⚙️ Admin" if u["role"] == "admin" else "📊 Trader"
                st.markdown(f"""
                <div style='padding:.4rem 0;'>
                    <span style='font-weight:600;color:#F0F0F0;'>{u['email']}</span>
                    <span style='margin-left:.6rem;font-size:.75rem;color:#FFD700;'>{role_badge}</span><br>
                    <span style='font-size:.78rem;color:#8A8A9A;'>Joined: {u.get('created_at','')[:10]}</span>
                </div>""", unsafe_allow_html=True)
            with col_status:
                st.markdown(f"<div style='padding:.6rem 0;'>{_status_badge(u.get('status','approved'))}</div>", unsafe_allow_html=True)
            with col_action:
                if u["role"] != "admin":
                    cur = u.get("status", "approved")
                    if cur != "approved":
                        if st.button("✅ Approve", key=f"au_app_{u['id']}", use_container_width=True):
                            update_user_status(u["id"], "approved")
                            st.rerun()
                    if cur != "rejected":
                        if st.button("❌ Reject", key=f"au_rej_{u['id']}", use_container_width=True):
                            update_user_status(u["id"], "rejected")
                            st.rerun()

            st.markdown("<div style='border-bottom:1px solid rgba(255,215,0,0.06);'></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # TAB 3 — LEADERBOARD
    # ══════════════════════════════════════════════════════════
    with tab_leaderboard:
        st.markdown("<div class='mp-card'>", unsafe_allow_html=True)
        lb_data = []
        for u in all_users:
            ut = [t for t in (all_trades or []) if t["user_id"] == u["id"]]
            if not ut:
                continue
            df_u = pd.DataFrame(ut)
            df_u["pnl"] = pd.to_numeric(df_u["pnl"], errors="coerce").fillna(0)
            s_u = compute_stats(df_u)
            lb_data.append({
                "email":     u["email"],
                "total_pnl": s_u["total_pnl"],
                "win_rate":  s_u["win_rate"],
                "trades":    s_u["total"],
            })

        if lb_data:
            lb_data.sort(key=lambda x: x["total_pnl"], reverse=True)
            for i, row in enumerate(lb_data):
                medal = ["🥇","🥈","🥉"][i] if i < 3 else f"#{i+1}"
                pnl_color = "#00E676" if row["total_pnl"] >= 0 else "#FF1744"
                pnl_sign  = "+" if row["total_pnl"] >= 0 else ""
                st.markdown(f"""
                <div style='display:flex;justify-content:space-between;align-items:center;
                             padding:.8rem 1rem;border-bottom:1px solid rgba(255,215,0,0.08);'>
                    <div>
                        <span style='font-size:1.2rem;'>{medal}</span>
                        <span style='margin-left:.8rem;font-weight:600;'>{row['email']}</span>
                    </div>
                    <div style='display:flex;gap:2rem;'>
                        <div style='text-align:center;'>
                            <div style='color:{pnl_color};font-family:Orbitron,sans-serif;'>{pnl_sign}${row['total_pnl']:.2f}</div>
                            <div style='color:#8A8A9A;font-size:.72rem;'>PnL</div>
                        </div>
                        <div style='text-align:center;'>
                            <div style='color:#FFD700;font-family:Orbitron,sans-serif;'>{row['win_rate']}%</div>
                            <div style='color:#8A8A9A;font-size:.72rem;'>Win Rate</div>
                        </div>
                        <div style='text-align:center;'>
                            <div style='color:#F0F0F0;font-family:Orbitron,sans-serif;'>{row['trades']}</div>
                            <div style='color:#8A8A9A;font-size:.72rem;'>Trades</div>
                        </div>
                    </div>
                </div>""", unsafe_allow_html=True)
            st.markdown("<div style='margin:.8rem 0;'></div>", unsafe_allow_html=True)
            st.plotly_chart(leaderboard_bar(lb_data), use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("No trade data yet.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ══════════════════════════════════════════════════════════
    # TAB 4 — TEAM CHARTS
    # ══════════════════════════════════════════════════════════
    with tab_charts:
        if all_trades:
            df_all = pd.DataFrame(all_trades)
            df_all["pnl"]  = pd.to_numeric(df_all["pnl"],  errors="coerce").fillna(0)
            df_all["date"] = pd.to_datetime(df_all["date"], errors="coerce").dt.strftime("%Y-%m-%d")
            st.markdown("<div class='mp-card' style='padding:1rem;'>", unsafe_allow_html=True)
            st.plotly_chart(equity_curve(df_all, title="Team Equity Curve"), use_container_width=True, config={"displayModeBar": False})
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            st.info("No team trade data yet.")
