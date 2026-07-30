import { useState } from "react"
import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
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

describe("ChatsSidebar delete flow", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("clears the selection (and the content pane) when the selected chat is deleted", async () => {
    const user = userEvent.setup()
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

    renderWithProviders()

    expect(screen.getByTestId("content-pane")).toHaveTextContent("Showing: My Chat")
    await screen.findByText("My Chat", { selector: "span" })

    await user.click(screen.getByRole("button", { name: "Delete chat" }))
    await user.click(await screen.findByRole("button", { name: "Confirm delete" }))

    expect(await screen.findByTestId("content-pane")).toHaveTextContent(
      "No chat selected"
    )
  })
})