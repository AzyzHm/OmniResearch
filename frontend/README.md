# OmniResearch — Frontend Documentation

Vite + React + TypeScript single-page app. This document covers the **frontend only**. Backend documentation lives at [`../backend/docs/README.md`](../backend/docs/README.md).

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Design System](#design-system)
- [Environment Variables](#environment-variables)
- [Running the Frontend](#running-the-frontend)
- [Routing & Code Splitting](#routing--code-splitting)
- [Authentication](#authentication)
- [Data Fetching & the API Client](#data-fetching--the-api-client)
- [Chat Streaming (SSE)](#chat-streaming-sse)
- [Testing](#testing)
- [Known Limitations / Future Work](#known-limitations--future-work)

---

## Overview

Users land on a marketing page, sign up (admin-approved before they can log in), and once inside the workspace:
- create **projects**, each with its own **collections** (sources) and **chats**,
- upload documents/text files, add URLs manually, or bulk-add results from a Tavily/Exa web search into a collection,
- toggle which collection items are active as retrieval context,
- chat with an LLM over SSE streaming, watching live node-progress labels from the backend's agentic RAG graph, picking a retrieval mode (semantic/keyword/hybrid) per message,
- see grounded answers with inline `[n]` citations and a footnote-style source list underneath, persisted so they survive a reload,
- hit a dedicated quota-exceeded card (with a live countdown to reset) if they exhaust their daily token quota.

A separate, role-gated **admin dashboard** (`/admin`, `admin`/`superadmin` only) mirrors the backend's four admin domains: overview stats, user management (approve/promote/demote/delete/token-limit editing), login logs with a per-day chart, and LLM/search usage monitoring with per-user breakdowns and charts.

This was originally a Streamlit app; it has since been fully migrated to this React SPA against the same, unchanged FastAPI backend.

---

## Tech Stack

| Concern | Technology |
|---|---|
| Build tool | Vite |
| Framework | React 19 + TypeScript |
| Routing | `react-router-dom` (declarative `<BrowserRouter>` mode) |
| Styling | Tailwind CSS v4 (`@theme` token system, no `tailwind.config.js`) |
| Component primitives | shadcn/ui on **Base UI** (not Radix) |
| Data fetching / caching | `@tanstack/react-query` |
| Markdown rendering | `react-markdown` (assistant chat replies) |
| Charts | `recharts` (admin panel only — lazy-loaded, see [Code Splitting](#routing--code-splitting)) |
| Icons | `lucide-react` |
| HTTP client | Native `fetch`, hand-rolled wrapper (no axios) |
| Testing | `vitest` + `@testing-library/react` + `jsdom` |
| Linting | ESLint (`eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`) |

---

## Project Structure

Feature-folder layout: each domain owns its API calls, components, hooks, and tests together, rather than being split by file type.

```
src/
├── main.tsx                     # QueryClientProvider setup, app entry
├── App.tsx                      # Route table; lazy-loads everything except Landing
├── index.css                    # Design tokens (@theme), font imports, global styles
│
├── shared/                      # Cross-feature primitives, no feature-specific logic
│   ├── components/ui/           # shadcn-generated: button, dialog, input, label
│   ├── lib/
│   │   ├── apiClient.ts         # fetch wrapper: ApiError, credentials, no-store cache
│   │   └── shortenUrl.ts        # URL truncation for compact table/citation display
│   └── test/setup.ts            # vitest + jest-dom setup
│
└── features/
    ├── auth/                    # api, AuthContext, ProtectedRoute/AdminRoute guards,
    │                             #   Login/Signup pages, AuthLayout
    ├── landing/                 # Landing page + Nav/Hero/Features/HowItWorks/Footer
    ├── legal/                   # Terms/Privacy/Cookies placeholder pages
    ├── projects/                # api, ProjectsList page, ProjectCard, ProjectFormDialog
    ├── collections/             # api, searchApi, sidebar, items panel, search modal,
    │                             #   status badge
    ├── chat/                    # api (incl. the SSE parser), useChatStream hook,
    │                             #   ChatArea, message bubble, input, sidebar, cards
    ├── workspace/                # Workspace shell + ProjectDetail page, SourcesDrawer
    └── admin/                   # api, AdminLayout + 4 tab pages, MetricCard/Badge/UserRow
```

The `@/` path alias points at `src/`, so imports look like `@/features/chat/api` or `@/shared/lib/apiClient` regardless of how deep a file lives.

---

## Design System

Palette, typography, and section-rhythm decisions from the original landing-page design work — **reproduce these values verbatim if extending the UI**, don't reinvent them:

| Token | Hex | Usage |
|---|---|---|
| `--color-paper` | `#F1F3F0` | Main page background |
| `--color-ink` | `#1C2321` | Primary text, dark surfaces |
| `--color-amber` | `#C9902F` | Accent, warnings, quota UI |
| `--color-teal` | `#2F6F62` | Secondary accent, links, citations, primary actions |
| `--color-surface` | `#FFFFFF` | Card/elevated surfaces |
| `--color-sand` | `#EAE1CF` | Light warm neutral (section backgrounds) |

**Fonts:** Fraunces (display/headings), Inter (body), IBM Plex Mono (labels, citation markers, tags) — loaded via Google Fonts `<link>` tags in `index.html`, not npm packages.

shadcn's own semantic tokens (`--background`, `--foreground`, `--primary`, etc.) are **remapped to derive from this palette** in `index.css`, rather than existing as a parallel raw-token system — every shadcn component automatically inherits the theme with zero per-component overrides. If touching `index.css`, always merge into the existing `@theme inline { ... }` / `:root { ... }` structure; never wholesale-replace it (doing so once broke shadcn's own `ghost`-variant button styling).

---

## Environment Variables

| Variable | Default | Purpose |
|---|---|---|
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend base URL. Set via `.env` (gitignored — copy `.env.example` to get started); `apiClient.ts` falls back to this same default if unset. Vite only reads env files from this project's own root — it has no access to the backend's `.env`, and shouldn't: any `VITE_`-prefixed variable gets baked directly into the public client bundle, so backend secrets must never live in this file. |

---

## Running the Frontend

```bash
npm install
npm run dev          # Vite dev server, default port 5173
npm run build        # production build → dist/
npm run test         # vitest run (or: npx vitest run)
npx tsc --noEmit      # type-check without emitting
npx eslint .          # lint
```

The backend must be running separately (`uvicorn backend.main:app --reload --port 8000`) and must have `http://localhost:5173` in its `cors_origins` setting.

---

## Routing & Code Splitting

`App.tsx` defines all routes. Every page **except `Landing`** is behind `React.lazy()`, wrapped in a single `<Suspense>` boundary — `Landing` is the critical first-paint/demo page and stays in the main bundle; everything else (auth pages, the entire workspace, and especially the admin panel, which pulls in `recharts`) only downloads once a person actually navigates there.

Route guards:
- **`ProtectedRoute`** (`features/auth/routes/`) — redirects to `/login` if not authenticated. Checks `AuthContext`, which itself resolves via `GET /auth/me`.
- **`AdminRoute`** — same, plus requires `role` to be `admin` or `superadmin`; redirects other authenticated users to `/app`.

```
/                              → Landing (eager)
/login, /signup                → lazy
/app                           → ProtectedRoute → Workspace shell
  /app (index)                 → ProjectsList
  /app/projects/:projectId     → ProjectDetail (Chats rail + Chat area + Sources drawer)
/admin                         → AdminRoute → AdminLayout
  /admin (index)               → Overview
  /admin/users                 → User Management
  /admin/logs                  → Login Logs
  /admin/usage                 → Usage
/terms, /privacy, /cookies     → lazy placeholders
```

---

## Authentication

JWT is stored in an **httpOnly cookie** set by the backend (`SameSite=Lax`), not `localStorage` — inaccessible to JavaScript entirely, closing the XSS-exfiltration vector that matters for a tool that ingests external URLs and files.

`AuthContext` (`features/auth/context/AuthContext.tsx`) wraps a TanStack Query call to `GET /auth/me` and exposes `{ user, isAuthenticated, isLoading, refetchUser, clearUser }` app-wide. A few things worth knowing if touching this:

- **The login race condition**: after a successful `POST /auth/login`, the UI must `await refetchUser()` *before* navigating to `/app`. Without it, `AuthContext`'s cached "logged out" state (from the initial app load) is still stale when `ProtectedRoute` mounts, and it bounces the user straight back to `/login` immediately after a successful login.
- **`clearUser()`** is called on logout to immediately reflect the logged-out state locally, without waiting on a network round-trip.
- There is deliberately no CSRF-token scheme — `SameSite=Lax` is judged sufficient since there's no cross-site form-posting in this app. A documented tradeoff, not an oversight.

---

## Data Fetching & the API Client

`shared/lib/apiClient.ts` is a small `fetch` wrapper — `get`/`post`/`put`/`patch`/`delete`/`upload` — used by every feature's `api.ts`. Two non-obvious things it handles that are easy to get wrong:

1. **`cache: "no-store"` on every request.** Without this, some delete/mutation flows can show stale data even after a successful write, if the browser serves an HTTP-cached GET instead of a fresh one.
2. **Never assumes a JSON body exists.** A `204 No Content` response can still carry a `Content-Type: application/json` header from a backend's default response class even though the body is empty — trusting that header and calling `.json()` on it throws a `SyntaxError` that looks exactly like a failed request. The client checks the *status code* first (skips parsing entirely for `204`/`304`) and falls back gracefully if parsing ever fails for any other reason, rather than letting a harmless parse failure masquerade as "the request failed."
3. **FormData uploads must not get an explicit `Content-Type`** — the browser needs to set its own multipart boundary. The `upload()` method and the generic `request()` wrapper both account for this.

Every feature's mutations (delete, in particular) follow the same pattern: update the TanStack Query cache immediately in `onSuccess` (`setQueryData`), then `invalidateQueries` as a backup reconciliation — rather than relying solely on invalidation-triggered background refetch, which is more prone to timing issues.

---

## Chat Streaming (SSE)

The backend's `/chats/{id}/message/stream` endpoint requires a `POST` with a JSON body and returns `text/event-stream` — the native `EventSource` API can't be used here since it's GET-only with no custom body support. `features/chat/api.ts`'s `streamChatMessage()` is a hand-rolled async generator instead: it reads the raw `ReadableStream`, buffers incoming chunks, and splits on `\n\n` to parse individual `data: {...}` frames — including correctly handling a frame's JSON getting split mid-object across two separate stream chunks (covered by a dedicated test).

`useChatStream` (`features/chat/hooks/`) wraps this generator with React state (`isStreaming`, `nodeName`, `error`) and properly aborts any in-flight stream via `AbortController` on unmount — switching chats mid-response doesn't leak a connection or try to update a dead component.

After a stream finishes (success **or** error), `ChatArea` refetches the persisted message list from the backend rather than trusting local state — the user's message is persisted server-side either way, so this is the source of truth for both the final answer and its citations.

**Citations**: the backend's `generate_node` only returns sources the model actually cited (parsed from `[n]` markers in its own answer, not just whatever was retrieved). The frontend renders these as a footnote-style list below the assistant's markdown-rendered reply — URL sources get the same shortened/clickable treatment used in the Collections panel, filenames render as plain text. Citations are persisted (`messages.sources` JSONB column) and survive a reload.

---

## Testing

`vitest` + `jsdom`, tests live next to the code they cover (e.g. `ChatMessageBubble.tsx` + `ChatMessageBubble.test.tsx` in the same folder), not in a separate top-level test tree.

```bash
npx vitest run          # run once
npx vitest               # watch mode
```

Notable tests, chosen because they each caught a real bug during development rather than being written for coverage's sake:
- **`features/chat/api.test.ts`** — the SSE parser, including a frame deliberately split mid-JSON across a chunk boundary (the classic way manual SSE parsers break), and a regression test for `createChat` always sending a body (the backend's required-body-but-optional-fields Pydantic pattern silently 422s on a missing body otherwise).
- **`shared/lib/shortenUrl.test.ts`** — the URL-truncation helper.
- **`features/chat/components/ChatMessageBubble.test.tsx`** — the citation footnote list (empty case, normal case, URL-vs-filename rendering, confirms user messages never show sources).
- **`features/projects/pages/ProjectsList.test.tsx`** — a full render + real delete-confirm click flow, with the backend's follow-up refetch deliberately left hanging forever, to prove the deleted item disappears from the optimistic cache update alone rather than depending on that refetch ever resolving.

---

## Known Limitations / Future Work

- `Terms`/`Privacy`/`Cookies` are still placeholder pages ("content coming soon").
- No route-level tests for the admin panel yet (unlike the rest of the app, which has real jsdom coverage for its trickiest logic).
- Citation UI shows a flat footnote list; `[n]` markers in the answer text are plain text, not yet clickable/scroll-linked to their footnote.