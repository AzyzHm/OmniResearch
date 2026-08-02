import { useEffect } from "react"
import { render, screen, waitFor } from "@testing-library/react"
import { describe, it, expect, vi, beforeEach } from "vitest"

const fakePageItems = [
  { str: "Intro paragraph." },
  { str: "Revenue grew", hasEOL: true },
  { str: "12% year over year." },
]

interface FakeDocumentProps {
  onLoadSuccess?: (doc: { numPages: number }) => void
  children?: React.ReactNode
}

interface FakePageProps {
  pageNumber: number
  onGetTextSuccess?: (textContent: { items: typeof fakePageItems; styles: object }) => void
  onRenderTextLayerSuccess?: () => void
  customTextRenderer?: (props: {
    pageIndex: number
    pageNumber: number
    itemIndex: number
    str: string
  }) => string
}

function FakeDocument({ onLoadSuccess, children }: FakeDocumentProps) {
  useEffect(() => {
    onLoadSuccess?.({ numPages: 1 })
  }, [])
  return <div data-testid="pdf-document">{children}</div>
}

function FakePage({ pageNumber, onGetTextSuccess, onRenderTextLayerSuccess, customTextRenderer }: FakePageProps) {
  useEffect(() => {
    onGetTextSuccess?.({ items: fakePageItems, styles: {} })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])
  useEffect(() => {
    onRenderTextLayerSuccess?.()
  }, [customTextRenderer])
  return (
    <div data-testid={`pdf-page-${pageNumber}`}>
      {fakePageItems.map((item, itemIndex) => (
        <span
          key={itemIndex}
          data-testid={`pdf-item-${pageNumber}-${itemIndex}`}
          dangerouslySetInnerHTML={{
            __html: customTextRenderer
              ? customTextRenderer({ pageIndex: pageNumber - 1, pageNumber, itemIndex, str: item.str })
              : item.str,
          }}
        />
      ))}
    </div>
  )
}

vi.mock("react-pdf", () => ({
  pdfjs: { GlobalWorkerOptions: {} },
  Document: FakeDocument,
  Page: FakePage,
}))

const { default: PdfPreview } = await import("@/features/collections/components/PdfPreview")

function mockPdfFetch(ok = true) {
  globalThis.fetch = vi.fn(() =>
    Promise.resolve({
      ok,
      status: ok ? 200 : 500,
      arrayBuffer: () => Promise.resolve(new ArrayBuffer(8)),
    })
  ) as unknown as typeof fetch
}

describe("PdfPreview", () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it("fetches the PDF with credentials and renders the document once loaded", async () => {
    mockPdfFetch()
    render(<PdfPreview collectionId="c1" itemId="i1" />)

    await screen.findByTestId("pdf-document")

    expect(fetch).toHaveBeenCalledWith(
      expect.stringContaining("/collections/c1/items/i1/content"),
      expect.objectContaining({ credentials: "include" })
    )
  })

  it("shows an error message when the file can't be fetched", async () => {
    mockPdfFetch(false)
    render(<PdfPreview collectionId="c1" itemId="i1" />)

    expect(await screen.findByText("Couldn't load this file's content.")).toBeInTheDocument()
    expect(screen.queryByTestId("pdf-document")).not.toBeInTheDocument()
  })

  it("wraps only the items that make up the cited chunk in a highlight mark", async () => {
    mockPdfFetch()
    render(
      <PdfPreview collectionId="c1" itemId="i1" highlightText="Revenue grew 12% year over year." />
    )

    const item1 = await screen.findByTestId("pdf-item-1-1")
    const item2 = await screen.findByTestId("pdf-item-1-2")
    const item0 = screen.getByTestId("pdf-item-1-0")

    await waitFor(() => expect(item1.querySelector("mark.pdf-chunk-highlight")).not.toBeNull())
    expect(item2.querySelector("mark.pdf-chunk-highlight")).not.toBeNull()
    expect(item0.querySelector("mark.pdf-chunk-highlight")).toBeNull()
    expect(item1.textContent).toBe("Revenue grew")
    expect(item2.textContent).toBe("12% year over year.")
  })

  it("doesn't render any highlight when there's no highlightText", async () => {
    mockPdfFetch()
    render(<PdfPreview collectionId="c1" itemId="i1" />)

    await screen.findByTestId("pdf-page-1")
    expect(document.querySelector("mark.pdf-chunk-highlight")).not.toBeInTheDocument()
  })

  it("scrolls the highlighted mark into view once it renders", async () => {
    mockPdfFetch()
    const scrollSpy = vi.spyOn(Element.prototype, "scrollIntoView")

    render(
      <PdfPreview collectionId="c1" itemId="i1" highlightText="Revenue grew 12% year over year." />
    )

    await waitFor(() => expect(scrollSpy).toHaveBeenCalledWith({ behavior: "smooth", block: "center" }))
    expect((scrollSpy.mock.instances[0] as HTMLElement).className).toContain("pdf-chunk-highlight")
  })

  it("doesn't scroll when there's no match to highlight", async () => {
    mockPdfFetch()
    const scrollSpy = vi.spyOn(Element.prototype, "scrollIntoView")

    render(<PdfPreview collectionId="c1" itemId="i1" highlightText="Not present anywhere." />)

    await screen.findByTestId("pdf-page-1")
    expect(scrollSpy).not.toHaveBeenCalled()
  })
})