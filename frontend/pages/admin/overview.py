import pandas as pd
import streamlit as st

from frontend.pages.admin._shared import _metric_card
from frontend.services.admin import admin_get_stats


def render_overview(token: str) -> None:
    try:
        stats = admin_get_stats(token)
    except RuntimeError as e:
        st.error(f"Failed to load stats: {e}")
        return

    if "admin_users" in stats:  # superadmin view
        c1, c2, c3, c4 = st.columns(4)
        with c1: _metric_card("Total Users",  stats["total_users"],  color="#6C63FF")
        with c2: _metric_card("Total Admins", stats["admin_users"],  color="#F5A623")
        with c3: _metric_card("Pending Approval", stats["pending_users"],
                              "⚠ Needs action" if stats["pending_users"] > 0 else "",
                              color="#F39C12")
        with c4: _metric_card("Total Logins", stats["total_logins"], color="#3498DB")
    else:  # regular admin view
        c1, c2, c3 = st.columns(3)
        with c1: _metric_card("Total Users", stats["total_users"], color="#6C63FF")
        with c2: _metric_card("Pending Approval", stats["pending_users"],
                              "⚠ Needs action" if stats["pending_users"] > 0 else "",
                              color="#F39C12")
        with c3: _metric_card("Total Logins", stats["total_logins"], color="#3498DB")

    st.markdown("<br>", unsafe_allow_html=True)

    if stats["recent_logins"]:
        st.markdown("#### Recent Login Activity")
        df = pd.DataFrame(stats["recent_logins"])
        df["login_time"] = pd.to_datetime(df["login_time"]).dt.strftime("%Y-%m-%d %H:%M")
        df.columns = ["Username", "Login Time", "IP Address"]
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.info("No login activity yet.")