import streamlit as st

from frontend.pages.admin.logs import render_logs
from frontend.pages.admin.overview import render_overview
from frontend.pages.admin.usage import render_usage
from frontend.pages.admin.users import render_users


def render():
    token = st.session_state.get("token", "")

    col_title, col_user, col_logout = st.columns([5, 2, 1])
    with col_title:
        st.markdown(
            "<h2 style='margin:0; padding:.5rem 0;'>⚙️ Admin Dashboard</h2>",
            unsafe_allow_html=True,
        )
    with col_user:
        st.markdown(
            f"<p style='color:#9B97C9; text-align:right; padding-top:.9rem; margin:0;'>"
            f"Signed in as <strong>{st.session_state.get('username','')}</strong></p>",
            unsafe_allow_html=True,
        )
    with col_logout:
        if st.button("Sign Out", use_container_width=True):
            for key in ["token", "user_id", "username", "role", "page"]:
                st.session_state.pop(key, None)
            st.session_state.page = "login"
            st.rerun()

    st.markdown("---")
    tab_overview, tab_users, tab_logs, tab_usage = st.tabs(
        ["📊 Overview", "👥 User Management", "📋 Login Logs", "📈 Usage"]
    )

    with tab_overview:
        render_overview(token)

    with tab_users:
        render_users(token)

    with tab_logs:
        render_logs(token)

    with tab_usage:
        render_usage(token)