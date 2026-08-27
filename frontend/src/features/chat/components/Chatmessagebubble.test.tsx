import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { describe, it, expect, vi } from "vitest"

vi.mock("@/features/collections/components/PdfPreview", () => ({
  default: () => <div data-testid="pdf-preview" />,
}))

import ChatMessageBubble from "@/features/chat/components/ChatMessageBubble"

function renderWithQueryClient(ui: React.ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>)
}

describe("ChatMessageBubble save-to-note button", () => {
  it("does not render a save button when messageId/projectId are omitted (e.g. the ephemeral streaming bubble)", () => {
    render(<ChatMessageBubble role="assistant" content="Thinking…" />)
    expect(screen.queryByRole("button", { name: "Save to note" })).not.toBeInTheDocument()
  })

  it("does not render a save button on user messages, even with messageId/projectId present", () => {
    render(
      <ChatMessageBubble
        role="user"
        content="What was Q3 revenue?"
        messageId="msg-1"
        projectId="proj-1"
      />,
    )
    expect(screen.queryByRole("button", { name: "Save to note" })).not.toBeInTheDocument()
  })

  it("renders a save button on a persisted assistant message", () => {
    renderWithQueryClient(
      <ChatMessageBubble
        role="assistant"
        content="Revenue grew 12%."
        messageId="msg-1"
        projectId="proj-1"
      />,
    )
    expect(screen.getByRole("button", { name: "Save to note" })).toBeInTheDocument()
  })
})

describe("ChatMessageBubble", () => {
  it("renders no source list when sources is empty or omitted", () => {
    render(<ChatMessageBubble role="assistant" content="Just an answer." />)
    expect(screen.queryByText("Sources")).not.toBeInTheDocument()
  })

  it("renders a footnote-style source list with index markers", () => {
    render(
      <ChatMessageBubble
        role="assistant"
        content="Revenue grew 12% [1]."
        sources={[{ index: 1, source_name: "q3-report.pdf", collection_id: "c1", item_id: "i1" }]}
      />,
    )
    expect(screen.getByText("Sources")).toBeInTheDocument()
    expect(screen.getByText("[1]")).toBeInTheDocument()
    expect(screen.getByText("q3-report.pdf")).toBeInTheDocument()
  })

  it("renders a URL source as a shortened, clickable link", () => {
    render(
      <ChatMessageBubble
        role="assistant"
        content="See the announcement [1]."
        sources={[
          {
            index: 1,
            source_name: "https://www.example.com/blog/announcement",
            collection_id: "c1",
            item_id: "i1",
          },
        ]}
      />,
    )
    const link = screen.getByRole("link")
    expect(link).toHaveAttribute("href", "https://www.example.com/blog/announcement")
    expect(link).toHaveAttribute("target", "_blank")
    expect(link.textContent).toContain("example.com/blog/announcement")
  })

  it("renders a PDF/TXT source as a clickable button that opens the item preview modal", async () => {
    const user = userEvent.setup()
    renderWithQueryClient(
      <ChatMessageBubble
        role="assistant"
        content="Revenue grew 12% [1]."
        sources={[
          {
            index: 1,
            source_name: "q3-report.pdf",
            collection_id: "c1",
            item_id: "i1",
            content: "Revenue grew 12% year over year.",
          },
        ]}
      />,
    )
    const sourceButton = screen.getByRole("button", { name: "q3-report.pdf" })
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument()

    await user.click(sourceButton)

    expect(screen.getByRole("dialog")).toBeInTheDocument()
    expect(screen.getAllByText("q3-report.pdf").length).toBeGreaterThan(0)
  })

  it("renders a PDF/TXT source as plain text when it has no collection_id/item_id", () => {
    render(
      <ChatMessageBubble
        role="assistant"
        content="Revenue grew 12% [1]."
        sources={[{ index: 1, source_name: "q3-report.pdf", collection_id: null, item_id: null }]}
      />,
    )
    expect(screen.queryByRole("button", { name: "q3-report.pdf" })).not.toBeInTheDocument()
    expect(screen.getByText("q3-report.pdf")).toBeInTheDocument()
  })

  it("does not render a source list for user messages", () => {
    render(
      <ChatMessageBubble
        role="user"
        content="What was Q3 revenue?"
        sources={[{ index: 1, source_name: "q3-report.pdf", collection_id: "c1", item_id: "i1" }]}
      />,
    )
    expect(screen.queryByText("Sources")).not.toBeInTheDocument()
  })
})
