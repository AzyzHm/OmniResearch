import streamlit as st

from frontend.utils import api_client as api

_RESULTS_BOX_HEIGHT = 320


def _existing_urls(token: str, collection_id: str) -> set:
    try:
        items = api.list_collection_items(token, collection_id)
        return {i["name"] for i in items if i["source_type"] == "url"}
    except RuntimeError:
        return set()


def _render_result_row(collection_id: str, r: dict, existing: set, selected_items: dict):
    """One compact, clickable result row with its checkbox."""
    url     = r["url"]
    title   = r.get("title") or url
    content = (r.get("content") or "").strip()
    already = url in existing
    has_content = bool(content)

    cb1, cb2 = st.columns([0.35, 5])
    with cb1:
        checked = st.checkbox(
            "",
            key=f"select_{collection_id}_{url}",
            value=(url in selected_items),
            disabled=already or not has_content,
            label_visibility="collapsed",
        )
        if checked and not already and has_content:
            selected_items[url] = r
        elif not checked and url in selected_items:
            selected_items.pop(url, None)

    with cb2:
        if already:
            note = "<span style='color:#2ECC71;'>✅ already in this collection</span>"
        elif not has_content:
            note = "<span style='color:#F5A623;'>⚠️ no content returned</span>"
        else:
            preview = content[:130] + ("…" if len(content) > 130 else "")
            note = f"<span style='color:#6B6E8A;'>{preview}</span>"

        st.markdown(
            f"<div style='line-height:1.3; margin-bottom:.45rem;'>"
            f"<a href='{url}' target='_blank' rel='noopener noreferrer' "
            f"style='font-size:.82rem; font-weight:600; color:#8B85FF; text-decoration:none;'>"
            f"{title}</a><br>"
            f"<span style='font-size:.72rem;'>{note}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


@st.dialog("🔍 Search the Web", width="large")
def render_search_modal(token: str, collection_id: str):
    latest_key   = f"search_latest_{collection_id}"
    selected_key = f"search_selected_items_{collection_id}"
    existing_key = f"search_existing_{collection_id}"

    st.session_state.setdefault(latest_key, [])
    st.session_state.setdefault(selected_key, {})
    if existing_key not in st.session_state:
        st.session_state[existing_key] = _existing_urls(token, collection_id)

    c1, c2, c3, c4 = st.columns([1, 2.4, 1, 1.2])
    with c1:
        engine = st.selectbox("Engine", ["tavily", "exa"], key=f"engine_{collection_id}")
    with c2:
        query = st.text_input("Search query", key=f"query_{collection_id}")
    with c3:
        num_results = st.slider("Results", 1, 20, 10, key=f"numres_{collection_id}")
    with c4:
        if engine == "tavily":
            search_depth = st.selectbox(
                "Depth",
                ["basic", "advanced", "fast", "ultra-fast"],
                key=f"depth_{collection_id}",
            )
        else:
            search_depth = "basic"
            st.caption("Depth: N/A for Exa")

    sb1, sb2, sb3 = st.columns([2, 1.2, 2])
    with sb2:
        run_search = st.button("Search", type="primary", use_container_width=True,
                                key=f"run_search_{collection_id}")

    if run_search:
        if not query.strip():
            st.warning("Enter a search query first.")
        else:
            with st.spinner("Searching…"):
                try:
                    results = api.search_web(token, engine, query.strip(), num_results, search_depth)
                    deduped: dict = {}
                    for r in results:
                        if r.get("url"):
                            deduped[r["url"]] = r
                    st.session_state[latest_key] = list(deduped.values())
                except RuntimeError as e:
                    st.error(str(e))

    latest_results = st.session_state[latest_key]
    selected_items = st.session_state[selected_key]
    existing       = st.session_state[existing_key]

    latest_urls = {r["url"] for r in latest_results}
    carried_over = [item for url, item in selected_items.items() if url not in latest_urls]

    if latest_results or carried_over:
        with st.container(height=_RESULTS_BOX_HEIGHT):
            if latest_results:
                st.caption(f"{len(latest_results)} result(s) — check the ones to add:")
                for r in latest_results:
                    _render_result_row(collection_id, r, existing, selected_items)

            if carried_over:
                st.markdown(
                    "<hr style='margin:.6rem 0 .5rem; border-color:#2A2D3E;'>"
                    "<p style='font-size:.75rem; color:#9B97C9; text-transform:uppercase; "
                    "letter-spacing:.06em; margin-bottom:.4rem;'>Selected sources</p>",
                    unsafe_allow_html=True,
                )
                for r in carried_over:
                    _render_result_row(collection_id, r, existing, selected_items)
    else:
        st.caption("No searches yet. Run one above.")

    n_selected = len(selected_items)
    b1, b2 = st.columns(2)
    with b1:
        if st.button(
            f"Add {n_selected} Selected", type="primary",
            use_container_width=True, disabled=n_selected == 0,
        ):
            to_add = list(selected_items.values())
            with st.spinner("Adding selected results…"):
                try:
                    response = api.add_search_result_items(token, collection_id, to_add)
                    skipped = response.get("skipped", [])
                    st.session_state.pop(latest_key, None)
                    st.session_state.pop(selected_key, None)
                    st.session_state.pop(existing_key, None)
                    st.session_state.show_search_modal = None
                    added_count = len(response.get("added", []))
                    if skipped:
                        st.toast(
                            f"Added {added_count} result(s). "
                            f"Skipped {len(skipped)} already in this collection.",
                            icon="⚠️",
                        )
                    else:
                        st.toast("Selected results added!", icon="✅")
                    st.rerun()
                except RuntimeError as e:
                    st.error(str(e))
    with b2:
        if st.button("Close", use_container_width=True):
            st.session_state.pop(latest_key, None)
            st.session_state.pop(selected_key, None)
            st.session_state.pop(existing_key, None)
            st.session_state.show_search_modal = None
            st.rerun()