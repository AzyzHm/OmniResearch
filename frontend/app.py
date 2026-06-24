"""
app.py – OmniResearch Streamlit entry point + page router.

Run from the project root:
    streamlit run frontend/app.py
"""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st
from frontend.utils.session import init

st.set_page_config(
    page_title="OmniResearch",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="stSidebarNav"], #MainMenu, footer, header { display:none !important; }

    /* Inputs */
    input[type="text"], input[type="password"] {
        background: #12152A !important;
        border: 1px solid #3A3D5E !important;
        border-radius: 8px !important;
        color: #E8E8F0 !important;
    }
    input[type="text"]:focus, input[type="password"]:focus {
        border-color: #6C63FF !important;
        box-shadow: 0 0 0 2px rgba(108,99,255,.25) !important;
    }

    /* Primary button */
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg,#6C63FF,#8B85FF) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        transition: opacity .18s, transform .18s;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        opacity: .88 !important; transform: translateY(-1px);
    }

    /* Secondary button */
    div[data-testid="stButton"] > button:not([kind="primary"]) {
        border-radius: 8px !important;
        border: 1px solid #3A3D5E !important;
        background: transparent !important;
        transition: border-color .18s;
    }
    div[data-testid="stButton"] > button:not([kind="primary"]):hover {
        border-color: #6C63FF !important;
    }

    /* Chat messages */
    [data-testid="stChatMessage"] {
        background: #1A1D2E !important;
        border-radius: 10px !important;
        border: 1px solid #2A2D3E !important;
        margin-bottom: .5rem !important;
    }

    /* Chat input */
    [data-testid="stChatInput"] textarea {
        background: #1A1D2E !important;
        border: 1px solid #3A3D5E !important;
        border-radius: 10px !important;
    }

    /* Tabs */
    button[data-baseweb="tab"] { font-weight: 600; font-size: .95rem; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #6C63FF !important; }

    /* Dataframe */
    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

    hr { border-color: #2A2D3E !important; }

    /* Column gap for workspace */
    [data-testid="column"] { padding: 0 .5rem; }
</style>
""", unsafe_allow_html=True)

# ── Session init ──────────────────────────────────────────────────────────────
init()

# ── Router ────────────────────────────────────────────────────────────────────
def _route():
    page = st.session_state.page

    # Guard: unauthenticated users → login or signup only
    if not st.session_state.token and page not in ("login", "signup"):
        st.session_state.page = "login"
        page = "login"

    if page == "login":
        from frontend.pages.login import render; render()

    elif page == "signup":
        from frontend.pages.signup import render; render()

    elif page == "projects":
        from frontend.pages.projects import render; render()

    elif page == "workspace":
        if not st.session_state.active_project_id:
            st.session_state.page = "projects"
            st.rerun()
        from frontend.pages.workspace import render; render()

    elif page == "admin":
        if st.session_state.get("role") != "admin":
            st.error("⛔ Access denied – admin only.")
            st.session_state.page = "login"
            st.rerun()
        from frontend.pages.admin import render; render()

    else:
        st.session_state.page = "login"
        st.rerun()


_route()