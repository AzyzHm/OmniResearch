import { useState } from "react"
import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { describe, it, expect, vi, beforeEach } from "vitest"

import ChatsSidebar from "@/features/chat/components/ChatsSidebar"
import type { Chat } from "@/features/chat/api"

const chat: Chat = {
  id: "chat-1",
  project_id: "proj-1",
  name: "My Chat",
  created_at: "2026-01-01T00:00:00Z",
}

function Harness() {
  const [selected, setSelected] = useState<Chat | null>(chat)
  return (
    <>
      <p data-testid="content-pane">
        {selected ? `Showing: ${selected.name}` : "No chat selected"}
      </p>
      <ChatsSidebar projectId="proj-1" selectedChatId={selected?.id ?? null} onSelect={setSelected} />
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

function mockChatFetch() {
  let getCallCount = 0
  globalThis.fetch = vi.fn((url: string, options?: RequestInit) => {
    const method = options?.method ?? "GET"

    if (method === "GET" && url.includes("/chats")) {
      getCallCount += 1
      const data = getCallCount === 1 ? [chat] : []
      return Promise.resolve(
        new Response(JSON.stringify(data), {
          status: 200,
          headers: { "content-type": "application/json" },
        })
      )
    }

    if (method === "DELETE" && url.endsWith(`/chats/${chat.id}`)) {
      return Promise.resolve(new Response(null, { status: 204 }))
    }

    return Promise.reject(new Error(`Unhandled fetch: ${method} ${url}`))
  }) as unknown as typeof fetch
}

describe("ChatsSidebar mobile visibility", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("does not hide rename/delete behind hover-only opacity — visible by default, hover-gated only from md up", async () => {
    mockChatFetch()
    renderWithProviders()
    await screen.findByText("My Chat", { selector: "span" })

    const renameButton = screen.getByRole("button", { name: "Rename chat" })
    const wrapper = renameButton.parentElement!
    const classes = wrapper.className.split(/\s+/)

    expect(classes).toContain("opacity-100")
    expect(classes).toContain("md:opacity-0")
    expect(classes).toContain("md:group-hover:opacity-100")
    expect(classes).not.toContain("opacity-0")
  })
})