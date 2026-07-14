import streamlit as st
from streamlit_autorefresh import st_autorefresh

from frontend.components.search_modal import render_search_modal
from frontend import services as api
from frontend.pages.workspace._shared import (
    COLLECTION_TYPES,
    SECTION_HEIGHT,
    _STATUS_BADGE,
    _TYPE_COLOR,
    _TYPE_ICON,
    _UPLOADABLE_TYPES,
)


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