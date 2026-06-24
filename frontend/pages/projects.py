"""
pages/projects.py – Project dashboard.

Shows all projects belonging to the current user as cards in a grid.
Actions: open, rename (inline), delete (with confirmation).
"""
import streamlit as st
import pandas as pd
from frontend.utils import api_client as api
from frontend.utils.session import logout, open_project

# ── Type badges ───────────────────────────────────────────────────────────────
_TYPE_ICON = {"documents": "📄", "urls": "🔗", "text": "📝"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _load_projects() -> list:
    try:
        return api.list_projects(st.session_state.token) or []
    except RuntimeError as e:
        st.error(str(e))
        return []


def _header():
    c1, c2 = st.columns([5, 1])
    with c1:
        st.markdown(
            f"<h2 style='margin:0'>📁 My Projects</h2>"
            f"<p style='color:#9B97C9; margin:0'>Welcome back, "
            f"<strong>{st.session_state.username}</strong></p>",
            unsafe_allow_html=True,
        )
    with c2:
        if st.button("Sign Out", use_container_width=True):
            logout()
    st.markdown("---")


# ── Create project form ───────────────────────────────────────────────────────

def _create_section():
    with st.expander("➕ New Project", expanded=False):
        with st.form("create_project_form", clear_on_submit=True):
            name = st.text_input("Project name", placeholder="My research project")
            submitted = st.form_submit_button("Create", type="primary", use_container_width=True)
        if submitted:
            if not name.strip():
                st.error("Project name cannot be empty.")
            else:
                try:
                    api.create_project(st.session_state.token, name.strip())
                    st.toast("Project created!", icon="✅")
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))


# ── Individual project card ───────────────────────────────────────────────────

def _project_card(project: dict):
    pid = project["id"]
    name = project["name"]
    created = pd.to_datetime(project["created_at"]).strftime("%d %b %Y")
    updated = pd.to_datetime(project["updated_at"]).strftime("%d %b %Y")

    # State keys
    rename_key  = f"renaming_{pid}"
    confirm_key = f"confirm_del_{pid}"

    with st.container():
        st.markdown(
            f"""
            <div style='background:#1A1D2E; border:1px solid #2A2D3E; border-radius:12px;
                        padding:1.2rem 1.4rem; margin-bottom:.8rem;'>
                <div style='font-size:1.15rem; font-weight:700; color:#E8E8F0;
                            margin-bottom:.2rem;'>📁 {name}</div>
                <div style='color:#6B6E8A; font-size:.8rem;'>
                    Created {created} &nbsp;·&nbsp; Updated {updated}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        col_open, col_rename, col_delete = st.columns([2, 1, 1])

        # Open
        with col_open:
            if st.button("Open →", key=f"open_{pid}", use_container_width=True, type="primary"):
                open_project(pid, name)

        # Rename toggle
        with col_rename:
            if st.button("✏️ Rename", key=f"rename_btn_{pid}", use_container_width=True):
                st.session_state[rename_key] = not st.session_state.get(rename_key, False)
                st.session_state.pop(confirm_key, None)
                st.rerun()

        # Delete toggle
        with col_delete:
            if st.button("🗑️ Delete", key=f"del_btn_{pid}", use_container_width=True):
                st.session_state[confirm_key] = True
                st.session_state.pop(rename_key, None)
                st.rerun()

        # ── Inline rename form ────────────────────────────────────────────────
        if st.session_state.get(rename_key):
            with st.form(f"rename_form_{pid}", clear_on_submit=True):
                new_name = st.text_input("New name", value=name, key=f"new_name_{pid}")
                c_save, c_cancel = st.columns(2)
                with c_save:
                    save = st.form_submit_button("Save", type="primary", use_container_width=True)
                with c_cancel:
                    cancel = st.form_submit_button("Cancel", use_container_width=True)
            if save:
                if not new_name.strip(): # type: ignore
                    st.error("Name cannot be empty.")
                else:
                    try:
                        api.rename_project(st.session_state.token, pid, new_name.strip()) # type: ignore
                        st.toast("Renamed!", icon="✏️")
                        del st.session_state[rename_key]
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))
            if cancel:
                del st.session_state[rename_key]
                st.rerun()

        # ── Delete confirmation ───────────────────────────────────────────────
        if st.session_state.get(confirm_key):
            st.warning(f"⚠️ Delete **{name}**? All chats and collections will be lost.")
            c_yes, c_no = st.columns(2)
            with c_yes:
                if st.button("Confirm Delete", key=f"confirm_yes_{pid}",
                             type="primary", use_container_width=True):
                    try:
                        api.delete_project(st.session_state.token, pid)
                        st.toast("Project deleted.", icon="🗑️")
                        del st.session_state[confirm_key]
                        st.rerun()
                    except RuntimeError as e:
                        st.error(str(e))
            with c_no:
                if st.button("Cancel", key=f"confirm_no_{pid}", use_container_width=True):
                    del st.session_state[confirm_key]
                    st.rerun()

        st.markdown("<div style='height:.4rem'></div>", unsafe_allow_html=True)


# ── Main render ───────────────────────────────────────────────────────────────

def render():
    _header()
    _create_section()
    st.markdown("<br>", unsafe_allow_html=True)

    projects = _load_projects()

    if not projects:
        st.markdown(
            """
            <div style='text-align:center; padding:4rem 0; color:#6B6E8A;'>
                <div style='font-size:3rem;'>📭</div>
                <p style='font-size:1.1rem; margin-top:.5rem;'>No projects yet.</p>
                <p>Use the <strong>New Project</strong> button above to get started.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    # Render cards in a 2-column grid
    left_col, right_col = st.columns(2)
    for i, project in enumerate(projects):
        with left_col if i % 2 == 0 else right_col:
            _project_card(project)