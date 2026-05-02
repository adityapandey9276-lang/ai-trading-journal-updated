import streamlit as st
from utils.database import get_user_by_email, verify_password, update_last_login

def check_session():
    return "user" in st.session_state

def login_user(email, password):
    email = email.strip().lower()
    password = password.strip()
    if not email or not password:
        return False, "Email and password are required."

    user = get_user_by_email(email)
    if not user:
        return False, "Email not found."
    if not verify_password(password, user["password_hash"]):
        return False, "Incorrect password."

    # ── Admin approval gate ───────────────────────────────────
    status = user.get("status", "approved")
    if status == "pending":
        return False, "⏳ Your account is pending admin approval. Please wait."
    if status == "rejected":
        return False, "❌ Your account has been rejected. Contact support."

    update_last_login(user["id"])
    st.session_state["user"] = {
        "id":        user["id"],
        "email":     user["email"],
        "full_name": user["full_name"],
        "role":      user["role"],
        "status":    user["status"],
    }
    return True, "Login successful!"

def require_admin(user):
    if user.get("role") != "admin":
        st.error("🔒 Admin access required.")
        st.stop()
