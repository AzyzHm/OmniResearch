# OmniResearch — Backend Documentation

AI-powered research and document analysis platform. This document covers the **backend only** (FastAPI + Supabase + ChromaDB + LangGraph). Frontend documentation lives separately.

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Environment Variables](#environment-variables)
- [Running the Backend](#running-the-backend)
- [Database Schema](#database-schema)
- [Authentication](#authentication)
- [API Reference](#api-reference)
- [The Agentic RAG System](#the-agentic-rag-system)
- [LLM Provider Fallback (Gemini → Mistral)](#llm-provider-fallback-gemini--mistral)
- [Document & URL Ingestion Pipeline](#document--url-ingestion-pipeline)
- [Usage Monitoring](#usage-monitoring)
- [Row Level Security](#row-level-security)
- [Known Limitations & Roadmap](#known-limitations--roadmap)

---

## Overview

Users register (admin-approved), create **projects** (workspaces), and inside each project:
- have one or more **chats** with an LLM (Gemini, falling back to Mistral),
- attach **collections** of sources — text files, PDFs, or URLs — which are chunked, embedded, and stored in ChromaDB,
- toggle which sources are active as context,
- get answers grounded in those sources via an **agentic RAG graph** (LangGraph) that decides for itself whether retrieval is even needed.

An admin dashboard covers user approval, login activity, and per-user LLM/search usage monitoring.

---

## Tech Stack

| Concern | Technology |
|---|---|
| API framework | FastAPI |
| Relational data | Supabase (PostgreSQL), accessed via the **service role** key only |
| Vector storage | ChromaDB (local, persistent) |
| Embeddings | `embeddinggemma` via local Ollama |
| Primary LLM | Gemini (`google-genai` SDK — **not** the legacy `google-generativeai`) |
| Fallback LLM | Mistral, called via raw `requests` (no `mistralai` SDK, to avoid dependency conflicts) |
| Agentic RAG orchestration | LangGraph |
| Web search | Tavily, Exa |
| Web fetch (single URL) | Jina Reader |
| Auth | Argon2 password hashing + JWT (python-jose) |
| PDF text extraction | pypdf |

---

## Project Structure

```
backend/
├── main.py                      # FastAPI app, CORS, router registration, lifespan (embedding warmup)
├── config/
│   ├── settings.py              # pydantic-settings; all env vars
│   ├── auth.py                  # Argon2 + JWT helpers, get_current_user / require_admin deps
│   ├── env.py                   # legacy manual dotenv loader (still referenced by settings.py)
│   ├── models.py                # get_gemini_response() — Gemini call + Mistral fallback + usage logging
│   └── prompts.py               # every RAG prompt template, centralized
├── database/
│   ├── db.py                    # Supabase client singleton (service role key)
│   └── chroma_client.py         # ChromaDB client + per-collection chunk add/delete
├── models/                      # Pydantic request/response schemas, split by domain
│   ├── auth.py  user.py  log.py  chat.py  collection.py  project.py  search.py
├── routes/                      # FastAPI routers, split by domain
│   ├── auth.py  admin.py  projects.py  chat.py  collections.py  search.py
├── services/                    # business logic used by routes and graph nodes
│   ├── extraction.py            # txt/pdf → raw text
│   ├── text_processing.py       # chunk_text()
│   ├── embeddings.py            # embed_texts(), warm_up_embedding_model()
│   ├── web_fetch.py             # Jina Reader (manual URL add)
│   ├── web_search.py            # Tavily / Exa search, normalized result shape
│   ├── rag_llm.py               # router/refine/validate/generate prompts → get_gemini_response
│   ├── rag_retrieval.py         # active-item lookup + globally-ranked Chroma chunk pool
│   └── usage_tracker.py         # best-effort LLM token / search credit logging
└── graph/                       # LangGraph agentic RAG pipeline
    ├── state.py                 # RAGState TypedDict
    ├── graph.py                 # builds + compiles the graph, conditional edges
    └── nodes/
        ├── router_node.py  refine_query_node.py  retrieve_node.py
        └── validation_node.py  generate_node.py
```

---

## Environment Variables

All read via `backend/config/settings.py`.

```env
# Supabase
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_SERVICE_KEY=eyJ...          # must be the service_role key, NOT anon — see "Row Level Security"

# JWT
JWT_SECRET=<32+ random hex chars>
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60

# CORS
CORS_ORIGINS=http://localhost:8501,http://127.0.0.1:8501

# Gemini (primary LLM)
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-2.5-flash

# Mistral (fallback LLM — used automatically if Gemini fails, e.g. quota exhaustion)
MISTRAL_API_KEY=...
MISTRAL_MODEL=mistral-small-2506
FORCE_MISTRAL=false                  # set true to force Mistral-only, for testing the fallback path

# Chat history
UI_HISTORY_LIMIT=50                  # messages shown in the UI
LLM_CONTEXT_LIMIT=10                 # messages sent to the LLM as context

# Embeddings (local Ollama)
EMBEDDING_MODEL=embeddinggemma
CHUNK_SIZE=1000
CHUNK_OVERLAP=150

# ChromaDB
CHROMA_PERSIST_DIR=./vector_database

# Web search / fetch
JINA_API_KEY=...
TAVILY_API_KEY=...
EXA_API_KEY=...
```

**Ollama** must be running locally with `embeddinggemma` pulled (`ollama pull embeddinggemma`) before starting the backend — `warm_up_embedding_model()` runs at startup and logs a warning (not a crash) if Ollama isn't reachable yet.

---

## Running the Backend

```bash
pip install -r requirements.txt --break-system-packages   # if needed
uvicorn backend.main:app --reload --port 8000
```

`GET /health` returns service status and the resolved CORS origin list — useful as a first smoke test.

---

## Database Schema

All tables live in Supabase/Postgres, under `public`. RLS is enabled on every table (see [Row Level Security](#row-level-security)) — the backend bypasses it entirely via the service role key.

| Table | Purpose | Key columns |
|---|---|---|
| `users` | Custom auth table (not Supabase Auth) | `id, username, password (Argon2id), role, is_approved` |
| `login_logs` | Login activity, shown in admin dashboard | `user_id, username, login_time, ip_address` |
| `projects` | Workspaces, one user owns many | `id, user_id, name` |
| `chats` | Conversations inside a project | `id, project_id, name` |
| `messages` | Persisted chat history | `id, chat_id, role ('user'\|'assistant'), content` |
| `collections` | Source groupings inside a project | `id, project_id, name, type ('documents'\|'urls'\|'text')` |
| `collection_items` | One row per file/URL inside a collection | `id, collection_id, name, source_type ('txt'\|'pdf'\|'url'), is_active, status, chunk_count, error_message` |
| `llm_usage` | One row per LLM call, for admin monitoring | `user_id, provider ('gemini'\|'mistral'), model, prompt_tokens, completion_tokens, total_tokens` |
| `search_usage` | One row per web search call, for admin monitoring | `user_id, engine ('tavily'\|'exa'), num_results, search_depth, credits` |

**Notes:**
- `collections.type` determines what `collection_items` can be added: `text` → `.txt` uploads, `documents` → `.pdf` uploads, `urls` → manual URL add or web-search results. Uploads for `urls` collections are rejected at the API level.
- `collection_items.is_active` controls whether that item's chunks are included in RAG retrieval — toggled from the UI, applied via a bulk PATCH endpoint (batches many toggles into one request rather than one request per checkbox).
- `search_usage.credits`: Tavily's `advanced` search depth costs ~2x a normal call, so it's logged as 2 credits; everything else (other Tavily depths, all Exa calls) is 1 credit.
- ChromaDB mirrors `collections`: one Chroma collection per Supabase `collections.id`. Each chunk inside it is tagged with `item_id` in its metadata, so toggling/deleting a single file or URL never requires touching other items' chunks.

---

## Authentication

1. Register → `is_approved = false`, `role = 'user'`.
2. Admin approves via `PUT /admin/users/{id}/approve`.
3. Login → JWT issued, payload `{"sub": "<user_uuid>", "username": ..., "role": ..., "exp": ...}`. Note `sub` is the UUID, not the username.
4. Every authenticated request sends `Authorization: Bearer <token>`.
5. `get_current_user` dependency decodes the JWT into `{sub, username, role}`; `require_admin` additionally checks `role == "admin"`.
6. Passwords are hashed with Argon2id (`argon2-cffi`), not bcrypt — bcrypt raises on passwords over 72 bytes, Argon2 has no such limit.

---

## API Reference

All routes are prefixed at the app root except `/admin/*`, which has its own router prefix.

### Auth
| Method | Path | Notes |
|---|---|---|
| POST | `/auth/register` | Creates an unapproved user |
| POST | `/auth/login` | Returns JWT + user info |

### Admin (requires `role == "admin"`)
| Method | Path | Notes |
|---|---|---|
| GET | `/admin/users` | `?pending_only=true` to filter |
| PUT | `/admin/users/{id}/approve` | |
| PUT | `/admin/users/{id}/role` | `?new_role=admin\|user`; can't change your own role |
| DELETE | `/admin/users/{id}` | Can't delete your own account |
| GET | `/admin/logs` | Paginated login history, `?username=` filter |
| GET | `/admin/stats` | Aggregate counts + 7 most recent logins |
| GET | `/admin/usage/llm` | Per-user token usage, aggregated in Python from `llm_usage` |
| GET | `/admin/usage/search` | Per-user search credits, aggregated in Python from `search_usage` |

### Projects
| Method | Path |
|---|---|
| GET / POST | `/projects` |
| PUT / DELETE | `/projects/{project_id}` |

### Chats
| Method | Path | Notes |
|---|---|---|
| GET / POST | `/projects/{project_id}/chats` | |
| PUT / DELETE | `/chats/{chat_id}` | |
| GET | `/chats/{chat_id}/messages` | Last `UI_HISTORY_LIMIT` messages, oldest first |
| POST | `/chats/{chat_id}/message` | Non-streaming — runs the full RAG graph, returns the final answer |
| POST | `/chats/{chat_id}/message/stream` | SSE — emits `{"type":"node","node":...}` per graph step, then `{"type":"done","answer":...}` or `{"type":"error","detail":...}` |

### Collections
| Method | Path | Notes |
|---|---|---|
| GET / POST | `/projects/{project_id}/collections` | |
| DELETE | `/collections/{collection_id}` | Also deletes its ChromaDB collection |
| GET | `/collections/{collection_id}/items` | |
| POST | `/collections/{collection_id}/items` | Multipart file upload (txt/pdf collections only) |
| POST | `/collections/{collection_id}/items/url` | Manual single URL add (urls collections only), fetched via Jina |
| POST | `/collections/{collection_id}/items/from-search` | Bulk-add selected Tavily/Exa results; rejects URLs already in the collection |
| PATCH | `/collections/{collection_id}/items/{item_id}` | Toggle `is_active` |
| PATCH | `/collections/{collection_id}/items/bulk` | Batch toggle many items in one request |
| DELETE | `/collections/{collection_id}/items/{item_id}` | Deletes the Supabase row and its Chroma chunks |

### Search
| Method | Path | Notes |
|---|---|---|
| POST | `/search/web` | `{engine: "tavily"\|"exa", query, num_results, search_depth}` — logs usage automatically |

---

## The Agentic RAG System

Built with LangGraph. Given a user query and the recent chat history, the graph decides for itself whether it needs to search the project's sources at all, and if the first retrieval attempt isn't enough, retries once with more context before answering regardless.

![RAG graph workflow](src/rag_graph_workflow.svg)

### Flow

1. **`router`** (`decide_retrieval`) — one LLM call decides `RETRIEVE` or `DIRECT`. `DIRECT` for greetings, small talk, or anything answerable from the visible chat history alone. `RETRIEVE` for anything needing facts from the project's sources, or an explicit "search my documents" request.
2. **`DIRECT`** → skips straight to `generate`.
3. **`RETRIEVE`** → **`refine_query`** (`refine_query`) — rewrites the raw message into a standalone search query using history to resolve references (e.g. "what is it?" → "what is an LLM?").
4. **`retrieve`** (`retrieve_pool`) —
   - **1st call**: embeds the refined query once via `embeddinggemma`, queries every ChromaDB collection with at least one active item in the project, merges results across collections, sorts globally by distance, keeps a pool of **10**. `context_chunks = pool[0:5]`.
   - **2nd call** (retry only): slices `pool[5:10]` from the *same* pool and appends it to `context_chunks` — no new embedding call, no new Chroma query, and guaranteed non-overlapping chunks.
   - If no active sources exist anywhere in the project, the pool is empty and validation is skipped entirely (see below).
5. **`validate`** (`validate_context`) — one LLM call judges whether `context_chunks` can answer the original query. Skipped (auto-pass) if the pool came back empty.
6. **Conditional**: `SUFFICIENT` → `generate`. `INSUFFICIENT` and `retrieval_attempts < 2` → back to `retrieve` for the second batch. `INSUFFICIENT` twice → `generate` anyway, with whatever context exists — the system always answers rather than refusing outright.
7. **`generate`** (`generate_answer`) — final answer. The retrieved context + question are folded into one final "user" turn appended after the real chat history (so role alternation stays valid for Gemini), then sent to `get_gemini_response`.

### State (`backend/graph/state.py`)

```python
class _RAGStateRequired(TypedDict):
    project_id: str
    chat_id: str
    user_id: str            # for usage attribution
    query: str               # original message
    history: list[dict]      # prior messages, excludes the new query

class RAGState(_RAGStateRequired, total=False):
    refined_query: str
    needs_retrieval: bool
    retrieved_pool: list[dict]
    context_chunks: list[dict]
    retrieval_attempts: int
    validation_passed: bool
    answer: str
```

Split deliberately into required vs. optional fields — the required set is always provided by `backend/routes/chat.py` when the graph is invoked, so nodes can safely do `state["query"]` instead of `state.get("query")` for those fields.

### Prompts

All four prompt templates live in `backend/config/prompts.py`: `ROUTER_PROMPT`, `REFINE_QUERY_PROMPT`, `VALIDATION_PROMPT`, `GENERATION_PROMPT`. Router and validation prompts force a single-word response (`RETRIEVE`/`DIRECT`, `SUFFICIENT`/`INSUFFICIENT`), parsed with `.startswith()` for tolerance to trailing punctuation.

### Debugging

Every node prints a `[RAG] ...` line to the backend terminal as it runs (which node, pool size, validation result, etc). The streaming endpoint (`/chats/{id}/message/stream`) surfaces the same node-by-node progress to the frontend in real time via Server-Sent Events, using `graph.stream(..., stream_mode="updates")` instead of `.invoke()`.

---

## LLM Provider Fallback (Gemini → Mistral)

`backend/config/models.py`'s `get_gemini_response(messages, temperature, user_id)` is the single entry point every LLM call in the app goes through (router, refine, validate, generate).

1. Tries Gemini first.
2. On **any** exception (most commonly hitting the free-tier quota), logs it and transparently retries via Mistral — a direct `requests.post` to `https://api.mistral.ai/v1/chat/completions`, deliberately **not** the `mistralai` SDK, to avoid dependency conflicts.
3. Mistral's chat completions API is OpenAI-compatible, and messages already use `"user"`/`"assistant"` roles, so no role conversion is needed there (unlike Gemini, which needs `"user"`/`"model"`).
4. If Mistral also fails, raises a combined `RuntimeError` rather than swallowing it — this reaches the frontend as an SSE `error` event or a `502` on the non-streaming endpoint.
5. Set `FORCE_MISTRAL=true` to skip Gemini entirely — useful for testing the fallback path without waiting for a real quota error.

Both providers' token usage is captured and logged per-call (see [Usage Monitoring](#usage-monitoring)).

---

## Document & URL Ingestion Pipeline

For `text`/`documents` collections (file upload, `POST /collections/{id}/items`):

1. Validate file extension matches the collection type.
2. Extract raw text (`extraction.py`: `extract_txt` decodes UTF-8/latin-1; `extract_pdf` uses pypdf page-by-page).
3. Chunk (`text_processing.py`: simple overlapping character-based chunker, `chunk_size`/`chunk_overlap` from settings).
4. Embed all chunks in one batch via `embeddings.py` (`embed_texts`, calls local Ollama).
5. Store in the collection's ChromaDB collection — `documents` = raw chunk text, `embeddings` = vectors, `metadatas` = `{item_id, collection_id, source_name, chunk_index}`.
6. Update the `collection_items` row: `status = "ready"`, `chunk_count = len(chunks)` — or `status = "error"` with `error_message` if anything above failed, without aborting the rest of the batch.

For `urls` collections, two entry points instead of upload:
- **Manual add** (`POST /collections/{id}/items/url`): fetches the page as markdown via Jina Reader, then follows the same chunk → embed → store pipeline. Rejects duplicate URLs within the same collection.
- **From search** (`POST /collections/{id}/items/from-search`): the Tavily/Exa snippet/highlight text is embedded directly, with no re-fetch — a deliberate speed/cost tradeoff over always pulling the full page.

---

## Usage Monitoring

Monitoring only — no limits are enforced yet (planned as a future feature).

- **LLM tokens**: every `get_gemini_response` call logs one `llm_usage` row (provider, model, prompt/completion/total tokens), attributed to the user via `RAGState.user_id`. Gemini's `usage_metadata.{prompt,candidates,total}_token_count` and Mistral's OpenAI-compatible `usage.{prompt,completion,total}_tokens` are both captured.
- **Search credits**: every `/search/web` call logs one `search_usage` row, weighted 2 credits for Tavily `advanced` depth, 1 credit otherwise.
- Both loggers are **best-effort** — wrapped in `try/except`, printing on failure rather than raising, so a logging hiccup can never break an actual chat response or search.
- `GET /admin/usage/llm` and `GET /admin/usage/search` aggregate raw rows into per-user totals in Python (not a SQL view/RPC) — fine at the row counts an MVP admin dashboard needs; worth revisiting with a real aggregate query if either table grows large.

---

## Row Level Security

RLS is enabled on all 9 tables. This is safe because the backend's only Supabase client (`backend/database/db.py`) uses the **service role** key, which has `BYPASSRLS` in Postgres — it ignores RLS regardless of whether it's enabled or whether any policies exist.

**Critical gotcha**: if login (or any other DB-backed endpoint) suddenly starts failing with empty results right after enabling RLS, the near-certain cause is that `SUPABASE_SERVICE_KEY` in `.env` is actually the **anon** key, not the true `service_role` key — Supabase's dashboard lists both, and it's an easy copy-paste mix-up. Decode the JWT payload to check:

```bash
echo "$SUPABASE_SERVICE_KEY" | cut -d. -f2 | base64 -d | python3 -m json.tool
```

`"role": "service_role"` is correct; `"role": "anon"` is the bug.

---

## Known Limitations & Roadmap

- **No usage limits enforced** — monitoring only, by design for now.
- **No token counting on chat context** — `LLM_CONTEXT_LIMIT` caps message *count*, not tokens; very long messages could still hit a model's context limit.
- **Character-based chunking** — simple and fast, not semantically aware. Could be upgraded to sentence/semantic chunking later without changing the `chunk_text()` signature.
- **Search-result content is a snippet, not a full page** — items added via Tavily/Exa search carry less content than manually-added URLs (which get the full page via Jina). A deliberate cost/speed tradeoff, not a bug.
- **Usage aggregation is row-by-row in Python** — fine for MVP scale; a real SQL aggregate query would be needed if `llm_usage`/`search_usage` grow large.
- **`backend/config/env.py`** is legacy (a manual dotenv loader `settings.py` still imports from) — dead-code cleanup candidate, left alone deliberately per project decision to avoid unrelated churn.