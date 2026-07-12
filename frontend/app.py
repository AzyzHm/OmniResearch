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

st.markdown("""
<style>
    [data-testid="stSidebarNav"], #MainMenu, footer, header { display:none !important; }

    .block-container {
        padding-top: 1rem !important;
        padding-bottom: 1rem !important;
    }

    div[data-testid="InputInstructions"] {
        display: none !important;
    }

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

    /* Retrieval-mode dropdown next to the chat input — match its height and
       vertically center both in their shared row, since stChatInput and a
       stSelectbox don't share the same natural height by default. */
    div[data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]) {
        align-items: center !important;
    }
    div[data-testid="stHorizontalBlock"]:has([data-testid="stChatInput"]) [data-testid="stSelectbox"] > div > div {
        min-height: 52px !important;
        display: flex !important;
        align-items: center !important;
        background: #1A1D2E !important;
        border: 1px solid #3A3D5E !important;
        border-radius: 10px !important;
    }
    [data-testid="stChatInput"] {
        min-height: 52px !important;
    }

    /* Tabs */
    button[data-baseweb="tab"] { font-weight: 600; font-size: .95rem; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #6C63FF !important; }

    /* Dataframe */
    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] {
        background-color: #6C63FF !important;
        border-color: #6C63FF !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"]:focus-visible {
        box-shadow: 0 0 0 0.2rem rgba(108, 99, 255, .35) !important;
    }
    div[data-testid="stSlider"] [data-baseweb="slider"] > div > div {
        background: #6C63FF !important;
    }
    div[data-testid="stThumbValue"] { color: #6C63FF !important; }
    div[data-testid="stTickBarMin"], div[data-testid="stTickBarMax"] { color: #9B97C9 !important; }

    hr { border-color: #2A2D3E !important; }

    /* Column gap for workspace */
    [data-testid="column"] { padding: 0 .5rem; }
</style>
""", unsafe_allow_html=True)

init()

def _route():
    page = st.session_state.page

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