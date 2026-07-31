import { useState } from "react"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { describe, it, expect, vi, beforeEach } from "vitest"

import CollectionsSidebar from "@/features/collections/components/CollectionsSidebar"
import type { Collection } from "@/features/collections/api"

const collection: Collection = {
  id: "col-1",
  project_id: "proj-1",
  name: "Background Reading",
  created_at: "2026-01-01T00:00:00Z",
}

function Harness() {
  const [selected, setSelected] = useState<Collection | null>(collection)
  return (
    <>
      <p data-testid="content-pane">
        {selected ? `Showing: ${selected.name}` : "No collection selected"}
      </p>
      <CollectionsSidebar
        projectId="proj-1"
        selectedCollectionId={selected?.id ?? null}
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
    </QueryClientProvider>
  )
}

function mockCollectionFetch() {
  let getCallCount = 0
  globalThis.fetch = vi.fn((url: string, options?: RequestInit) => {
    const method = options?.method ?? "GET"

    if (method === "GET" && url.includes("/collections")) {
      getCallCount += 1
      const data = getCallCount === 1 ? [collection] : []
      return Promise.resolve(
        new Response(JSON.stringify(data), {
          status: 200,
          headers: { "content-type": "application/json" },
        })
      )
    }

    if (method === "DELETE" && url.endsWith(`/collections/${collection.id}`)) {
      return Promise.resolve(new Response(null, { status: 204 }))
    }

    return Promise.reject(new Error(`Unhandled fetch: ${method} ${url}`))
  }) as unknown as typeof fetch
}

describe("CollectionsSidebar mobile visibility", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("does not hide delete behind hover-only opacity — visible by default, hover-gated only from md up", async () => {
    mockCollectionFetch()
    renderWithProviders()
    await screen.findByText("Background Reading", { selector: "span" })

    const deleteButton = screen.getByRole("button", { name: "Delete collection" })
    const classes = deleteButton.className.split(/\s+/)

    expect(classes).toContain("opacity-100")
    expect(classes).toContain("md:opacity-0")
    expect(classes).toContain("md:group-hover:opacity-100")
    expect(classes).not.toContain("opacity-0")
  })

  it("clears the selection when the currently-selected collection is deleted, instead of leaving stale content showing", async () => {
    mockCollectionFetch()
    renderWithProviders()
    const user = userEvent.setup()
    await screen.findByText("Background Reading", { selector: "span" })
    expect(screen.getByTestId("content-pane")).toHaveTextContent("Showing: Background Reading")

    await user.click(await screen.findByRole("button", { name: "Delete collection" }))
    await user.click(await screen.findByRole("button", { name: "Confirm delete" }))

    await vi.waitFor(() => {
      expect(screen.getByTestId("content-pane")).toHaveTextContent("No collection selected")
    })
  })
})