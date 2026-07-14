from datetime import datetime, timezone

import streamlit as st

from frontend import services as api
from frontend.pages.workspace._shared import (
    CHAT_SECTION_HEIGHT,
    _RETRIEVAL_MODE_HELP,
    _RETRIEVAL_MODE_OPTIONS,
)
from frontend.utils.session import append_message, load_chat_history


def _chat_area():
    """Renders the message list. Returns (messages_box, empty_placeholder) —
    messages_box so _handle_input can write new turns directly into it in
    real time, and empty_placeholder (an st.empty() slot, or None if the
    chat already has history) so _handle_input can clear the "No messages
    yet" notice before writing the first real messages into the same
    container, instead of it staying stacked above them."""
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
        return None, None

    st.markdown(
        f"<p style='color:#9B97C9; font-size:.85rem; margin-bottom:.8rem;'>"
        f"Chat: <strong style='color:#E8E8F0;'>{chat_name}</strong></p>",
        unsafe_allow_html=True,
    )

    history = load_chat_history(chat_id)

    messages_box = st.container(height=CHAT_SECTION_HEIGHT, border=False)
    empty_placeholder = None
    with messages_box:
        if not history:
            empty_placeholder = st.empty()
            empty_placeholder.markdown(
                "<div style='text-align:center; padding:3rem 1rem; color:#6B6E8A;'>"
                "<p>No messages yet. Type below to start the conversation.</p></div>",
                unsafe_allow_html=True,
            )
        else:
            for msg in history:
                with st.chat_message(msg["role"]):
                    st.markdown(msg["content"])

    return messages_box, empty_placeholder


_NODE_LABELS = {
    "router":       "🧭 Deciding if I need to search your sources…",
    "refine_query": "✏️ Refining your question…",
    "retrieve":     "🔎 Searching your sources…",
    "rerank":       "📊 Ranking the most relevant chunks…",
    "validate":     "🧐 Checking if I found enough…",
    "generate":     "✍️ Writing the answer…",
}


class ChatError(RuntimeError):
    """Raised for SSE 'error' events from the chat stream. Carries the
    backend's structured fields (when present) alongside the plain-text
    detail, so specific error types (e.g. quota_exceeded) can be rendered
    with a dedicated UI instead of generic error text."""

    def __init__(self, detail: str, code: str | None = None, **extra):
        super().__init__(detail)
        self.code = code
        self.extra = extra


