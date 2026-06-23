import re
import streamlit as st
from frontend.utils.api_client import register


def _password_strength(pw: str) -> tuple[int, str, str]:
    """Return (score 0-4, label, css_color)."""
    score = 0
    if len(pw) >= 8:  score += 1
    if re.search(r"[A-Z]", pw): score += 1
    if re.search(r"\d", pw):     score += 1
    if re.search(r"[^A-Za-z0-9]", pw): score += 1
    labels = ["Too short", "Weak", "Fair", "Good", "Strong"]
    colors = ["#E74C3C", "#E74C3C", "#F39C12", "#2ECC71", "#6C63FF"]
    return score, labels[score], colors[score]


def render():
    # ── Header ────────────────────────────────────────────────────────────────
    st.markdown(
        """
        <div style='text-align:center; padding: 2rem 0 1rem;'>
            <h1 style='font-size:2.4rem; margin-bottom:0;'>
                🔬 OmniResearch
            </h1>
            <p style='color:#9B97C9; margin-top:.3rem; font-size:1.05rem;'>
                Create your account
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Card ──────────────────────────────────────────────────────────────────
    col_l, card, col_r = st.columns([1, 1.6, 1])
    with card:
        st.markdown(
            "<h3 style='text-align:center; margin-bottom:1.4rem;'>Sign Up</h3>",
            unsafe_allow_html=True,
        )

        username = st.text_input(
            "Username",
            placeholder="letters, digits, _ and - only",
            key="reg_user",
        )
        password = st.text_input(
            "Password",
            type="password",
            placeholder="Min. 8 characters",
            key="reg_pass",
        )
        confirm = st.text_input(
            "Confirm Password",
            type="password",
            placeholder="Repeat your password",
            key="reg_confirm",
        )

        # Live password-strength indicator
        if password:
            score, label, color = _password_strength(password)
            pct = int(score / 4 * 100)
            st.markdown(
                f"""
                <div style='margin:.3rem 0 .8rem;'>
                    <div style='background:#2A2D3E; border-radius:4px; height:6px;'>
                        <div style='width:{pct}%; background:{color}; height:6px;
                                    border-radius:4px; transition:width .3s;'></div>
                    </div>
                    <p style='color:{color}; font-size:.8rem; margin:.2rem 0 0;'>
                        Strength: {label}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("<div style='height:.5rem'></div>", unsafe_allow_html=True)

        if st.button("Create Account →", use_container_width=True, type="primary"):
            # Client-side validation
            errors = []
            if not username:
                errors.append("Username is required.")
            if not password:
                errors.append("Password is required.")
            elif len(password) < 8:
                errors.append("Password must be at least 8 characters.")
            if password != confirm:
                errors.append("Passwords do not match.")

            if errors:
                for e in errors:
                    st.error(e)
                return

            with st.spinner("Creating your account…"):
                try:
                    result = register(username, password)
                except RuntimeError as e:
                    st.error(str(e))
                    return

            st.success("✅ " + result["message"])
            st.info("You will be able to sign in once an administrator approves your account.")

            import time; time.sleep(2)
            st.session_state.page = "login"
            st.rerun()

        st.markdown(
            "<hr style='border-color:#2A2D3E; margin:1.4rem 0;'>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='text-align:center; color:#9B97C9; font-size:.9rem;'>"
            "Already have an account?</p>",
            unsafe_allow_html=True,
        )
        if st.button("Back to Sign In", use_container_width=True):
            st.session_state.page = "login"
            st.rerun()