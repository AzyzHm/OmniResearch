import streamlit as st


DEFAULTS: dict = {
    "page": "login",
    "token": None,
    "user_id": None,
    "username": None,
    "role": None,
    "active_project_id": None,
    "active_project_name": None,
    "active_chat_id": None,
    "active_chat_name": None,
    "chat_histories": {},
    "active_collections": set(),
}


def init() -> None:
    """Initialise all session keys with their defaults if not already set."""
    for key, value in DEFAULTS.items():
        if key not in st.session_state:
            st.session_state[key] = value


def go(page: str) -> None:
    """Navigate to a page and rerun."""
    st.session_state.page = page
    st.rerun()


def open_project(project_id: str, project_name: str) -> None:
    """Set the active project and navigate to the workspace."""
    st.session_state.active_project_id = project_id
    st.session_state.active_project_name = project_name
    st.session_state.active_chat_id = None
    st.session_state.active_chat_name = None
    st.session_state.active_collections = set()
    go("workspace")


def select_chat(chat_id: str, chat_name: str) -> None:
    """Switch the active chat inside the workspace."""
    st.session_state.active_chat_id = chat_id
    st.session_state.active_chat_name = chat_name


def logout() -> None:
    """Clear all session state and return to login."""
    for key, value in DEFAULTS.items():
        st.session_state[key] = value
    st.session_state.chat_histories = {}
    go("login")


def append_message(chat_id: str, role: str, content: str) -> None:
    """Add a message to the in-memory history for a chat."""
    histories: dict = st.session_state.chat_histories
    if chat_id not in histories:
        histories[chat_id] = []
    histories[chat_id].append({"role": role, "content": content})


def get_history(chat_id: str) -> list[dict]:
    """Return the in-memory message history for a chat (empty list if none)."""
    return st.session_state.chat_histories.get(chat_id, [])


def load_chat_history(chat_id: str) -> list[dict]:
    """
    Return the message history for a chat.

    On first access, fetches from the API and caches in session state.
    Subsequent calls within the same session return the cached list directly,
    avoiding a round-trip on every Streamlit rerun.
    """
    histories: dict = st.session_state.chat_histories
    if chat_id not in histories:
        from frontend.utils import api_client as api  # local import avoids circular deps
        token: str = st.session_state.token or ""
        try:
            raw = api.get_messages(token, chat_id)
            histories[chat_id] = [
                {"role": m["role"], "content": m["content"]} for m in raw
            ]
        except RuntimeError:
            histories[chat_id] = []
    return histories[chat_id]