import streamlit as st

from frontend.utils import api_client as api
from frontend.utils.session import (
    append_message,
    get_history,
    logout,
    select_chat,
)

_TYPE_COLOR = {
    "documents": "#6C63FF",
    "urls":      "#3498DB",
    "text":      "#2ECC71",
}
_TYPE_ICON = {
    "documents": "📄",
    "urls":      "🔗",
    "text":      "📝",
}
COLLECTION_TYPES = ["documents", "urls", "text"]


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
    st.markdown("---")


def _chats_panel(token: str, project_id: str):
    st.markdown(
        "<p style='color:#9B97C9; font-size:.8rem; text-transform:uppercase; "
        "letter-spacing:.08em; margin-bottom:.5rem;'>💬 Chats</p>",
        unsafe_allow_html=True,
    )

    if st.button("＋ New Chat", use_container_width=True, key="new_chat_btn"):
        try:
            chat = api.create_chat(token, project_id)
            select_chat(chat["id"], chat["name"])
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    try:
        chats = api.list_chats(token, project_id)
    except RuntimeError as e:
        st.error(str(e))
        return

    if not chats:
        st.caption("No chats yet.")
        return

    active_id = st.session_state.get("active_chat_id")

    for chat in chats:
        cid   = chat["id"]
        cname = chat["name"]
        is_active = cid == active_id

        btn_label = f"{'▶ ' if is_active else ''}{cname}"
        if st.button(btn_label, key=f"chat_btn_{cid}", use_container_width=True):
            select_chat(cid, cname)
            st.rerun()

        if is_active:
            rc1, rc2 = st.columns(2)
            with rc1:
                if st.button("✏️", key=f"rename_chat_{cid}", use_container_width=True,
                             help="Rename chat"):
                    st.session_state[f"renaming_chat_{cid}"] = True
                    st.rerun()
            with rc2:
                if st.button("🗑️", key=f"del_chat_{cid}", use_container_width=True,
                             help="Delete chat"):
                    st.session_state[f"confirm_del_chat_{cid}"] = True
                    st.rerun()

            if st.session_state.get(f"renaming_chat_{cid}"):
                with st.form(f"rename_chat_form_{cid}", clear_on_submit=True):
                    new_name = st.text_input("New name", value=cname)
                    cs, cc = st.columns(2)
                    with cs:
                        save = st.form_submit_button("Save", type="primary",
                                                     use_container_width=True)
                    with cc:
                        cancel = st.form_submit_button("Cancel", use_container_width=True)
                if save and new_name.strip(): # type: ignore
                    try:
                        api.rename_chat(token, cid, new_name.strip()) # type: ignore
                        select_chat(cid, new_name.strip()) # type: ignore
                        del st.session_state[f"renaming_chat_{cid}"]
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))
                if cancel:
                    del st.session_state[f"renaming_chat_{cid}"]
                    st.rerun()

            if st.session_state.get(f"confirm_del_chat_{cid}"):
                st.warning(f"Delete **{cname}**?")
                cy, cn = st.columns(2)
                with cy:
                    if st.button("Yes", key=f"yes_del_chat_{cid}",
                                 type="primary", use_container_width=True):
                        try:
                            api.delete_chat(token, cid)
                            st.session_state.active_chat_id = None
                            st.session_state.chat_histories.pop(cid, None)
                            del st.session_state[f"confirm_del_chat_{cid}"]
                            st.rerun()
                        except RuntimeError as e:
                            st.error(str(e))
                with cn:
                    if st.button("No", key=f"no_del_chat_{cid}", use_container_width=True):
                        del st.session_state[f"confirm_del_chat_{cid}"]
                        st.rerun()

        st.markdown(
            "<hr style='border-color:#2A2D3E; margin:.3rem 0;'>",
            unsafe_allow_html=True,
        )


