import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.pages.admin._shared import _plotly_dark_layout
from frontend.services.admin import admin_get_logs


def render_logs(token: str) -> None:
    st.markdown("#### Login Activity Log")

    col_search, col_limit = st.columns([3, 1])
    with col_search:
        search_user = st.text_input(
            "Filter by username", placeholder="Leave blank for all", key="log_search"
        )
    with col_limit:
        limit = st.selectbox("Show", [50, 100, 200, 500], index=1, key="log_limit")

    if st.button("🔍 Load Logs", use_container_width=False, key="load_logs"):
        st.session_state["logs_loaded"] = True

    if not st.session_state.get("logs_loaded"):
        return

    try:
        logs_data = admin_get_logs(
            token, limit=limit, username=search_user
        )
    except RuntimeError as e:
        st.error(f"Failed to load logs: {e}")
        return

    logs = logs_data["logs"]
    st.markdown(
        f"<p style='color:#9B97C9;'>{logs_data['total']} total log entries "
        f"(showing {len(logs)})</p>",
        unsafe_allow_html=True,
    )

    if not logs:
        st.info("No login logs found.")
        return

    df = pd.DataFrame(logs)
    df["login_time"] = pd.to_datetime(df["login_time"])
    df_display = df[["username", "login_time", "ip_address"]].copy()
    df_display["login_time"] = df_display["login_time"].dt.strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    df_display.columns = ["Username", "Login Time (UTC)", "IP Address"]
    st.dataframe(df_display, use_container_width=True, hide_index=True)

    st.markdown("#### Logins Per Day")
    df["date"] = df["login_time"].dt.date
    chart_df = df.groupby("date").size().reset_index(name="logins")
    fig = px.bar(
        chart_df,
        x="date",
        y="logins",
        color_discrete_sequence=["#6C63FF"],
        labels={"date": "Date", "logins": "Login Count"},
    )
    st.plotly_chart(_plotly_dark_layout(fig), use_container_width=True)