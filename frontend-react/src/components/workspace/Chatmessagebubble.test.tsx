import { render, screen } from "@testing-library/react"
import { describe, it, expect } from "vitest"

import ChatMessageBubble from "@/components/workspace/ChatMessageBubble"

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
        sources={[
          { index: 1, source_name: "q3-report.pdf", collection_id: "c1", item_id: "i1" },
        ]}
      />
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
      />
    )
    const link = screen.getByRole("link")
    expect(link).toHaveAttribute("href", "https://www.example.com/blog/announcement")
    expect(link).toHaveAttribute("target", "_blank")
    expect(link.textContent).toContain("example.com/blog/announcement")
  })

  it("does not render a source list for user messages", () => {
    render(
      <ChatMessageBubble
        role="user"
        content="What was Q3 revenue?"
        sources={[
          { index: 1, source_name: "q3-report.pdf", collection_id: "c1", item_id: "i1" },
        ]}
      />
    )
    expect(screen.queryByText("Sources")).not.toBeInTheDocument()
  })
})