def _chat_area():
    chat_id   = st.session_state.get("active_chat_id")
    chat_name = st.session_state.get("active_chat_name", "")

    if not chat_id:
        st.markdown(
            """
            <div style='text-align:center; padding:5rem 1rem; color:#6B6E8A;'>
                <div style='font-size:3rem;'>💬</div>
                <p style='font-size:1.05rem; margin-top:.5rem;'>
                    Select a chat or create a new one to get started.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    st.markdown(
        f"<p style='color:#9B97C9; font-size:.85rem; margin-bottom:.8rem;'>"
        f"Chat: <strong style='color:#E8E8F0;'>{chat_name}</strong></p>",
        unsafe_allow_html=True,
    )

    history = get_history(chat_id)

    if not history:
        st.markdown(
            "<div style='text-align:center; padding:3rem 1rem; color:#6B6E8A;'>"
            "<p>No messages yet. Type below to start the conversation.</p></div>",
            unsafe_allow_html=True,
        )
    else:
        for msg in history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])


def _collections_panel(token: str, project_id: str):
    st.markdown(
        "<p style='color:#9B97C9; font-size:.8rem; text-transform:uppercase; "
        "letter-spacing:.08em; margin-bottom:.5rem;'>📚 Sources</p>",
        unsafe_allow_html=True,
    )

    try:
        collections = api.list_collections(token, project_id)
    except RuntimeError as e:
        st.error(str(e))
        return

    if "active_collections" not in st.session_state:
        st.session_state.active_collections = set()

    if collections:
        for col in collections:
            col_id   = col["id"]
            col_name = col["name"]
            col_type = col["type"]
            color    = _TYPE_COLOR.get(col_type, "#9B97C9")
            icon     = _TYPE_ICON.get(col_type, "📦")

            is_active = col_id in st.session_state.active_collections

            c_check, c_info, c_del = st.columns([0.5, 3, 0.5])

            with c_check:
                checked = st.checkbox(
                    "", value=is_active, key=f"col_toggle_{col_id}", label_visibility="collapsed"
                )
                if checked != is_active:
                    if checked:
                        st.session_state.active_collections.add(col_id)
                    else:
                        st.session_state.active_collections.discard(col_id)
                    st.rerun()

            with c_info:
                st.markdown(
                    f"<span style='font-size:.9rem; font-weight:600;'>{col_name}</span><br>"
                    f"<span style='background:{color}22; color:{color}; border:1px solid {color}55;"
                    f"border-radius:8px; padding:1px 7px; font-size:.72rem;'>"
                    f"{icon} {col_type}</span>",
                    unsafe_allow_html=True,
                )

            with c_del:
                if st.button("🗑", key=f"del_col_{col_id}", help=f"Delete {col_name}",
                             use_container_width=True):
                    st.session_state[f"confirm_del_col_{col_id}"] = True
                    st.rerun()

            if st.session_state.get(f"confirm_del_col_{col_id}"):
                st.warning(f"Delete **{col_name}**?")
                dc1, dc2 = st.columns(2)
                with dc1:
                    if st.button("Yes", key=f"yes_col_{col_id}",
                                 type="primary", use_container_width=True):
                        try:
                            api.delete_collection(token, col_id)
                            st.session_state.active_collections.discard(col_id)
                            del st.session_state[f"confirm_del_col_{col_id}"]
                            st.toast("Collection deleted.", icon="🗑️")
                            st.rerun()
                        except RuntimeError as e:
                            st.error(str(e))
                with dc2:
                    if st.button("No", key=f"no_col_{col_id}", use_container_width=True):
                        del st.session_state[f"confirm_del_col_{col_id}"]
                        st.rerun()

            st.markdown(
                "<hr style='border-color:#2A2D3E; margin:.3rem 0;'>",
                unsafe_allow_html=True,
            )
    else:
        st.caption("No collections yet.")

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    with st.expander("➕ Add Collection"):
        with st.form("new_collection_form", clear_on_submit=True):
            col_name = st.text_input("Name", placeholder="My documents")
            col_type = st.selectbox(
                "Type",
                COLLECTION_TYPES,
                format_func=lambda t: f"{_TYPE_ICON[t]} {t.capitalize()}",
            )
            submitted = st.form_submit_button("Create", type="primary", use_container_width=True)
        if submitted:
            if not col_name.strip():
                st.error("Name cannot be empty.")
            else:
                try:
                    api.create_collection(token, project_id, col_name.strip(), col_type)
                    st.toast("Collection created!", icon="✅")
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))


def _handle_input(token: str):
    """
    st.chat_input() renders at the very bottom of the page (outside columns).
    Only shown when a chat is active.
    """
    chat_id = st.session_state.get("active_chat_id")
    if not chat_id:
        return

    prompt = st.chat_input("Ask anything…")
    if not prompt:
        return

    append_message(chat_id, "user", prompt)

    history = get_history(chat_id)[:-1]
    api_history = [{"role": m["role"], "content": m["content"]} for m in history]

    with st.spinner("Thinking…"):
        try:
            result = api.send_message(token, chat_id, prompt, api_history)
            reply = result["response"]
        except RuntimeError as e:
            reply = f"⚠️ Error: {e}"

    append_message(chat_id, "assistant", reply)
    st.rerun()


def render():
    token      = st.session_state.token
    project_id = st.session_state.active_project_id

    if not project_id:
        st.session_state.page = "projects"
        st.rerun()

    _top_bar()

    left, center, right = st.columns([1.3, 3.8, 1.8], gap="medium")

    with left:
        _chats_panel(token, project_id)

    with center:
        _chat_area()

    with right:
        _collections_panel(token, project_id)

    _handle_input(token)