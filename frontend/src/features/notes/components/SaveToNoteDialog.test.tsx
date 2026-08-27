import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { describe, it, expect, vi, beforeEach } from "vitest"

import SaveToNoteDialog from "@/features/notes/components/SaveToNoteDialog"
import type { Note } from "@/features/notes/api"

const note: Note = {
  id: "note-1",
  project_id: "proj-1",
  name: "Key Findings",
  created_at: "2026-01-01T00:00:00Z",
}

function renderDialog(onSaved = vi.fn()) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  const utils = render(
    <QueryClientProvider client={queryClient}>
      <SaveToNoteDialog
        open
        onOpenChange={() => {}}
        projectId="proj-1"
        messageId="msg-1"
        onSaved={onSaved}
      />
    </QueryClientProvider>,
  )
  return { ...utils, onSaved }
}

describe("SaveToNoteDialog", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("lists existing notes and saves the message into the chosen one", async () => {
    const user = userEvent.setup()
    globalThis.fetch = vi.fn((url: string, options?: RequestInit) => {
      const method = options?.method ?? "GET"
      if (method === "GET" && url.endsWith("/projects/proj-1/notes")) {
        return Promise.resolve(
          new Response(JSON.stringify([note]), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
        )
      }
      if (method === "POST" && url.endsWith("/notes/note-1/items")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: "item-1",
              note_id: "note-1",
              message_id: "msg-1",
              chat_id: "chat-1",
              role: "assistant",
              content: "Hi",
              created_at: "2026-01-01T00:00:00Z",
            }),
            { status: 201, headers: { "content-type": "application/json" } },
          ),
        )
      }
      return Promise.reject(new Error(`Unhandled fetch: ${method} ${url}`))
    }) as unknown as typeof fetch

    const { onSaved } = renderDialog()
    await screen.findByRole("button", { name: /Key Findings/ })
    await user.click(screen.getByRole("button", { name: /Key Findings/ }))

    await vi.waitFor(() => expect(onSaved).toHaveBeenCalled())
    expect(await screen.findByText("Saved ✓")).toBeInTheDocument()
  })

  it("treats an already-saved message (409) as a soft success, not an error", async () => {
    const user = userEvent.setup()
    globalThis.fetch = vi.fn((url: string, options?: RequestInit) => {
      const method = options?.method ?? "GET"
      if (method === "GET" && url.endsWith("/projects/proj-1/notes")) {
        return Promise.resolve(
          new Response(JSON.stringify([note]), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
        )
      }
      if (method === "POST" && url.endsWith("/notes/note-1/items")) {
        return Promise.resolve(
          new Response(JSON.stringify({ detail: "This message is already saved to this note." }), {
            status: 409,
            headers: { "content-type": "application/json" },
          }),
        )
      }
      return Promise.reject(new Error(`Unhandled fetch: ${method} ${url}`))
    }) as unknown as typeof fetch

    const { onSaved } = renderDialog()
    await user.click(await screen.findByRole("button", { name: /Key Findings/ }))

    await vi.waitFor(() => expect(onSaved).toHaveBeenCalled())
    expect(screen.queryByText("Couldn't save this message.")).not.toBeInTheDocument()
  })

  it("creates a new note and saves the message into it in one step", async () => {
    const user = userEvent.setup()
    globalThis.fetch = vi.fn((url: string, options?: RequestInit) => {
      const method = options?.method ?? "GET"
      if (method === "GET" && url.endsWith("/projects/proj-1/notes")) {
        return Promise.resolve(
          new Response(JSON.stringify([]), {
            status: 200,
            headers: { "content-type": "application/json" },
          }),
        )
      }
      if (method === "POST" && url.endsWith("/projects/proj-1/notes")) {
        return Promise.resolve(
          new Response(JSON.stringify({ ...note, name: "New Note" }), {
            status: 201,
            headers: { "content-type": "application/json" },
          }),
        )
      }
      if (method === "POST" && url.endsWith("/notes/note-1/items")) {
        return Promise.resolve(
          new Response(
            JSON.stringify({
              id: "item-1",
              note_id: "note-1",
              message_id: "msg-1",
              chat_id: "chat-1",
              role: "assistant",
              content: "Hi",
              created_at: "2026-01-01T00:00:00Z",
            }),
            { status: 201, headers: { "content-type": "application/json" } },
          ),
        )
      }
      return Promise.reject(new Error(`Unhandled fetch: ${method} ${url}`))
    }) as unknown as typeof fetch

    const { onSaved } = renderDialog()
    await screen.findByText("No notes yet. Create one below.")
    await user.click(screen.getByRole("button", { name: "New note" }))
    await user.type(screen.getByPlaceholderText("New note name"), "New Note")
    await user.click(screen.getByRole("button", { name: "Create & save" }))

    await vi.waitFor(() => expect(onSaved).toHaveBeenCalled())
  })
})
