import streamlit as st

from frontend.pages.workspace.chat_area import _chat_area, _handle_input
from frontend.pages.workspace.chats_panel import _chats_panel
from frontend.pages.workspace.collections_panel import _collections_panel
from frontend.utils.session import logout


def _top_bar():
    c_back, c_title, c_logout = st.columns([1, 6, 1])
    with c_back:
        if st.button("← Projects", use_container_width=True):
            st.session_state.active_project_id = None
            st.session_state.active_chat_id = None
            st.session_state.page = "projects"
            st.rerun()
    with c_title:
        st.markdown(
            f"<h3 style='margin:0; padding-top:.3rem;'>"
            f"📁 {st.session_state.active_project_name}</h3>",
            unsafe_allow_html=True,
        )
    with c_logout:
        if st.button("Sign Out", use_container_width=True):
            logout()
    st.markdown(
        "<hr style='margin:.6rem 0 .8rem;'>",
        unsafe_allow_html=True,
    )


def render():
    token      = st.session_state.token
    project_id = st.session_state.active_project_id

    st.session_state.setdefault("show_search_modal", None)

    if not project_id:
        st.session_state.page = "projects"
        st.rerun()

    _top_bar()

    left, center, right = st.columns([1.3, 3.8, 1.8], gap="medium")

    with left:
        _chats_panel(token, project_id)

    with center:
        with st.container(border=True):
            messages_box, empty_placeholder = _chat_area()
            _handle_input(token, messages_box, empty_placeholder)

    with right:
        _collections_panel(token, project_id)