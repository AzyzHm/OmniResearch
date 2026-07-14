import pandas as pd
import streamlit as st

from frontend.pages.admin._shared import _badge
from frontend.services.admin import (
    admin_approve_user,
    admin_change_role,
    admin_delete_user,
    admin_list_users,
    admin_update_token_limit,
)


def render_users(token: str) -> None:
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
        return

    st.markdown(f"<p style='color:#9B97C9;'>{data['total']} user(s)</p>", unsafe_allow_html=True)

    for user in users:
        is_self = user["id"] == st.session_state.get("user_id")
        viewer_role = st.session_state.get("role")
        is_superadmin_viewer = viewer_role == "superadmin"

        with st.container():
            col_info, col_status, col_actions = st.columns([3, 2, 3])

            with col_info:
                role_colors = {"admin": "#6C63FF", "superadmin": "#F5A623"}
                role_color  = role_colors.get(user["role"], "#3498DB")
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
                    can_change_role = is_superadmin_viewer and user["role"] != "superadmin"

                    actions = ["approve"] if not user["is_approved"] else []
                    if can_change_role:
                        actions.append("role")
                    actions.append("delete")

                    btn_cols = st.columns(len(actions))
                    for col, action in zip(btn_cols, actions):
                        with col:
                            if action == "approve":
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

                            elif action == "role":
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

                            elif action == "delete":
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

            if user["role"] == "user":
                lim_col1, lim_col2, lim_col3 = st.columns([2, 2, 1])
                with lim_col1:
                    st.caption("Daily token limit")
                with lim_col2:
                    new_limit = st.number_input(
                        "Daily token limit",
                        min_value=0,
                        max_value=100_000_000,
                        step=5000,
                        value=int(user.get("daily_token_limit", 80_000)),
                        key=f"limit_input_{user['id']}",
                        label_visibility="collapsed",
                    )
                with lim_col3:
                    if st.button("Save", key=f"save_limit_{user['id']}", use_container_width=True):
                        try:
                            r = admin_update_token_limit(token, user["id"], int(new_limit))
                            st.success(r["message"])
                            st.rerun()
                        except RuntimeError as e:
                            st.error(str(e))

        st.markdown(
            "<hr style='border-color:#2A2D3E; margin:.5rem 0;'>",
            unsafe_allow_html=True,
        )