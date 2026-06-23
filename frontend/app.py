import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import streamlit as st

st.set_page_config(
    page_title="OmniResearch",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* hide default sidebar nav & Streamlit chrome */
    [data-testid="stSidebarNav"], #MainMenu, footer, header { display:none !important; }

    /* ── Auth card wrapper ── */
    div[data-testid="stVerticalBlock"]:has(
        > div > div[data-testid="stTextInput"]
    ) {
        background: #1A1D2E;
        border-radius: 14px;
        padding: 2rem;
        box-shadow: 0 4px 24px rgba(0,0,0,.45);
    }

    /* ── Inputs ── */
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

    /* ── Primary button ── */
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg,#6C63FF,#8B85FF) !important;
        color: #fff !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 600 !important;
        letter-spacing: .03em !important;
        transition: opacity .18s, transform .18s;
    }
    div[data-testid="stButton"] > button[kind="primary"]:hover {
        opacity: .88 !important;
        transform: translateY(-1px);
    }

    /* ── Secondary button ── */
    div[data-testid="stButton"] > button:not([kind="primary"]) {
        border-radius: 8px !important;
        border: 1px solid #3A3D5E !important;
        background: transparent !important;
        transition: border-color .18s;
    }
    div[data-testid="stButton"] > button:not([kind="primary"]):hover {
        border-color: #6C63FF !important;
    }

    /* ── Tabs ── */
    button[data-baseweb="tab"] { font-weight: 600; font-size: .95rem; }
    button[data-baseweb="tab"][aria-selected="true"] { color: #6C63FF !important; }

    /* ── Dataframe ── */
    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }

    /* ── Divider ── */
    hr { border-color: #2A2D3E !important; }
</style>
""", unsafe_allow_html=True)


# ── Session defaults ──────────────────────────────────────────────────────────
for _k, _v in [
    ("page", "login"),
    ("token", None),
    ("user_id", None),
    ("username", None),
    ("role", None),
]:
    if _k not in st.session_state:
        st.session_state[_k] = _v


# ── Router ────────────────────────────────────────────────────────────────────
def _route():
    page = st.session_state.page

    # Guard: unauthenticated users can only see login / signup
    if not st.session_state.token and page not in ("login", "signup"):
        st.session_state.page = "login"
        page = "login"

    if page == "login":
        from frontend.pages.login import render; render()

    elif page == "signup":
        from frontend.pages.signup import render; render()

    elif page == "admin":
        if st.session_state.get("role") != "admin":
            st.error("⛔ Access denied – admin only.")
            st.session_state.page = "login"
            st.rerun()
        from frontend.pages.admin import render; render()

    elif page == "home":
        # Placeholder until the research workspace is built
        st.markdown(f"## 👋 Welcome, **{st.session_state.username}**!")
        st.info("The research workspace is coming in the next sprint. Stay tuned!")
        if st.button("Sign Out"):
            for k in ("token","user_id","username","role"):
                st.session_state[k] = None
            st.session_state.page = "login"
            st.rerun()

    else:
        st.session_state.page = "login"
        st.rerun()


_route()