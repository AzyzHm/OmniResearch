import streamlit as st
from frontend.services.auth import login


def render():
    st.markdown(
        """
        <div style='text-align:center; padding: 1rem 0 .5rem;'>
            <h1 style='font-size:2.4rem; margin-bottom:0;'>
                🔬 OmniResearch
            </h1>
            <p style='color:#9B97C9; margin-top:.3rem; font-size:1.05rem;'>
                AI-powered research & document analysis platform
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col_l, card, col_r = st.columns([1, 1.6, 1])
    with card:
        st.markdown(
            "<h3 style='text-align:center; margin-bottom:1.4rem;'>Sign In</h3>",
            unsafe_allow_html=True,
        )

        username = st.text_input("Username", placeholder="your_username", key="login_user")
        password = st.text_input("Password", type="password", placeholder="••••••••", key="login_pass")

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        b_l, b_mid, b_r = st.columns([1, 1.4, 1])
        with b_mid:
            if st.button("Sign In →", use_container_width=True, type="primary"):
                if not username or not password:
                    st.error("Please fill in both fields.")
                else:
                    with st.spinner("Authenticating…"):
                        try:
                            token_data = login(username, password)
                        except RuntimeError as e:
                            st.error(str(e))
                            return

                    st.session_state.token      = token_data["access_token"]
                    st.session_state.user_id    = token_data["user_id"]
                    st.session_state.username   = token_data["username"]
                    st.session_state.role       = token_data["role"]
                    st.session_state.page       = "admin" if token_data["role"] in ("admin", "superadmin") else "projects"
                    st.rerun()

        st.markdown(
            "<hr style='border-color:#2A2D3E; margin:1.4rem 0;'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#9B97C9; font-size:.9rem;'>"
            "Don't have an account?</p>",
            unsafe_allow_html=True,
        )
        n_l, n_mid, n_r = st.columns([1, 1.4, 1])
        with n_mid:
            if st.button("Create Account", use_container_width=True):
                st.session_state.page = "signup"
                st.rerun()