# OmniResearch : Frontend Documentation

Vite + React + TypeScript single-page application. This document covers the **frontend only**. Backend documentation lives at [`backend/docs/README.md`](../backend/docs/README.md).

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Design System](#design-system)
- [Environment Variables](#environment-variables)
- [Getting Started](#getting-started)
- [Routing & Code Splitting](#routing--code-splitting)
- [Authentication](#authentication)
- [Data Fetching & the API Client](#data-fetching--the-api-client)
- [Chat Streaming (SSE)](#chat-streaming-sse)
- [Testing](#testing)

---

## Overview

Users land on a marketing page, sign up (admin-approved before they can log in), and once inside the workspace can:

- create **projects**, each holding its own set of sources (collections), chats, and notes,
- upload documents or text files, add URLs manually, or bulk-add results from a Tavily/Exa web search into a project's source library,
- toggle which source items are active as retrieval context,
- chat with an LLM over SSE streaming, watching live node-progress labels from the backend's agentic RAG graph, and pick a retrieval mode (semantic, keyword, or hybrid) per message,
- read grounded answers with inline `[n]` citations and a footnote-style source list underneath, persisted so they survive a reload,
- save individual chat messages, along with their citations, into named notebooks for later reference,
- hit a dedicated quota-exceeded card, with a live countdown to reset, if the daily token quota is exhausted,
- switch between light, dark, and system-driven themes, with the preference remembered across visits.

A separate, role-gated **admin dashboard** (`/admin`, `admin`/`superadmin` only) mirrors the backend's four admin domains: overview stats, user management (approve, promote, demote, delete, edit token limits), login logs with a per-day chart, and LLM/search usage monitoring with per-user breakdowns and charts.

This was originally a Streamlit application. It has since been fully migrated to this React SPA, running against the same FastAPI backend.

---

## Tech Stack

| Concern                 | Technology                                                          |
| ----------------------- | ------------------------------------------------------------------- |
| Build tool              | Vite                                                                |
| Framework               | React 19 + TypeScript                                               |
| Routing                 | `react-router-dom` (`<BrowserRouter>`)                              |
| Styling                 | Tailwind CSS v4 (`@theme` token system, no `tailwind.config.js`)    |
| Component primitives    | shadcn/ui on Base UI (not Radix)                                    |
| Data fetching / caching | `@tanstack/react-query`                                             |
| Markdown rendering      | `react-markdown` with `remark-gfm` (assistant chat replies)         |
| PDF rendering           | `react-pdf` / `pdfjs-dist` (source preview)                         |
| Charts                  | `recharts` (admin panel only, lazy-loaded)                          |
| Icons                   | `lucide-react`                                                      |
| HTTP client             | Native `fetch`, hand-rolled wrapper (no axios)                      |
| Testing                 | `vitest` + `@testing-library/react` + `jsdom`                       |
| Linting                 | ESLint (`eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`) |

---

## Project Structure

Feature-folder layout: each domain owns its own API calls, components, hooks, and tests, rather than being split by file type.

```
src/
├── main.tsx                     # QueryClientProvider + ThemeProvider setup, app entry
├── App.tsx                      # Route table; lazy-loads everything except Landing
├── index.css                    # Design tokens (@theme), font imports, global styles
│
├── shared/                      # Cross-feature primitives, no feature-specific logic
│   ├── components/
│   │   ├── ui/                  # shadcn-generated primitives (button, dialog, input, label...)
│   │   ├── ThemeToggle.tsx      # Light / dark / system switcher
│   │   ├── AssistantBot.tsx     # Landing/marketing illustration
│   │   └── RagPipelineIllustration.tsx
│   ├── context/
│   │   └── ThemeContext.tsx     # Theme preference, resolution, persistence
│   ├── lib/
│   │   ├── apiClient.ts         # fetch wrapper: ApiError, credentials, no-store cache
│   │   ├── shortenUrl.ts        # URL truncation for compact table/citation display
│   │   └── utils.ts             # cn() class-merging helper
│   └── test/setup.ts            # vitest + jest-dom setup
│
└── features/
    ├── auth/                    # api, AuthContext, ProtectedRoute/AdminRoute guards,
    │                             #   Login/Signup pages, AuthLayout
    ├── landing/                 # Landing page + Nav/Hero/Features/HowItWorks/Footer
    ├── legal/                   # Terms/Privacy/Cookies pages
    ├── projects/                # api, ProjectsList page, ProjectCard, ProjectFormDialog
    ├── collections/             # api, searchApi, source sidebar, items panel, PDF preview,
    │                             #   search modal, status badge
    ├── notes/                   # api, notes sidebar, note items panel, save-to-note dialog
    ├── chat/                    # api (incl. the SSE parser), useChatStream hook,
    │                             #   ChatArea, message bubble, input, sidebar, quota/error cards
    ├── workspace/                # Workspace shell + ProjectDetail page, Sources/Notes drawers
    └── admin/                   # api, AdminLayout + 4 tab pages, MetricCard/Badge/UserRow
```

The `@/` path alias points at `src/`, so imports look like `@/features/chat/api` or `@/shared/lib/apiClient` regardless of how deep a file lives.

---

## Design System

Palette, typography, and section-rhythm decisions from the original landing-page design work. Reproduce these values verbatim if extending the UI, don't reinvent them. Every token has both a light and a dark value, resolved through `ThemeContext`.

| Token             | Light     | Dark      | Usage                                               |
| ----------------- | --------- | --------- | --------------------------------------------------- |
| `--color-paper`   | `#F1F3F0` | `#14171A` | Main page background                                |
| `--color-ink`     | `#1C2321` | `#E7EAE7` | Primary text, dark surfaces                         |
| `--color-amber`   | `#C9902F` | `#D9A548` | Accent, warnings, quota UI                          |
| `--color-teal`    | `#2F6F62` | `#4C9285` | Secondary accent, links, citations, primary actions |
| `--color-surface` | `#FFFFFF` | `#1C2023` | Card / elevated surfaces                            |
| `--color-sand`    | `#EAE1CF` | `#262A20` | Light warm neutral (section backgrounds)            |

**Fonts:** Fraunces (display/headings), Inter (body), IBM Plex Mono (labels, citation markers, tags), loaded via Google Fonts `<link>` tags in `index.html`, not npm packages.

shadcn's own semantic tokens (`--background`, `--foreground`, `--primary`, etc.) are remapped to derive from this palette in `index.css`, rather than existing as a parallel raw-token system, so every shadcn component automatically inherits the theme with zero per-component overrides. If touching `index.css`, always merge into the existing `@theme inline { ... }` / `:root { ... }` / `.dark { ... }` structure rather than replacing it wholesale.

The `dark` class is toggled on `<html>` by `ThemeContext`; the preference (`light` / `dark` / `system`) is stored in `localStorage` under `omniresearch-theme` and resolved live against `prefers-color-scheme` when set to `system`.

---

## Environment Variables

| Variable            | Default                 | Purpose                                                                                                                                                                                                                                                                                                                            |
| ------------------- | ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `VITE_API_BASE_URL` | `http://localhost:8000` | Backend base URL. Set via `.env` (gitignored, copy `.env.example` to get started) `apiClient.ts` falls back to this same default if unset. Vite only reads env files from this project's own root. Any `VITE_` prefixed variable is baked directly into the public client bundle, so backend secrets must never live in this file. |

---

## Getting Started

Steps to run the frontend from a clean clone:

```bash
cd frontend
npm i                 # install dependencies
npm test               # run the test suite (vitest run)
npm run dev             # start the Vite dev server, default port 5173
```

Additional scripts available in `package.json`:

```bash
npm run build          # type-check (tsc -b) + production build → dist/
npm run preview         # preview the production build locally
npm run lint            # eslint .
npm run test:watch      # vitest in watch mode
```

The backend must be running separately (`uvicorn main:app --reload --port 8000`) and must have `http://localhost:5173` listed in its `cors_origins` setting for requests from the dev server to succeed.

---

## Routing & Code Splitting

`App.tsx` defines all routes. Every page except `Landing` is behind `React.lazy()`, wrapped in a single `<Suspense>` boundary. `Landing` is the critical first-paint/demo page and stays in the main bundle; everything else (auth pages, the entire workspace, and especially the admin panel, which pulls in `recharts`) only downloads once a person actually navigates there.

Route guards:

- **`ProtectedRoute`** (`features/auth/routes/`) redirects to `/login` if not authenticated. Checks `AuthContext`, which itself resolves via `GET /auth/me`.
- **`AdminRoute`** does the same, plus requires `role` to be `admin` or `superadmin`, redirecting other authenticated users to `/app`.

```
/                              → Landing (eager)
/login, /signup                → lazy
/app                           → ProtectedRoute → Workspace shell
  /app (index)                 → ProjectsList
  /app/projects/:projectId     → ProjectDetail (Chats rail + Chat area + Sources/Notes drawers)
/admin                         → AdminRoute → AdminLayout
  /admin (index)               → Overview
  /admin/users                 → User Management
  /admin/logs                  → Login Logs
  /admin/usage                 → Usage
/terms, /privacy, /cookies     → lazy
```

---

## Authentication

The JWT is stored in an httpOnly cookie set by the backend (`SameSite=Lax`), not `localStorage`, so it's inaccessible to JavaScript entirely.

`AuthContext` (`features/auth/context/AuthContext.tsx`) wraps a TanStack Query call to `GET /auth/me` and exposes `{ user, isAuthenticated, isLoading, refetchUser, clearUser }` app-wide. A couple of details worth knowing if touching this:

- **The login race condition**: after a successful `POST /auth/login`, the UI must `await refetchUser()` before navigating to `/app`. Without it, `AuthContext`'s cached "logged out" state from the initial app load is still stale when `ProtectedRoute` mounts, and it bounces the user straight back to `/login`.
- **`clearUser()`** is called on logout to immediately reflect the logged-out state locally, without waiting on a network round-trip.
- There is deliberately no CSRF-token scheme; `SameSite=Lax` is judged sufficient since the app has no cross-site form-posting. This is a documented tradeoff, not an oversight.

---

## Data Fetching & the API Client

`shared/lib/apiClient.ts` is a small `fetch` wrapper (`get`/`post`/`put`/`patch`/`delete`/`upload`) used by every feature's `api.ts`. A few behaviors worth knowing:

1. **`cache: "no-store"` on every request.** Without this, some delete/mutation flows can show stale data even after a successful write, if the browser serves an HTTP-cached GET instead of a fresh one.
2. **Never assumes a JSON body exists.** A `204 No Content` response can still carry a `Content-Type: application/json` header even though the body is empty. The client checks the status code first, skipping parsing entirely for `204`/`304`, and falls back gracefully if parsing fails for any other reason.
3. **FormData uploads never get an explicit `Content-Type`**, letting the browser set its own multipart boundary. Both `upload()` and the generic `request()` wrapper account for this.

Mutations that delete or modify data follow the same pattern throughout the app: update the TanStack Query cache immediately in `onSuccess` (`setQueryData`), then `invalidateQueries` as a backup reconciliation, rather than relying solely on invalidation-triggered background refetch.

---

## Chat Streaming (SSE)

The backend's `/chats/{id}/message/stream` endpoint requires a `POST` with a JSON body and returns `text/event-stream`. The native `EventSource` API can't be used here since it's GET-only with no custom body support, so `features/chat/api.ts`'s `streamChatMessage()` is a hand-rolled async generator instead: it reads the raw `ReadableStream`, buffers incoming chunks, and splits on `\n\n` to parse individual `data: {...}` frames, including correctly handling a frame's JSON getting split mid-object across two separate stream chunks.

`useChatStream` (`features/chat/hooks/`) wraps this generator with React state (`isStreaming`, `nodeName`, `error`) and properly aborts any in-flight stream via `AbortController` on unmount, so switching chats mid-response doesn't leak a connection or try to update a dead component.

After a stream finishes, whether it ends in success or error, `ChatArea` refetches the persisted message list from the backend rather than trusting local state, since the user's message is persisted server-side either way.

**Citations**: the backend's `generate_node` only returns sources the model actually cited, parsed from `[n]` markers in its own answer rather than everything that was retrieved. The frontend renders these as a footnote-style list below the assistant's markdown-rendered reply. URL sources get the same shortened, clickable treatment used in the source library panel; filenames render as plain text. Citations are persisted (`messages.sources` JSONB column) and survive a reload.

---

## Testing

`vitest` + `jsdom`; tests live next to the code they cover (for example `ChatMessageBubble.tsx` and `Chatmessagebubble.test.tsx` in the same folder), not in a separate top-level test tree.

```bash
npx vitest run          # run once
npx vitest               # watch mode
```

Notable tests, chosen because each one caught a real bug during development rather than being written for coverage's sake:

- **`features/chat/api.test.ts`** the SSE parser, including a frame deliberately split mid-JSON across a chunk boundary, and a regression test confirming `createChat` always sends a body, since the backend's required-body-but-optional-fields Pydantic pattern silently 422s on a missing body otherwise.
- **`shared/lib/shortenUrl.test.ts`** the URL-truncation helper.
- **`features/chat/components/Chatmessagebubble.test.tsx`** the citation footnote list (empty case, normal case, URL-vs-filename rendering, confirms user messages never show sources).
- **`features/projects/pages/ProjectsList.test.tsx`** a full render plus a real delete-confirm click flow, with the backend's follow-up refetch deliberately left hanging forever, to prove the deleted item disappears from the optimistic cache update alone rather than depending on that refetch ever resolving.
- **`shared/context/ThemeContext.test.tsx`** theme resolution across `light`/`dark`/`system`, persistence to `localStorage`, and live response to a simulated OS preference change.
