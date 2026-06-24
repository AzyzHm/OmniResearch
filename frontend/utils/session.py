import streamlit as st


DEFAULTS: dict = {
    "page": "login",
    "token": None,
    "user_id": None,
    "username": None,
    "role": None,
    # Workspace
    "active_project_id": None,
    "active_project_name": None,
    "active_chat_id": None,
    "active_chat_name": None,
    # chat_histories: {chat_id: [{"role": "user"|"assistant", "content": "..."}]}
    "chat_histories": {},
    # active_collections: set of collection_ids selected for the current chat
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
    """Return the message history for a chat (empty list if none)."""
    return st.session_state.chat_histories.get(chat_id, [])