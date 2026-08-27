import { render, screen } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { describe, it, expect, vi, beforeEach } from "vitest"

import CollectionItemsPanel from "@/features/collections/components/CollectionItemsPanel"
import type { Collection, CollectionItem } from "@/features/collections/api"

const collection: Collection = {
  id: "col-1",
  project_id: "proj-1",
  name: "Everything",
  created_at: "2026-01-01T00:00:00Z",
}

function renderWithProviders(items: CollectionItem[]) {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve(
      new Response(JSON.stringify(items), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      })
    )
  ) as unknown as typeof fetch

  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <CollectionItemsPanel collection={collection} />
    </QueryClientProvider>
  )
}

describe("CollectionItemsPanel", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("shows both the file-upload control and the URL/search controls together, for any collection", async () => {
    renderWithProviders([])

    expect(await screen.findByText(/No items yet/)).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Upload files/ })).toBeInTheDocument()
    expect(screen.getByPlaceholderText("https://example.com/article")).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Add URL/ })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: /Search the web/ })).toBeInTheDocument()
  })

  it("renders a PDF item as plain text and a URL item as a link, based on the item's own source_type", async () => {
    const items: CollectionItem[] = [
      {
        id: "item-1",
        collection_id: "col-1",
        name: "report.pdf",
        source_type: "pdf",
        is_active: true,
        status: "ready",
        chunk_count: 4,
        page_count: 12,
        word_count: null,
        error_message: null,
        created_at: "2026-01-01T00:00:00Z",
      },
      {
        id: "item-2",
        collection_id: "col-1",
        name: "https://example.com/article",
        source_type: "url",
        is_active: true,
        status: "ready",
        chunk_count: 2,
        page_count: null,
        word_count: null,
        error_message: null,
        created_at: "2026-01-01T00:00:00Z",
      },
    ]
    renderWithProviders(items)

    expect(await screen.findByText("report.pdf")).toBeInTheDocument()
    const link = screen.getByRole("link", { name: /example\.com\/article/ })
    expect(link).toHaveAttribute("href", "https://example.com/article")
  })

  it("shows a type badge and a page-count badge for a ready PDF item", async () => {
    const items: CollectionItem[] = [
      {
        id: "item-1",
        collection_id: "col-1",
        name: "report.pdf",
        source_type: "pdf",
        is_active: true,
        status: "ready",
        chunk_count: 4,
        page_count: 12,
        word_count: null,
        error_message: null,
        created_at: "2026-01-01T00:00:00Z",
      },
    ]
    renderWithProviders(items)

    expect(await screen.findByText("PDF")).toBeInTheDocument()
    expect(screen.getByText("12 pages")).toBeInTheDocument()
  })

  it("shows a type badge and a word-count badge for a ready TXT item", async () => {
    const items: CollectionItem[] = [
      {
        id: "item-1",
        collection_id: "col-1",
        name: "notes.txt",
        source_type: "txt",
        is_active: true,
        status: "ready",
        chunk_count: 1,
        page_count: null,
        word_count: 2000,
        error_message: null,
        created_at: "2026-01-01T00:00:00Z",
      },
    ]
    renderWithProviders(items)

    expect(await screen.findByText("TXT")).toBeInTheDocument()
    expect(screen.getByText("2,000 words")).toBeInTheDocument()
  })

  it("shows only a type badge for a URL item, with no second count badge", async () => {
    const items: CollectionItem[] = [
      {
        id: "item-2",
        collection_id: "col-1",
        name: "https://example.com/article",
        source_type: "url",
        is_active: true,
        status: "ready",
        chunk_count: 2,
        page_count: null,
        word_count: null,
        error_message: null,
        created_at: "2026-01-01T00:00:00Z",
      },
    ]
    renderWithProviders(items)

    expect(await screen.findByText("URL")).toBeInTheDocument()
    expect(screen.queryByText(/pages|words/)).not.toBeInTheDocument()
  })

  it("does not show a count badge for a PDF that is still processing", async () => {
    const items: CollectionItem[] = [
      {
        id: "item-1",
        collection_id: "col-1",
        name: "report.pdf",
        source_type: "pdf",
        is_active: false,
        status: "processing",
        chunk_count: 0,
        page_count: null,
        word_count: null,
        error_message: null,
        created_at: "2026-01-01T00:00:00Z",
      },
    ]
    renderWithProviders(items)

    expect(await screen.findByText("PDF")).toBeInTheDocument()
    expect(screen.queryByText(/pages/)).not.toBeInTheDocument()
  })
})