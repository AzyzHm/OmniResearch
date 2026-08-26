import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { MemoryRouter } from "react-router-dom"
import { describe, it, expect, vi, beforeEach } from "vitest"

import ProjectsList from "@/features/projects/pages/ProjectsList"

const project = {
  id: "p1",
  user_id: "u1",
  name: "Test Project",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
}

function renderWithProviders() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <ProjectsList />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("ProjectsList delete flow", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("removes the deleted project from the UI even if the follow-up background refetch never resolves", async () => {
    const user = userEvent.setup()
    let getCallCount = 0

    globalThis.fetch = vi.fn((url: string, options?: RequestInit) => {
      const method = options?.method ?? "GET"

      if (method === "GET" && url.endsWith("/projects")) {
        getCallCount += 1
        if (getCallCount === 1) {
          // Initial load: one project.
          return Promise.resolve(
            new Response(JSON.stringify([project]), {
              status: 200,
              headers: { "content-type": "application/json" },
            }),
          )
        }
        return new Promise(() => {})
      }

      if (method === "DELETE" && url.endsWith(`/projects/${project.id}`)) {
        return Promise.resolve(
          new Response(null, {
            status: 204,
            headers: { "content-type": "application/json" },
          }),
        )
      }

      return Promise.reject(new Error(`Unhandled fetch: ${method} ${url}`))
    }) as unknown as typeof fetch

    renderWithProviders()

    expect(await screen.findByText("Test Project")).toBeInTheDocument()

    const deleteButton = screen.getByRole("button", { name: /delete project/i })
    await user.click(deleteButton)

    const confirmButton = await screen.findByRole("button", { name: "Confirm" })
    await user.click(confirmButton)

    expect(screen.queryByText("Test Project")).not.toBeInTheDocument()
  })
})
