import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.services.admin import (
    admin_approve_user,
    admin_change_role,
    admin_delete_user,
    admin_get_llm_usage,
    admin_get_logs,
    admin_get_search_usage,
    admin_get_stats,
    admin_list_users,
)


def _metric_card(label: str, value, delta: str = "", color: str = "#6C63FF"):
    st.markdown(
        f"""
        <div style='background:#1A1D2E; border-radius:10px; padding:1.1rem 1.4rem;
                    border-left:4px solid {color};'>
            <p style='color:#9B97C9; font-size:.8rem; margin:0;'>{label}</p>
            <p style='font-size:2rem; font-weight:700; margin:.1rem 0 0;
                      color:#E8E8F0;'>{value}</p>
            {f"<p style='color:{color}; font-size:.8rem; margin:0;'>{delta}</p>" if delta else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )


def _badge(text: str, color: str):
    return (
        f"<span style='background:{color}22; color:{color}; border:1px solid {color}55; "
        f"border-radius:12px; padding:2px 10px; font-size:.78rem;'>{text}</span>"
    )


def _plotly_dark_layout(fig):
    fig.update_layout(
        plot_bgcolor="#0F1117",
        paper_bgcolor="#1A1D2E",
        font_color="#E8E8F0",
        xaxis=dict(gridcolor="#2A2D3E"),
        yaxis=dict(gridcolor="#2A2D3E"),
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


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
        try:
            stats = admin_get_stats(token)
        except RuntimeError as e:
            st.error(f"Failed to load stats: {e}")
            return

        c1, c2, c3, c4 = st.columns(4)
        with c1: _metric_card("Total Users",    stats["total_users"],    color="#6C63FF")
        with c2: _metric_card("Approved Users", stats["approved_users"], color="#2ECC71")
        with c3: _metric_card("Pending Approval", stats["pending_users"],
                              "⚠ Needs action" if stats["pending_users"] > 0 else "",
                              color="#F39C12")
        with c4: _metric_card("Total Logins",   stats["total_logins"],   color="#3498DB")

        st.markdown("<br>", unsafe_allow_html=True)

        if stats["recent_logins"]:
            st.markdown("#### Recent Login Activity")
            df = pd.DataFrame(stats["recent_logins"])
            df["login_time"] = pd.to_datetime(df["login_time"]).dt.strftime("%Y-%m-%d %H:%M")
            df.columns = ["Username", "Login Time", "IP Address"]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No login activity yet.")

    with tab_users:
        st.markdown("#### Registered Users")

        col_filter, col_refresh = st.columns([3, 1])
        with col_filter:
            show_pending = st.checkbox("Show pending accounts only", key="show_pending")
        with col_refresh:
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_users"):
                st.rerun()

        try:
            data = admin_list_users(token, pending_only=show_pending)
        except RuntimeError as e:
            st.error(f"Failed to load users: {e}")
            return

        users = data["users"]
        if not users:
            st.info("No users found.")
        else:
            st.markdown(f"<p style='color:#9B97C9;'>{data['total']} user(s)</p>", unsafe_allow_html=True)

            for user in users:
                is_self = user["id"] == st.session_state.get("user_id")

                with st.container():
                    col_info, col_status, col_actions = st.columns([3, 2, 3])

                    with col_info:
                        role_color  = "#6C63FF" if user["role"] == "admin" else "#3498DB"
                        badge_role  = _badge(user["role"].upper(), role_color)
                        badge_self  = _badge("YOU", "#9B97C9") if is_self else ""
                        st.markdown(
                            f"**{user['username']}** {badge_role} {badge_self}",
                            unsafe_allow_html=True,
                        )
                        joined = pd.to_datetime(user["created_at"]).strftime("%d %b %Y")
                        st.caption(f"Joined {joined}")

                    with col_status:
                        if user["is_approved"]:
                            st.markdown(
                                _badge("✓ Approved", "#2ECC71"),
                                unsafe_allow_html=True,
                            )
                        else:
                            st.markdown(
                                _badge("⏳ Pending", "#F39C12"),
                                unsafe_allow_html=True,
                            )

                    with col_actions:
                        if not is_self:
                            btn_col1, btn_col2, btn_col3 = st.columns(3)

                            with btn_col1:
                                if not user["is_approved"]:
                                    if st.button(
                                        "Approve",
                                        key=f"approve_{user['id']}",
                                        help="Approve account",
                                        use_container_width=True,
                                    ):
                                        try:
                                            r = admin_approve_user(token, user["id"])
                                            st.success(r["message"])
                                            st.rerun()
                                        except RuntimeError as e:
                                            st.error(str(e))

                            with btn_col2:
                                new_role = "admin" if user["role"] == "user" else "user"
                                lbl = "Promote" if new_role == "admin" else "Demote"
                                if st.button(
                                    lbl,
                                    key=f"role_{user['id']}",
                                    help=f"Change role to {new_role}",
                                    use_container_width=True,
                                ):
                                    try:
                                        r = admin_change_role(token, user["id"], new_role)
                                        st.success(r["message"])
                                        st.rerun()
                                    except RuntimeError as e:
                                        st.error(str(e))

                            with btn_col3:
                                if st.button(
                                    "Delete",
                                    key=f"del_{user['id']}",
                                    help="Delete user",
                                    use_container_width=True,
                                ):
                                    st.session_state[f"confirm_del_{user['id']}"] = True

                            if st.session_state.get(f"confirm_del_{user['id']}"):
                                st.warning(
                                    f"⚠️ Delete **{user['username']}**? This cannot be undone."
                                )
                                c_yes, c_no = st.columns(2)
                                with c_yes:
                                    if st.button(
                                        "Confirm Delete",
                                        key=f"confirm_yes_{user['id']}",
                                        type="primary",
                                    ):
                                        try:
                                            r = admin_delete_user(token, user["id"])
                                            st.success(r["message"])
                                            del st.session_state[f"confirm_del_{user['id']}"]
                                            st.rerun()
                                        except RuntimeError as e:
                                            st.error(str(e))
                                with c_no:
                                    if st.button("Cancel", key=f"confirm_no_{user['id']}"):
                                        del st.session_state[f"confirm_del_{user['id']}"]
                                        st.rerun()

                st.markdown(
                    "<hr style='border-color:#2A2D3E; margin:.5rem 0;'>",
                    unsafe_allow_html=True,
                )

    with tab_logs:
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

        if st.session_state.get("logs_loaded"):
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
            else:
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

    with tab_usage:
        st.markdown("#### LLM Token Usage")
        st.caption("Monitoring only for now — no limits are enforced yet.")

        col_refresh_llm, _ = st.columns([1, 4])
        with col_refresh_llm:
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_llm_usage"):
                st.rerun()

        try:
            llm_data = admin_get_llm_usage(token)
        except RuntimeError as e:
            st.error(f"Failed to load LLM usage: {e}")
            llm_data = {"users": []}

        llm_rows = llm_data.get("users", [])

        if not llm_rows:
            st.info("No LLM usage recorded yet.")
        else:
            total_tokens  = sum(r["total_tokens"] for r in llm_rows)
            total_calls   = sum(r["total_calls"] for r in llm_rows)
            mistral_calls = sum(r["mistral_calls"] for r in llm_rows)

            c1, c2, c3 = st.columns(3)
            with c1: _metric_card("Total Tokens (all users)", f"{total_tokens:,}", color="#6C63FF")
            with c2: _metric_card("Total LLM Calls", total_calls, color="#3498DB")
            with c3: _metric_card(
                "Mistral Fallback Calls", mistral_calls,
                "Gemini quota was hit" if mistral_calls > 0 else "",
                color="#F39C12",
            )

            st.markdown("<br>", unsafe_allow_html=True)

            llm_df = pd.DataFrame(llm_rows)
            display_df = llm_df[[
                "username", "total_calls", "total_tokens",
                "gemini_calls", "gemini_tokens",
                "mistral_calls", "mistral_tokens",
            ]].copy()
            display_df.columns = [
                "Username", "Total Calls", "Total Tokens",
                "Gemini Calls", "Gemini Tokens",
                "Mistral Calls", "Mistral Tokens",
            ]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            fig = px.bar(
                llm_df.sort_values("total_tokens", ascending=True),
                x="total_tokens",
                y="username",
                orientation="h",
                color_discrete_sequence=["#6C63FF"],
                labels={"total_tokens": "Total Tokens", "username": "User"},
            )
            st.plotly_chart(_plotly_dark_layout(fig), use_container_width=True)

        st.markdown("<hr style='border-color:#2A2D3E; margin:1.2rem 0;'>", unsafe_allow_html=True)

        st.markdown("#### Search Engine Usage")
        st.caption(
            "Tracked in credits, not raw call counts — Tavily's \"advanced\" search "
            "depth costs 2 credits per call (roughly double a normal request); "
            "everything else (Tavily basic/fast/ultra-fast, all Exa calls) is 1 credit."
        )

        col_refresh_search, _ = st.columns([1, 4])
        with col_refresh_search:
            if st.button("🔄 Refresh", use_container_width=True, key="refresh_search_usage"):
                st.rerun()

        try:
            search_data = admin_get_search_usage(token)
        except RuntimeError as e:
            st.error(f"Failed to load search usage: {e}")
            search_data = {"users": []}

        search_rows = search_data.get("users", [])

        if not search_rows:
            st.info("No search usage recorded yet.")
        else:
            total_credits = sum(r["total_credits"] for r in search_rows)
            tavily_credits = sum(r["tavily_credits"] for r in search_rows)
            exa_credits = sum(r["exa_credits"] for r in search_rows)

            c1, c2, c3 = st.columns(3)
            with c1: _metric_card("Total Credits", total_credits, color="#6C63FF")
            with c2: _metric_card("Tavily Credits", tavily_credits, color="#3498DB")
            with c3: _metric_card("Exa Credits", exa_credits, color="#2ECC71")

            st.markdown("<br>", unsafe_allow_html=True)

            search_df = pd.DataFrame(search_rows)
            display_df = search_df[[
                "username", "total_credits", "total_calls",
                "tavily_credits", "tavily_calls",
                "exa_credits", "exa_calls",
            ]].copy()
            display_df.columns = [
                "Username", "Total Credits", "Total Calls",
                "Tavily Credits", "Tavily Calls",
                "Exa Credits", "Exa Calls",
            ]
            st.dataframe(display_df, use_container_width=True, hide_index=True)

            fig = px.bar(
                search_df.sort_values("total_credits", ascending=True),
                x="total_credits",
                y="username",
                orientation="h",
                color_discrete_sequence=["#3498DB"],
                labels={"total_credits": "Search Credits", "username": "User"},
            )
            st.plotly_chart(_plotly_dark_layout(fig), use_container_width=True)