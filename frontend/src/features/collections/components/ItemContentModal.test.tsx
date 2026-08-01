import { render, screen, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"

import ItemContentModal from "@/features/collections/components/ItemContentModal"

const txtItem = { id: "item-1", name: "notes.txt", source_type: "txt" }

function mockTextResponse(body: string) {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve(new Response(body, { status: 200 }))
  ) as unknown as typeof fetch
}

describe("ItemContentModal TXT highlighting", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("wraps the cited chunk in a <mark> when it's found in the file", async () => {
    mockTextResponse("Intro paragraph.\n\nRevenue grew 12% year over year.\n\nOutro paragraph.")

    render(
      <ItemContentModal
        collectionId="c1"
        item={txtItem}
        onOpenChange={() => {}}
        highlightText="Revenue grew 12% year over year."
      />
    )

    const mark = await waitFor(() => screen.getByText("Revenue grew 12% year over year."))
    expect(mark.tagName).toBe("MARK")
  })

  it("renders the plain text with no <mark> when there's no highlightText", async () => {
    mockTextResponse("Just some file contents.")

    render(
      <ItemContentModal collectionId="c1" item={txtItem} onOpenChange={() => {}} />
    )

    await waitFor(() => screen.getByText("Just some file contents."))
    expect(document.querySelector("mark")).not.toBeInTheDocument()
  })

  it("falls back to plain text (no crash) when the chunk text isn't found verbatim in the file", async () => {
    mockTextResponse("The file content has changed since this citation was generated.")

    render(
      <ItemContentModal
        collectionId="c1"
        item={txtItem}
        onOpenChange={() => {}}
        highlightText="This exact sentence is not in the file."
      />
    )

    await waitFor(() =>
      screen.getByText("The file content has changed since this citation was generated.")
    )
    expect(document.querySelector("mark")).not.toBeInTheDocument()
  })
})