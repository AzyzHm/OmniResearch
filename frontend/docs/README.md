# OmniResearch — Frontend Documentation

Streamlit frontend for OmniResearch. This document covers the **frontend only** — for backend architecture, the RAG graph, database schema, and API reference, see `backend/docs/README.md`.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Configuration](#configuration)
- [Routing](#routing)
- [Session State](#session-state)
- [Services Layer (API Client)](#services-layer-api-client)
- [Pages](#pages)
- [Components](#components)
- [Key UI/UX Patterns](#key-uiux-patterns)
- [Known Limitations & Cleanup Items](#known-limitations--cleanup-items)

---

## Overview

A single Streamlit app acting as a lightweight SPA: one entry point (`app.py`) reads `st.session_state.page` and renders whichever page function matches, rather than using Streamlit's native multi-page file-based routing. All backend communication goes through a `requests`-based service layer — the frontend never talks to Supabase, ChromaDB, or any LLM/search provider directly.

---

## Tech Stack

| Concern | Technology |
|---|---|
| UI framework | Streamlit |
| HTTP client | `requests`, with a shared `Session` + retry policy |
| Data display | `pandas`, `plotly` (admin dashboard charts) |
| Streaming | Server-Sent Events consumed via `requests(stream=True)` + manual line parsing |

---

## Project Structure

```
frontend/
├── app.py                       # entry point: global CSS, session init, page routing
├── services/                    # API client, split by domain (mirrors backend routes)
│   ├── __init__.py              # flat re-export: `from frontend import services as api`
│   ├── base.py                  # _call, _call_multipart, shared _session — all HTTP plumbing
│   ├── auth.py                  # register, login
│   ├── projects.py              # project CRUD
│   ├── chats.py                 # chat CRUD, message history, send_message(_stream)
│   ├── collections.py           # collection + item CRUD, manual URL add
│   ├── search.py                # search_web, add_search_result_items
│   └── admin.py                 # user management, logs, stats, usage monitoring
├── components/
│   └── search_modal.py          # web search dialog (Tavily/Exa), used by urls collections
├── utils/
│   ├── config.py                # API_BASE, _TIMEOUT
│   └── session.py               # session_state DEFAULTS + navigation/chat-history helpers
└── pages/
    ├── login.py
    ├── signup.py
    ├── projects.py               # project list / create / rename / delete
    ├── workspace.py              # the main 3-section view: chats / chat / sources
    └── admin.py                  # tabs: overview, user management, login logs, usage
```

---

## Configuration

`frontend/utils/config.py`:

```python
API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")   # FastAPI backend URL
_TIMEOUT = 60                                                     # seconds, see note below
```

`_TIMEOUT` applies differently depending on the call type:
- **Regular calls** (`_call` in `services/base.py`): a flat 60s timeout for the whole request.
- **Streaming calls** (`send_message_stream`): with `stream=True`, `requests`' timeout applies *per chunk received*, not to the total response duration — so a multi-step RAG run that takes longer than 60s overall doesn't get killed, as long as no single step individually stalls that long.

---

## Routing

There's no Streamlit multi-page setup (no `pages/` auto-discovery) — `app.py` does it manually:

```python
def _route():
    page = st.session_state.page

    if not st.session_state.token and page not in ("login", "signup"):
        st.session_state.page = "login"   # force logout redirect
        page = "login"

    if page == "login": ...
    elif page == "signup": ...
    elif page == "projects": ...
    elif page == "workspace":
        if not st.session_state.active_project_id:
            st.session_state.page = "projects"; st.rerun()
        ...
    elif page == "admin":
        if st.session_state.get("role") != "admin":
            st.error(...); st.session_state.page = "login"; st.rerun()
        ...
```

Each page module is imported lazily, inside the matching branch — not at the top of `app.py` — so a page's own imports (and any side effects) only run when that page is actually about to render.

Navigating between pages is just `st.session_state.page = "..."` followed by `st.rerun()`, wrapped in `session.py`'s `go()`, `open_project()`, `select_chat()`, and `logout()` helpers rather than done ad hoc at every call site.

---

## Session State

`frontend/utils/session.py` centralizes every session key in one `DEFAULTS` dict, initialized once via `init()` (called at the top of `app.py`, before routing):

```python
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
    "active_collections": set(),   # legacy — see "Known Limitations" below
}
```

Helper functions:

| Function | Purpose |
|---|---|
| `init()` | Seeds any missing key from `DEFAULTS` — safe to call every rerun |
| `go(page)` | Sets `page` and reruns |
| `open_project(id, name)` | Sets active project, clears active chat/collections, navigates to `workspace` |
| `select_chat(id, name)` | Switches the active chat within the workspace |
| `logout()` | Resets every key back to `DEFAULTS` and navigates to `login` |
| `append_message(chat_id, role, content)` | Appends one message to the in-memory `chat_histories[chat_id]` cache |
| `get_history(chat_id)` | Returns the in-memory cache only (no API call) |
| `load_chat_history(chat_id)` | Returns the in-memory cache if present; otherwise fetches once via the API and caches it. This is what avoids re-fetching message history on every Streamlit rerun |

Beyond `DEFAULTS`, several pages use ad hoc `st.session_state` keys scoped with an f-string suffix for per-widget or per-entity state — e.g. `f"confirm_del_chat_{chat_id}"` (delete confirmation flags), `f"item_toggle_{collection_id}_{item_id}"` (collection item checkboxes — see below), `show_search_modal` (which collection's search dialog is open). These are set with `st.session_state.setdefault(...)` at first use rather than being pre-declared in `DEFAULTS`, since their keys depend on runtime IDs.

---

## Services Layer (API Client)

Originally one 350-line `api_client.py`; split into `frontend/services/` by domain, one file per backend route group.

**`base.py`** holds everything shared:
- `_session`: one `requests.Session()` with a retry policy (3 retries, backoff, retries on 502/503/504) reused across every domain module — not recreated per call.
- `_call(method, path, *, token, json, params)`: the standard JSON request wrapper. Raises `RuntimeError(detail)` on any 4xx/5xx or network failure, so pages can do `except RuntimeError as e: st.error(str(e))` uniformly.
- `_call_multipart(...)`: same error handling, but for file uploads — deliberately does **not** set a `Content-Type` header, letting `requests` generate the correct multipart boundary itself.

Every domain file imports `_call`/`_call_multipart` from `base.py` and exposes plain functions matching one backend endpoint each (`login`, `list_chats`, `create_collection`, `admin_get_stats`, etc). None of them talk to `requests` directly except `chats.py`'s `send_message_stream`, which needs `stream=True` and a `text/event-stream` `Accept` header that the shared JSON-oriented `_call` doesn't support, so it calls `_session` directly.

**`services/__init__.py`** re-exports every function from every submodule, so most pages can keep using one flat import:

```python
from frontend import services as api
api.list_chats(token, project_id)
api.create_collection(token, project_id, name, col_type)
```

A few files (`login.py`, `signup.py`, `admin.py`) import directly from the specific submodule instead (`from frontend.services.auth import login`) since they only ever call functions from one domain — makes it obvious at a glance where those calls live, without needing the flat alias.

**Note on import cost**: importing *any* submodule (e.g. `frontend.services.admin`) always executes `services/__init__.py` first, since Python must initialize a parent package before its submodules — so there's no actual difference in what gets loaded into memory between the flat-alias style and the direct-submodule style. The choice between them is purely about readability at the call site, not performance.

---

## Pages

### `login.py` / `signup.py`
Centered card layout (`st.columns([1, 1.6, 1])`, form in the middle column), narrow centered buttons (a further nested `st.columns([1, 1.4, 1])` split so the button doesn't span the whole card width). Signup includes a live password-strength meter (regex-based scoring, no API call).

### `projects.py`
Grid of project cards; create/rename/delete. Selecting a project calls `session.open_project(...)` and navigates to `workspace`.

### `workspace.py`
The main view — three sections side by side (`st.columns([1.3, 3.8, 1.8])`):

| Section | Contents |
|---|---|
| Left (chats) | Chat list, rename/delete, "Start a Chat" |
| Center (chat) | Message history + input, wrapped together in one bordered card |
| Right (sources) | Collections, per-item checkboxes, file upload, manual URL add, search modal trigger |

See [Key UI/UX Patterns](#key-uiux-patterns) below for the specific tricks used to make this feel like a real fixed-layout app rather than a scrolling Streamlit script.

### `admin.py`
Four tabs: **Overview** (metric cards + recent logins), **User Management** (approve/promote/demote/delete), **Login Logs** (filterable table + Plotly bar chart), **Usage** (per-user LLM token usage and search credits, tables + horizontal bar charts, sourced from `admin_get_llm_usage`/`admin_get_search_usage`).

---

## Components

### `search_modal.py`
A `@st.dialog(width="large")`-based modal for adding URLs to a `urls`-type collection via Tavily/Exa search, opened from `workspace.py` via a `show_search_modal` session flag rather than called unconditionally (Streamlit dialogs must be triggered, not always-rendered).

Notable design points:
- The engine selector lives **outside** any `st.form`, so switching between Tavily/Exa reruns immediately — inside a form, non-submit widgets don't apply until the form is submitted, which previously meant the "depth doesn't apply to Exa" notice only appeared after clicking Search.
- Search results from the **most recent search only** are shown at the top of the results box; anything checked from an *earlier* search that isn't part of the current batch is shown below a "Selected sources" divider instead of disappearing. State is split into `search_latest_{collection_id}` (replaced every search) and `search_selected_items_{collection_id}` (a `{url: result_dict}` map that persists across searches).
- Result titles are real `<a target="_blank">` links.
- The results list itself is wrapped in `st.container(height=320)`, so the dialog's overall size stays constant no matter how many searches have been run — only that inner box scrolls.

---

## Key UI/UX Patterns

A few non-obvious techniques used throughout `workspace.py`, worth knowing before modifying it:

**Independently-scrollable sections.** Each of the three workspace sections is wrapped in `st.container(height=N, border=...)`. Streamlit's `st.container(height=...)` renders as a fixed-height, independently-scrollable box — this is what stops the whole page from scrolling as chat/source lists grow. `SECTION_HEIGHT` (chats/sources) and `CHAT_SECTION_HEIGHT` (the chat section specifically) are both defined near the top of `workspace.py` and are the two knobs to adjust if these ever need resizing.

**Chat input placement.** `st.chat_input()` normally pins itself to the very bottom of the *entire page*, full width, regardless of where it's called. Placing it inside `st.columns()` changes this — it renders inline instead, at whatever width its column provides. `workspace.py` calls it right after the messages container, both nested inside one shared `st.container(border=True)` — so visually it reads as "the input bar at the bottom of the chat card" even though there's no true CSS-level pinning happening; it's just the last thing rendered inside that bordered box.

**Live streaming into the message list.** `_chat_area()` returns the `st.container` object it rendered history into (rather than just rendering and discarding it), so `_handle_input()` can write new content directly into that *same* container as the response streams in: the user's message appears the instant it's sent, then an assistant bubble with a placeholder (`st.empty()`) updates its own text live as each RAG graph node finishes (`_Thinking…_` → `_🔎 Searching your sources…_` → final answer), all before any `st.rerun()` — so nothing waits for a full page refresh to become visible.

**Staged collection-item toggles.** Collection item checkboxes do **not** call the API on every click — each is backed by its own `st.session_state` key, and checking/unchecking many of them just updates local state. Only clicking "Save Changes" bulk-commits every changed item in one `PATCH .../items/bulk` request. This exists because the original one-request-per-checkbox design could fire a burst of concurrent requests against the same FastAPI worker if a user rapidly clicked several checkboxes, which was severe enough to interfere with unrelated endpoints (including the chat endpoint) until the page was reloaded. "Select All" / "Deselect All" buttons operate on the same staged local state, not live.

---

## Known Limitations & Cleanup Items

- **`DEFAULTS["active_collections"]`** in `session.py` is a leftover from an earlier whole-collection active/inactive toggle design, since replaced by per-item toggles (see above). It's never read anywhere anymore — safe to remove, just hasn't been done yet.
- **No component tests** — verification throughout development has been manual, screenshot-driven.
- **`_TIMEOUT` is a single flat constant** shared by every non-streaming call; a slow collection upload (large PDF, many chunks) and a slow admin stats fetch share the same 60s ceiling.
- **Search modal's "Selected sources" carry-over section** re-renders full result rows (title, link, preview) for anything selected from a prior search — fine at typical result-list sizes, but not paginated or virtualized if someone ran many large searches in one session.