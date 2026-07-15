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
- [Testing](#testing)

---

## Overview

A single Streamlit app acting as a lightweight SPA: one entry point (`app.py`) reads `st.session_state.page` and renders whichever page function matches, rather than using Streamlit's native multi-page file-based routing. All backend communication goes through a `requests`-based service layer — the frontend never talks to Supabase, ChromaDB, or any LLM/search provider directly.

Both the `admin` and `workspace` pages are structured as Python packages rather than single files, each with an `__init__.py` that exposes a `render()` function — the rest of the app imports them exactly the same way it would a plain module (`from frontend.pages.admin import render`).

---

## Tech Stack

| Concern | Technology |
|---|---|
| UI framework | Streamlit |
| HTTP client | `requests`, with a shared `Session` + retry policy |
| Data display | `pandas`, `plotly` (admin dashboard charts) |
| Streaming | Server-Sent Events consumed via `requests(stream=True)` + manual line parsing |
| Auto-refresh | `streamlit-autorefresh`, used for collection items still mid-processing |
| Testing | `pytest`, with `unittest.mock.MagicMock` patches — see [Testing](#testing) |

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
│   └── admin.py                 # user management, role changes, token limits, logs, stats, usage
├── components/
│   └── search_modal.py          # web search dialog (Tavily/Exa), used by urls collections
├── utils/
│   ├── config.py                # API_BASE, _TIMEOUT
│   └── session.py               # session_state DEFAULTS + navigation/chat-history helpers
├── pages/
│   ├── login.py
│   ├── signup.py
│   ├── projects.py               # project list / create / rename / delete
│   ├── workspace/                # the main 3-panel view: chats / chat / sources
│   │   ├── __init__.py           # render() — page shell: top bar + 3-column layout
│   │   ├── _shared.py            # constants shared across the three panels
│   │   ├── chats_panel.py        # left panel: chat list, create/rename/delete
│   │   ├── chat_area.py          # center panel: message display, chat input, SSE handling
│   │   └── collections_panel.py  # right panel: sources list, item management, ingestion UI
│   └── admin/                    # admin dashboard: overview / users / logs / usage
│       ├── __init__.py           # render() — page shell: header, sign-out, tab bar
│       ├── _shared.py            # _metric_card, _badge, _plotly_dark_layout
│       ├── overview.py           # Overview tab
│       ├── users.py              # User Management tab
│       ├── logs.py               # Login Logs tab
│       └── usage.py              # Usage tab
└── tests/                        # pytest suite for the services layer — see Testing
    ├── conftest.py
    ├── test_auth.py
    ├── test_projects.py
    ├── test_chats.py
    ├── test_collections.py
    ├── test_search.py
    ├── test_admin.py
    └── test_base.py
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
        if st.session_state.get("role") not in ("admin", "superadmin"):
            st.error(...); st.session_state.page = "login"; st.rerun()
        ...
```

Each page module is imported lazily, inside the matching branch — not at the top of `app.py` — so a page's own imports (and any side effects) only run when that page is actually about to render. This applies identically whether the page is a single module (`login.py`) or a package (`workspace/`, `admin/`) — Python resolves `from frontend.pages.workspace import render` the same way either way.

Both the `admin` role and the `superadmin` role can reach the admin page; what each of them can actually do once there differs — see [Pages → admin](#adminadminpy) and the User Management tab below.

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
    "active_collections": set(),
}
```

`role` holds one of `"user"`, `"admin"`, or `"superadmin"` — set once at login from the JWT's role claim and read wherever the UI needs to branch on it (the admin page guard in `app.py`, and the per-tab visibility logic in `pages/admin/users.py`).

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

Beyond `DEFAULTS`, several pages use ad hoc `st.session_state` keys scoped with an f-string suffix for per-widget or per-entity state — e.g. `f"confirm_del_chat_{chat_id}"` (delete confirmation flags), `f"item_toggle_{collection_id}_{item_id}"` (collection item checkboxes), `f"confirm_del_{user_id}"` (admin user-deletion confirmation), `show_search_modal` (which collection's search dialog is open), `logs_loaded` (whether the admin Login Logs tab has been triggered to load), `retrieval_mode_choice` (the workspace's retrieval-mode dropdown). These are set with `st.session_state.setdefault(...)` at first use rather than being pre-declared in `DEFAULTS`, since their keys depend on runtime IDs.

---

## Services Layer (API Client)

Split into `frontend/services/`, one file per backend route group.

**`base.py`** holds everything shared:
- `_session`: one `requests.Session()` with a retry policy (3 retries, backoff, retries on 502/503/504) reused across every domain module — not recreated per call.
- `_call(method, path, *, token, json, params)`: the standard JSON request wrapper. Raises `RuntimeError(detail)` on any 4xx/5xx or network failure, so pages can do `except RuntimeError as e: st.error(str(e))` uniformly.
- `_call_multipart(...)`: same error handling, but for file uploads — deliberately does **not** set a `Content-Type` header, letting `requests` generate the correct multipart boundary itself.

Every domain file imports `_call`/`_call_multipart` from `base.py` and exposes plain functions matching one backend endpoint each (`login`, `list_chats`, `create_collection`, `admin_get_stats`, etc). None of them talk to `requests` directly except `chats.py`'s `send_message_stream`, which needs `stream=True` and a `text/event-stream` `Accept` header that the shared JSON-oriented `_call` doesn't support, so it calls `_session` directly.

Both `send_message` and `send_message_stream` (`chats.py`) take a `retrieval_mode` argument (`"semantic"` / `"keyword"` / `"hybrid"`, defaulting to `"semantic"`) and forward it in the request body's `retrieval_mode` field, alongside the message itself.

`admin.py` additionally exposes `admin_change_role` (promote/demote between `user` and `admin`, calling `PUT /admin/users/{id}/role`) and `admin_update_token_limit` (calling `PUT /admin/users/{id}/token-limit`) — used by the User Management tab's role and quota controls respectively.

**`services/__init__.py`** re-exports most functions from most submodules, so pages can use one flat import:

```python
from frontend import services as api
api.list_chats(token, project_id)
api.create_collection(token, project_id, name, col_type)
```

`login.py`, `signup.py`, and the `admin/` package's tab modules import directly from the specific submodule instead (`from frontend.services.auth import login`, `from frontend.services.admin import admin_update_token_limit`) since they only ever call functions from one domain — this makes it obvious at a glance where those calls live, and works regardless of whether that particular function happens to be included in `services/__init__.py`'s re-export list, since importing a submodule attribute directly doesn't go through the parent package's `__all__`.

**Note on import cost**: importing *any* submodule (e.g. `frontend.services.admin`) always executes `services/__init__.py` first, since Python must initialize a parent package before its submodules — so there's no actual difference in what gets loaded into memory between the flat-alias style and the direct-submodule style. The choice between them is purely about readability at the call site, not performance.

---

## Pages

### `login.py` / `signup.py`
Centered card layout (`st.columns([1, 1.6, 1])`, form in the middle column), narrow centered buttons (a further nested `st.columns([1, 1.4, 1])` split so the button doesn't span the whole card width). Signup includes a live password-strength meter (regex-based scoring, no API call). On successful login, the role claim from the token routes straight to `admin` for both `admin` and `superadmin` roles, or `projects` for a regular `user`.

### `projects.py`
Grid of project cards; create/rename/delete. Selecting a project calls `session.open_project(...)` and navigates to `workspace`.

### `workspace/`
The main view — three panels side by side (`st.columns([1.3, 3.8, 1.8])`), each implemented in its own module:

| Panel | Module | Contents |
|---|---|---|
| Left (chats) | `chats_panel.py` | Chat list, rename/delete, "Start a Chat" |
| Center (chat) | `chat_area.py` | Message history + input, wrapped together in one bordered card |
| Right (sources) | `collections_panel.py` | Collections, per-item checkboxes, file upload, manual URL add, search modal trigger |

`chat_area.py` also holds the retrieval-mode dropdown (Semantic / Keyword / Hybrid, sitting beside the chat input), the SSE-driven live progress display, and the styled error cards (`ChatError`, `_quota_exceeded_card`, `_generic_error_card`) shown in place of the assistant's reply when something goes wrong instead of a plain error string. See [Key UI/UX Patterns](#key-uiux-patterns) below for the specific rendering tricks these rely on.

### `admin/`
Four tabs, one module each:

| Tab | Module | Contents |
|---|---|---|
| Overview | `overview.py` | Metric cards + recent logins table |
| User Management | `users.py` | Registered users, approve/promote/demote/delete, daily token limit editor |
| Login Logs | `logs.py` | Filterable table + Plotly bar chart of logins per day |
| Usage | `usage.py` | Per-user LLM token usage and search credits, tables + horizontal bar charts |

**Role hierarchy affects what each tab shows:**
- A **regular `admin`** only ever sees `user`-role accounts across every tab — never themselves, other admins, or the super admin. They can approve, delete, and edit the daily token limit for those accounts, but cannot promote or demote anyone (the Promote/Demote button doesn't render for them at all).
- The **`superadmin`** sees every account except their own row (both `user` and `admin` roles), can promote/demote between `user` and `admin`, but the daily-token-limit editor only appears for `user`-role rows — not for `admin` rows, since token quotas don't apply to admin accounts.
- The Overview tab's metric cards differ accordingly: a superadmin gets **Total Users / Total Admins / Pending Approval / Total Logins** (4 cards); a regular admin gets **Total Users / Pending Approval / Total Logins** (3 cards, no admin count).

Each tab function (`render_overview(token)`, `render_users(token)`, `render_logs(token)`, `render_usage(token)`) is self-contained and only touches its own tab's state — a failure loading one tab's data doesn't affect whether the others render.

---

## Components

### `search_modal.py`
A `@st.dialog(width="large")`-based modal for adding URLs to a `urls`-type collection via Tavily/Exa search, opened from `collections_panel.py` via a `show_search_modal` session flag rather than called unconditionally (Streamlit dialogs must be triggered, not always-rendered).

Notable design points:
- The engine selector lives **outside** any `st.form`, so switching between Tavily/Exa reruns immediately — inside a form, non-submit widgets don't apply until the form is submitted, which previously meant the "depth doesn't apply to Exa" notice only appeared after clicking Search.
- Search results from the **most recent search only** are shown at the top of the results box; anything checked from an *earlier* search that isn't part of the current batch is shown below a "Selected sources" divider instead of disappearing. State is split into `search_latest_{collection_id}` (replaced every search) and `search_selected_items_{collection_id}` (a `{url: result_dict}` map that persists across searches).
- "Select all" / "Deselect all" buttons use `on_click` callbacks (`_select_all`/`_deselect_all`) rather than an `if st.button(...): ...; st.rerun()` pattern — the latter is a known Streamlit issue inside `@st.dialog` functions where it can cause the dialog body to be invoked twice in the same pass, raising `StreamlitDuplicateElementKey` for every widget inside it.
- Result titles are real `<a target="_blank">` links.
- The results list itself is wrapped in `st.container(height=320)`, so the dialog's overall size stays constant no matter how many searches have been run — only that inner box scrolls.

---

## Key UI/UX Patterns

A few non-obvious techniques used throughout the `workspace/` package, worth knowing before modifying it:

**Independently-scrollable sections.** Each of the three workspace panels is wrapped in `st.container(height=N, border=...)`. Streamlit's `st.container(height=...)` renders as a fixed-height, independently-scrollable box — this is what stops the whole page from scrolling as chat/source lists grow. `SECTION_HEIGHT` (chats/sources) and `CHAT_SECTION_HEIGHT` (the chat section specifically) both live in `workspace/_shared.py` and are the two knobs to adjust if these ever need resizing.

**Chat input placement.** `st.chat_input()` normally pins itself to the very bottom of the *entire page*, full width, regardless of where it's called. Placing it inside `st.columns()` changes this — it renders inline instead, at whatever width its column provides. `chat_area.py` calls it in a row alongside the retrieval-mode dropdown, both nested inside the same shared `st.container(border=True)` from `workspace/__init__.py`'s `render()` — so visually it reads as "the input bar at the bottom of the chat card" even though there's no true CSS-level pinning happening; it's just the last thing rendered inside that bordered box.

**Clearing the "No messages yet" placeholder.** When a chat has no history, `_chat_area()` renders its empty-state notice inside an `st.empty()` slot rather than a plain `st.markdown(...)` call, and returns that placeholder object alongside the messages container. `_handle_input()` calls `.empty()` on it right before writing the first real message bubbles into the same container — without this, Streamlit has no way to "un-draw" previously rendered content, so the notice would otherwise stay stacked above the first message instead of being replaced by it.

**Live streaming into the message list.** `_chat_area()` returns the `st.container` object it rendered history into (rather than just rendering and discarding it), so `_handle_input()` can write new content directly into that *same* container as the response streams in: the user's message appears the instant it's sent, then an assistant bubble with a placeholder (`st.empty()`) updates its own text live as each RAG graph node finishes (`_Thinking…_` → `_🔎 Searching your sources…_` → final answer), all before any `st.rerun()` — so nothing waits for a full page refresh to become visible. `st.rerun()` itself is only called on the success path; an error (including the quota-exceeded case) ends the function without rerunning, so the styled error card that was just written into the reply slot stays visible instead of being wiped by an immediate rerun.

**Staged collection-item toggles.** Collection item checkboxes do **not** call the API on every click — each is backed by its own `st.session_state` key, and checking/unchecking many of them just updates local state. Only clicking "Save Changes" bulk-commits every changed item in one `PATCH .../items/bulk` request. "Select All" / "Deselect All" buttons operate on the same staged local state, not live.

**Auto-refresh for processing items.** `collections_panel.py` calls `st_autorefresh(interval=2500, ...)` whenever any item in the currently-rendered collection has `status == "processing"` — file/URL/search-result ingestion runs as a backend background task, so this is what lets a "Processing…" badge flip to "Ready" on its own without the user needing to click anything else. It only fires while something is actually pending; once nothing is processing, no more auto-refresh calls happen for that collection.

---

## Testing

`frontend/tests/` is a `pytest` suite covering the services layer (`frontend/services/`) — one test file per domain module, plus `test_base.py` for the shared HTTP plumbing. 83 test functions across 7 files as of this writing.

**Configuration** (`frontend/Pytest.ini`):
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
```

**Approach**: nothing makes a real network call. Each service function is tested by patching the layer directly beneath it, using fixtures defined in `conftest.py`:

- **`mock_call(monkeypatch)`** — patches `_call` inside a given service module (e.g. `frontend.services.projects`) with a `MagicMock`, returning the mock so a test can both control its return value/side effect and assert exactly how it was called (method, path, `token`, `json`, `params`).
- **`mock_call_multipart(monkeypatch)`** — same idea, for `_call_multipart` (used by `upload_collection_items`).
- **`patched_session_request(monkeypatch)`** — patches the shared `_session.request` method one level deeper, for `test_base.py`'s tests of `_call`/`_call_multipart` themselves (status code handling, error parsing, network exception translation into `RuntimeError`).
- **`patched_session_post(monkeypatch)`** — patches `_session.post` specifically, since `send_message_stream` calls it directly rather than going through `_call`.

**`FakeResponse`** (`conftest.py`) is a minimal stand-in for `requests.Response` — just `status_code`, `.json()`, `.text`, `.content`, and an `iter_lines` callable — enough to drive both the JSON-response path (`_call`) and the SSE line-by-line path (`send_message_stream`) without a real HTTP layer underneath.

Test files, by what they cover:

| File | Covers |
|---|---|
| `test_base.py` | `_call`/`_call_multipart`: success responses, auth header injection, every error status path, network-level exceptions (`ConnectionError`, `Timeout`, generic `RequestException`), multipart uploads |
| `test_auth.py` | `register`, `login` |
| `test_projects.py` | `list_projects`, `create_project`, `rename_project`, `delete_project` |
| `test_chats.py` | Chat CRUD, `get_messages`, `send_message`, and `send_message_stream`'s SSE event parsing |
| `test_collections.py` | Collection + item CRUD, `upload_collection_items` (via a `_FakeUploadedFile` stand-in for Streamlit's `UploadedFile`), bulk item updates |
| `test_search.py` | `search_web`, `add_search_result_items` |
| `test_admin.py` | User listing/approval/role changes/token-limit updates/deletion, logs, stats, and both usage-aggregation endpoints |

Each file organizes its tests into one `Test*` class per function under test (e.g. `TestListProjects`, `TestSendMessageStream`), matching `Pytest.ini`'s `python_classes = Test*` convention.