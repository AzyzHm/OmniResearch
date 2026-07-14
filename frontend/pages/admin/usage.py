import pandas as pd
import plotly.express as px
import streamlit as st

from frontend.pages.admin._shared import _metric_card, _plotly_dark_layout
from frontend.services.admin import admin_get_llm_usage, admin_get_search_usage


def render_usage(token: str) -> None:
    st.markdown("#### LLM Token Usage")
    st.caption(
        "Each user has a daily token quota (default 80,000, resets at UTC midnight) "
        "editable per-user in the User Management tab above. This view shows all-time "
        "totals, not remaining quota."
    )

    col_refresh_llm, _ = st.columns([1, 4])
    with col_refresh_llm:
        if st.button("🔄 Refresh", use_container_width=True, key="refresh_llm_usage"):
            st.rerun()

    try:
        llm_data = admin_get_llm_usage(token)
    except RuntimeError as e:
        st.error(f"Failed to load LLM usage: {e}")
        llm_data = {"users": []}

    llm_rows = llm_data.get("users", [])

    if not llm_rows:
        st.info("No LLM usage recorded yet.")
    else:
        total_tokens  = sum(r["total_tokens"] for r in llm_rows)
        total_calls   = sum(r["total_calls"] for r in llm_rows)
        mistral_calls = sum(r["mistral_calls"] for r in llm_rows)

        c1, c2, c3 = st.columns(3)
        with c1: _metric_card("Total Tokens (all users)", f"{total_tokens:,}", color="#6C63FF")
        with c2: _metric_card("Total LLM Calls", total_calls, color="#3498DB")
        with c3: _metric_card(
            "Mistral Fallback Calls", mistral_calls,
            "Gemini quota was hit" if mistral_calls > 0 else "",
            color="#F39C12",
        )

        st.markdown("<br>", unsafe_allow_html=True)

        llm_df = pd.DataFrame(llm_rows)
        display_df = llm_df[[
            "username", "total_calls", "total_tokens",
            "gemini_calls", "gemini_tokens",
            "mistral_calls", "mistral_tokens",
        ]].copy()
        display_df.columns = [
            "Username", "Total Calls", "Total Tokens",
            "Gemini Calls", "Gemini Tokens",
            "Mistral Calls", "Mistral Tokens",
        ]
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        fig = px.bar(
            llm_df.sort_values("total_tokens", ascending=True),
            x="total_tokens",
            y="username",
            orientation="h",
            color_discrete_sequence=["#6C63FF"],
            labels={"total_tokens": "Total Tokens", "username": "User"},
        )
        st.plotly_chart(_plotly_dark_layout(fig), use_container_width=True)

    st.markdown("<hr style='border-color:#2A2D3E; margin:1.2rem 0;'>", unsafe_allow_html=True)

    st.markdown("#### Search Engine Usage")
    st.caption(
        "Tracked in credits, not raw call counts — Tavily's \"advanced\" search "
        "depth costs 2 credits per call (roughly double a normal request); "
        "everything else (Tavily basic/fast/ultra-fast, all Exa calls) is 1 credit."
    )

    col_refresh_search, _ = st.columns([1, 4])
    with col_refresh_search:
        if st.button("🔄 Refresh", use_container_width=True, key="refresh_search_usage"):
            st.rerun()

    try:
        search_data = admin_get_search_usage(token)
    except RuntimeError as e:
        st.error(f"Failed to load search usage: {e}")
        search_data = {"users": []}

    search_rows = search_data.get("users", [])

    if not search_rows:
        st.info("No search usage recorded yet.")
        return

    total_credits = sum(r["total_credits"] for r in search_rows)
    tavily_credits = sum(r["tavily_credits"] for r in search_rows)
    exa_credits = sum(r["exa_credits"] for r in search_rows)

    c1, c2, c3 = st.columns(3)
    with c1: _metric_card("Total Credits", total_credits, color="#6C63FF")
    with c2: _metric_card("Tavily Credits", tavily_credits, color="#3498DB")
    with c3: _metric_card("Exa Credits", exa_credits, color="#2ECC71")

    st.markdown("<br>", unsafe_allow_html=True)

    search_df = pd.DataFrame(search_rows)
    display_df = search_df[[
        "username", "total_credits", "total_calls",
        "tavily_credits", "tavily_calls",
        "exa_credits", "exa_calls",
    ]].copy()
    display_df.columns = [
        "Username", "Total Credits", "Total Calls",
        "Tavily Credits", "Tavily Calls",
        "Exa Credits", "Exa Calls",
    ]
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    fig = px.bar(
        search_df.sort_values("total_credits", ascending=True),
        x="total_credits",
        y="username",
        orientation="h",
        color_discrete_sequence=["#3498DB"],
        labels={"total_credits": "Search Credits", "username": "User"},
    )
    st.plotly_chart(_plotly_dark_layout(fig), use_container_width=True)