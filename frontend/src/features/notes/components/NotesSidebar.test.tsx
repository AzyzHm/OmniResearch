import { useState } from "react"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { describe, it, expect, vi, beforeEach } from "vitest"

import NotesSidebar from "@/features/notes/components/NotesSidebar"
import type { Note } from "@/features/notes/api"

const note: Note = {
  id: "note-1",
  project_id: "proj-1",
  name: "Key Findings",
  created_at: "2026-01-01T00:00:00Z",
}

function Harness() {
  const [selected, setSelected] = useState<Note | null>(note)
  return (
    <>
      <p data-testid="content-pane">
        {selected ? `Showing: ${selected.name}` : "No note selected"}
      </p>
      <NotesSidebar
        projectId="proj-1"
        selectedNoteId={selected?.id ?? null}
        onSelect={setSelected}
      />
    </>
  )
}

function renderWithProviders() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <Harness />
    </QueryClientProvider>,
  )
}

function mockNoteFetch() {
  let getCallCount = 0
  globalThis.fetch = vi.fn((url: string, options?: RequestInit) => {
    const method = options?.method ?? "GET"

    if (method === "GET" && url.endsWith("/projects/proj-1/notes")) {
      getCallCount += 1
      const data = getCallCount === 1 ? [note] : []
      return Promise.resolve(
        new Response(JSON.stringify(data), {
          status: 200,
          headers: { "content-type": "application/json" },
        }),
      )
    }

    if (method === "DELETE" && url.endsWith(`/notes/${note.id}`)) {
      return Promise.resolve(new Response(null, { status: 204 }))
    }

    return Promise.reject(new Error(`Unhandled fetch: ${method} ${url}`))
  }) as unknown as typeof fetch
}

describe("NotesSidebar", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("does not hide rename/delete behind hover-only opacity — visible by default, hover-gated only from md up", async () => {
    mockNoteFetch()
    renderWithProviders()
    await screen.findByText("Key Findings", { selector: "span" })

    const deleteButton = screen.getByRole("button", { name: "Delete note" })
    const classes = deleteButton.parentElement!.className.split(/\s+/)

    expect(classes).toContain("opacity-100")
    expect(classes).toContain("md:opacity-0")
    expect(classes).toContain("md:group-hover:opacity-100")
    expect(classes).not.toContain("opacity-0")
  })

  it("clears the selection when the currently-selected note is deleted, instead of leaving stale content showing", async () => {
    mockNoteFetch()
    renderWithProviders()
    const user = userEvent.setup()
    await screen.findByText("Key Findings", { selector: "span" })
    expect(screen.getByTestId("content-pane")).toHaveTextContent("Showing: Key Findings")

    await user.click(await screen.findByRole("button", { name: "Delete note" }))
    await user.click(await screen.findByRole("button", { name: "Confirm delete" }))

    await vi.waitFor(() => {
      expect(screen.getByTestId("content-pane")).toHaveTextContent("No note selected")
    })
  })
})
