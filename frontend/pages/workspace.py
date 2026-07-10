import streamlit as st
from streamlit_autorefresh import st_autorefresh

from frontend.components.search_modal import render_search_modal
from frontend import services as api
from frontend.utils.session import (
    append_message,
    load_chat_history,
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

_UPLOADABLE_TYPES = {
    "documents": ["pdf"],
    "text": ["txt"],
}

_STATUS_BADGE = {
    "ready":      ("#2ECC71", "Ready"),
    "processing": ("#F5A623", "Processing…"),
    "error":      ("#E74C3C", "Error"),
}

SECTION_HEIGHT = 480
CHAT_SECTION_HEIGHT = 440


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


def _chats_panel(token: str, project_id: str):
    st.markdown(
        "<p style='color:#9B97C9; font-size:.8rem; text-transform:uppercase; "
        "letter-spacing:.08em; margin-bottom:.5rem;'>💬 Chats</p>",
        unsafe_allow_html=True,
    )

    if st.button("▶ Start a Chat", use_container_width=True, key="new_chat_btn"):
        try:
            chat = api.create_chat(token, project_id)
            select_chat(chat["id"], chat["name"])
            st.rerun()
        except RuntimeError as e:
            st.error(str(e))

    st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

    with st.container(height=SECTION_HEIGHT):
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
                    if st.button("Rename", key=f"rename_chat_{cid}", use_container_width=True,
                                 help="Rename chat"):
                        st.session_state[f"renaming_chat_{cid}"] = True
                        st.rerun()
                with rc2:
                    if st.button("Delete", key=f"del_chat_{cid}", use_container_width=True,
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
    """Renders the message list. Returns the messages container object so
    _handle_input can write the new user/assistant turns directly into it
    in real time, instead of waiting for a full page rerun to show them."""
    chat_id   = st.session_state.get("active_chat_id")
    chat_name = st.session_state.get("active_chat_name", "")

    if not chat_id:
        with st.container(height=CHAT_SECTION_HEIGHT, border=False):
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
        return None

    st.markdown(
        f"<p style='color:#9B97C9; font-size:.85rem; margin-bottom:.8rem;'>"
        f"Chat: <strong style='color:#E8E8F0;'>{chat_name}</strong></p>",
        unsafe_allow_html=True,
    )

    history = load_chat_history(chat_id)

    messages_box = st.container(height=CHAT_SECTION_HEIGHT, border=False)
    with messages_box:
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

    return messages_box


def _collection_items(token: str, collection_id: str, col_type: str):
    """Render the per-item list (checkbox, status, delete) and the uploader.

    Checkboxes are purely local UI state (backed by their own widget key in
    st.session_state) until "Save Changes" is clicked — that's what stops a
    burst of clicks from firing one API request per checkbox.
    """
    try:
        items = api.list_collection_items(token, collection_id)
    except RuntimeError as e:
        st.error(str(e))
        items = []

    if any(i["status"] == "processing" for i in items):
        st_autorefresh(interval=2500, key=f"autorefresh_{collection_id}")

    def _checkbox_key(item_id: str) -> str:
        return f"item_toggle_{collection_id}_{item_id}"

    ready_items = [i for i in items if i["status"] == "ready"]

    for item in items:
        st.session_state.setdefault(_checkbox_key(item["id"]), item["is_active"])

    if items:
        if ready_items:
            sa1, sa2 = st.columns(2)
            with sa1:
                if st.button("☑️ Select All", key=f"select_all_{collection_id}",
                             use_container_width=True):
                    for item in ready_items:
                        st.session_state[_checkbox_key(item["id"])] = True
                    st.rerun()
            with sa2:
                if st.button("⬜ Deselect All", key=f"deselect_all_{collection_id}",
                             use_container_width=True):
                    for item in ready_items:
                        st.session_state[_checkbox_key(item["id"])] = False
                    st.rerun()

        for item in items:
            item_id = item["id"]
            name    = item["name"]
            status  = item["status"]
            badge_color, badge_label = _STATUS_BADGE.get(status, ("#9B97C9", status))

            ic1, ic2, ic3 = st.columns([0.5, 3.2, 0.5])

            with ic1:
                st.checkbox(
                    "", key=_checkbox_key(item_id),
                    label_visibility="collapsed",
                    disabled=(status != "ready"),
                )

            with ic2:
                st.markdown(
                    f"<span style='font-size:.85rem;'>{name}</span><br>"
                    f"<span style='background:{badge_color}22; color:{badge_color}; "
                    f"border:1px solid {badge_color}55; border-radius:8px; "
                    f"padding:1px 6px; font-size:.68rem;'>{badge_label}</span>",
                    unsafe_allow_html=True,
                )
                if status == "error" and item.get("error_message"):
                    st.caption(f"⚠️ {item['error_message']}")

            with ic3:
                if st.button("", icon="❌", key=f"del_item_{item_id}", help=f"Remove {name}",
                             use_container_width=True):
                    try:
                        api.delete_collection_item(token, collection_id, item_id)
                        st.session_state.pop(_checkbox_key(item_id), None)
                        st.toast("File removed.", icon="❌")
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))

            st.markdown(
                "<hr style='border-color:#242637; margin:.25rem 0;'>",
                unsafe_allow_html=True,
            )

        dirty = {
            item["id"]: st.session_state[_checkbox_key(item["id"])]
            for item in ready_items
            if st.session_state[_checkbox_key(item["id"])] != item["is_active"]
        }

        if dirty:
            st.info(f"{len(dirty)} unsaved change(s).")
            sv1, sv2 = st.columns(2)
            with sv1:
                if st.button("💾 Save Changes", key=f"save_toggles_{collection_id}",
                             type="primary", use_container_width=True):
                    try:
                        updates = [
                            {"item_id": iid, "is_active": val} for iid, val in dirty.items()
                        ]
                        api.bulk_update_collection_items(token, collection_id, updates)
                        st.toast("Changes saved!", icon="✅")
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))
            with sv2:
                if st.button("Discard", key=f"discard_toggles_{collection_id}",
                             use_container_width=True):
                    for item in ready_items:
                        st.session_state[_checkbox_key(item["id"])] = item["is_active"]
                    st.rerun()
    else:
        st.caption("No files yet.")

    if col_type in _UPLOADABLE_TYPES:
        allowed_ext = _UPLOADABLE_TYPES[col_type]
        with st.form(f"upload_form_{collection_id}", clear_on_submit=True):
            uploaded = st.file_uploader(
                f"Add .{allowed_ext[0]} files",
                type=allowed_ext,
                accept_multiple_files=True,
                key=f"uploader_{collection_id}",
            )
            submitted = st.form_submit_button("Upload", type="primary", use_container_width=True)
        if submitted:
            if not uploaded:
                st.warning("Choose at least one file first.")
            else:
                with st.spinner(f"Adding {len(uploaded)} file(s)…"):
                    try:
                        api.upload_collection_items(token, collection_id, uploaded)
                        st.toast("Files added — processing in the background.", icon="⏳")
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))
    else:
        c1, c2 = st.columns([3, 1.3])
        with c1:
            with st.form(f"add_url_form_{collection_id}", clear_on_submit=True):
                url = st.text_input("Add a URL", placeholder="https://example.com/article")
                add_submitted = st.form_submit_button(
                    "Add URL", type="primary", use_container_width=True
                )
            if add_submitted:
                if not url.strip():
                    st.warning("Enter a URL first.")
                else:
                    with st.spinner("Adding URL…"):
                        try:
                            api.add_url_item(token, collection_id, url.strip())
                            st.toast("URL added — processing in the background.", icon="⏳")
                            st.rerun()
                        except RuntimeError as e:
                            st.error(str(e))
        with c2:
            st.markdown("<div style='height:1.85rem'></div>", unsafe_allow_html=True)
            if st.button("🔍 Search", key=f"search_open_{collection_id}", use_container_width=True):
                st.session_state.show_search_modal = collection_id
                st.rerun()

        if st.session_state.get("show_search_modal") == collection_id:
            render_search_modal(token, collection_id)


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

    with st.container(height=SECTION_HEIGHT):
        if collections:
            for col in collections:
                col_id   = col["id"]
                col_name = col["name"]
                col_type = col["type"]
                color    = _TYPE_COLOR.get(col_type, "#9B97C9")
                icon     = _TYPE_ICON.get(col_type, "📦")

                c_info, c_del = st.columns([4, 0.6])
                with c_info:
                    st.markdown(
                        f"<span style='font-size:.9rem; font-weight:600;'>{col_name}</span> "
                        f"<span style='background:{color}22; color:{color}; border:1px solid {color}55;"
                        f"border-radius:8px; padding:1px 7px; font-size:.72rem;'>"
                        f"{icon} {col_type}</span>",
                        unsafe_allow_html=True,
                    )
                with c_del:
                    if st.button("", icon="❌", key=f"del_col_{col_id}", help=f"Delete {col_name}",
                                 use_container_width=True):
                        st.session_state[f"confirm_del_col_{col_id}"] = True
                        st.rerun()

                if st.session_state.get(f"confirm_del_col_{col_id}"):
                    st.warning(f"Delete **{col_name}** and all its files?")
                    dc1, dc2 = st.columns(2)
                    with dc1:
                        if st.button("Yes", key=f"yes_col_{col_id}",
                                     type="primary", use_container_width=True):
                            try:
                                api.delete_collection(token, col_id)
                                del st.session_state[f"confirm_del_col_{col_id}"]
                                st.toast("Collection deleted.", icon="❌")
                                st.rerun()
                            except RuntimeError as e:
                                st.error(str(e))
                    with dc2:
                        if st.button("No", key=f"no_col_{col_id}", use_container_width=True):
                            del st.session_state[f"confirm_del_col_{col_id}"]
                            st.rerun()

                with st.expander("Files", expanded=False):
                    _collection_items(token, col_id, col_type)

                st.markdown(
                    "<hr style='border-color:#2A2D3E; margin:.4rem 0;'>",
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


_NODE_LABELS = {
    "router":       "🧭 Deciding if I need to search your sources…",
    "refine_query": "✏️ Refining your question…",
    "retrieve":     "🔎 Searching your sources…",
    "validate":     "🧐 Checking if I found enough…",
    "generate":     "✍️ Writing the answer…",
}


def _handle_input(token: str, messages_box):
    """
    Called inside the center column, right after the fixed-height messages
    container — placing st.chat_input() inside a column makes it render
    inline instead of pinned to the full page width, so it naturally lands
    just below the messages box: narrow (matching the column width) and,
    since both live inside the same outer bordered card (see render()),
    reads as attached to the bottom of that section.

    messages_box is the container _chat_area() rendered history into. The
    new user turn and the live node-progress / final answer are written
    directly into that same container as they happen, so the query appears
    the instant it's sent and the progress shows up where the reply will
    land — no waiting for a rerun to see any of it.
    """
    chat_id = st.session_state.get("active_chat_id")
    if not chat_id:
        return

    prompt = st.chat_input("Ask anything…")
    if not prompt:
        return

    load_chat_history(chat_id)
    append_message(chat_id, "user", prompt)

    reply_slot = None
    if messages_box is not None:
        with messages_box:
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                reply_slot = st.empty()
                reply_slot.markdown("_Thinking…_")

    try:
        reply = None
        for event in api.send_message_stream(token, chat_id, prompt):
            etype = event.get("type")
            if etype == "node":
                label = _NODE_LABELS.get(event["node"], f"Running {event['node']}…")
                if reply_slot is not None:
                    reply_slot.markdown(f"_{label}_")
            elif etype == "done":
                reply = event.get("answer") or "⚠️ The model did not return a response."
                if reply_slot is not None:
                    reply_slot.markdown(reply)
            elif etype == "error":
                raise RuntimeError(event.get("detail", "Unknown error."))

        if reply is None:
            raise RuntimeError("No response was received from the server.")
        append_message(chat_id, "assistant", reply)

    except RuntimeError as e:
        if reply_slot is not None:
            reply_slot.markdown(f"⚠️ {e}")
        history = st.session_state.chat_histories.get(chat_id, [])
        if history and history[-1]["role"] == "user":
            history.pop()
        st.error(f"⚠️ {e}")

    st.rerun()


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
            messages_box = _chat_area()
            _handle_input(token, messages_box)

    with right:
        _collections_panel(token, project_id)