def _quota_exceeded_card(e: "ChatError") -> str:
    """A dedicated, readable card for the daily-quota-exceeded error —
    distinct from generic error text so it's unmistakable what happened
    and when the user can chat again."""
    used = e.extra.get("used")
    limit = e.extra.get("limit")
    reset_at = e.extra.get("reset_at")

    reset_line = ""
    if reset_at:
        try:
            reset_dt = datetime.fromisoformat(reset_at)
            now = datetime.now(timezone.utc)
            remaining = reset_dt - now
            total_minutes = max(int(remaining.total_seconds() // 60), 0)
            hours, minutes = divmod(total_minutes, 60)
            reset_line = (
                f"<div style='margin-top:8px; font-size:.82rem; color:#B9B6D9;'>"
                f"Resets at <b style='color:#E8E8F0;'>{reset_dt.strftime('%Y-%m-%d %H:%M')} UTC</b>"
                f" &nbsp;•&nbsp; in <b style='color:#E8E8F0;'>{hours}h {minutes}m</b>"
                f"</div>"
            )
        except (ValueError, TypeError):
            pass

    usage_line = ""
    if used is not None and limit is not None and limit > 0:
        pct = min(int(used / limit * 100), 100)
        usage_line = (
            f"<div style='margin-top:10px;'>"
            f"<div style='background:#2A2D3E; border-radius:6px; height:8px; overflow:hidden;'>"
            f"<div style='background:#F5A623; width:{pct}%; height:100%;'></div>"
            f"</div>"
            f"<div style='margin-top:4px; font-size:.78rem; color:#9B97C9;'>"
            f"{used:,} / {limit:,} tokens used today</div>"
            f"</div>"
        )

    return (
        "<div style='background:#2A1F1A; border:1px solid #F5A623; border-radius:10px; "
        "padding:14px 16px;'>"
        "<div style='display:flex; align-items:center; gap:8px;'>"
        "<span style='font-size:1.2rem;'>⏳</span>"
        "<span style='font-weight:700; color:#F5A623; font-size:.95rem;'>"
        "Daily token quota reached</span>"
        "</div>"
        "<div style='margin-top:6px; font-size:.85rem; color:#E8E8F0; line-height:1.5;'>"
        "You've used all of your daily tokens for today. You can send messages again "
        "once your quota resets."
        "</div>"
        f"{usage_line}"
        f"{reset_line}"
        "</div>"
    )


def _generic_error_card(message: str) -> str:
    """Fallback styled card for any non-quota chat error (network issues,
    both LLM providers down, etc.) — same visual language, different color,
    so it doesn't get mistaken for a quota message."""
    return (
        "<div style='background:#2A1A1A; border:1px solid #E74C3C; border-radius:10px; "
        "padding:14px 16px;'>"
        "<div style='display:flex; align-items:center; gap:8px;'>"
        "<span style='font-size:1.2rem;'>⚠️</span>"
        "<span style='font-weight:700; color:#E74C3C; font-size:.95rem;'>"
        "Something went wrong</span>"
        "</div>"
        f"<div style='margin-top:6px; font-size:.85rem; color:#E8E8F0; line-height:1.5;'>"
        f"{message}</div>"
        "</div>"
    )


def _handle_input(token: str, messages_box, empty_placeholder=None):
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

    empty_placeholder is the "No messages yet" notice's st.empty() slot
    (only set when the chat had no history yet) — cleared right before the
    first real messages are written, so it doesn't stay stacked above them.
    """
    chat_id = st.session_state.get("active_chat_id")
    if not chat_id:
        return

    input_col, mode_col = st.columns([4, 1.15], gap="small")
    with input_col:
        prompt = st.chat_input("Ask anything…")
    with mode_col:
        mode_label = st.selectbox(
            "Retrieval mode",
            options=list(_RETRIEVAL_MODE_OPTIONS.keys()),
            index=0,
            key="retrieval_mode_choice",
            label_visibility="collapsed",
            help=_RETRIEVAL_MODE_HELP,
        )
    retrieval_mode = _RETRIEVAL_MODE_OPTIONS.get(mode_label, "semantic")

    if not prompt:
        return

    load_chat_history(chat_id)
    append_message(chat_id, "user", prompt)

    reply_slot = None
    if messages_box is not None:
        with messages_box:
            if empty_placeholder is not None:
                empty_placeholder.empty()
            with st.chat_message("user"):
                st.markdown(prompt)
            with st.chat_message("assistant"):
                reply_slot = st.empty()
                reply_slot.markdown("_Thinking…_")

    try:
        reply = None
        for event in api.send_message_stream(token, chat_id, prompt, retrieval_mode):
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
                raise ChatError(
                    event.get("detail", "Unknown error."),
                    code=event.get("code"),
                    used=event.get("used"),
                    limit=event.get("limit"),
                    reset_at=event.get("reset_at"),
                )

        if reply is None:
            raise RuntimeError("No response was received from the server.")
        append_message(chat_id, "assistant", reply)
        st.rerun()

    except ChatError as e:
        card_html = _quota_exceeded_card(e) if e.code == "quota_exceeded" else _generic_error_card(str(e))
        if reply_slot is not None:
            reply_slot.markdown(card_html, unsafe_allow_html=True)
        history = st.session_state.chat_histories.get(chat_id, [])
        if history and history[-1]["role"] == "user":
            history.pop()

    except Exception as e:
        card_html = _generic_error_card(str(e))
        if reply_slot is not None:
            reply_slot.markdown(card_html, unsafe_allow_html=True)
        history = st.session_state.chat_histories.get(chat_id, [])
        if history and history[-1]["role"] == "user":
            history.pop()