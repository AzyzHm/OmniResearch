import { useEffect, useRef, useState } from "react"
import { Document, Page, pdfjs, type TextContent } from "react-pdf"
import "react-pdf/dist/Page/TextLayer.css"
import pdfWorkerSrc from "pdfjs-dist/build/pdf.worker.min.mjs?url"

import { getCollectionItemContentUrl } from "@/features/collections/api"
import { computeItemHighlights, escapeHtml, type TextLayerItemLike } from "@/features/collections/lib/textHighlight"

pdfjs.GlobalWorkerOptions.workerSrc = pdfWorkerSrc

interface PdfPreviewProps {
  collectionId: string
  itemId: string
  highlightText?: string | null
}

function PdfPreview({ collectionId, itemId, highlightText }: PdfPreviewProps) {
  const [pdfData, setPdfData] = useState<ArrayBuffer | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [numPages, setNumPages] = useState(0)
  const [containerWidth, setContainerWidth] = useState(0)
  const [highlightsByPage, setHighlightsByPage] = useState<Map<number, Map<number, [number, number]>>>(
    new Map()
  )

  const containerRef = useRef<HTMLDivElement | null>(null)
  const foundMatchRef = useRef(false)
  const scrolledRef = useRef(false)

  useEffect(() => {
    let cancelled = false
    fetch(getCollectionItemContentUrl(collectionId, itemId), {
      credentials: "include",
      cache: "no-store",
    })
      .then((response) => {
        if (!response.ok) throw new Error(`Request failed with ${response.status}`)
        return response.arrayBuffer()
      })
      .then((buffer) => {
        if (!cancelled) setPdfData(buffer)
      })
      .catch(() => {
        if (!cancelled) setError("Couldn't load this file's content.")
      })

    return () => {
      cancelled = true
    }
  }, [collectionId, itemId])

  useEffect(() => {
    if (containerRef.current) {
      setContainerWidth(containerRef.current.clientWidth)
    }
  }, [pdfData])

  function handleGetTextSuccess(pageNumber: number, textContent: TextContent) {
    if (!highlightText || foundMatchRef.current) return
    const highlights = computeItemHighlights(textContent.items as TextLayerItemLike[], highlightText)
    if (!highlights) return
    foundMatchRef.current = true
    setHighlightsByPage((prev) => {
      const next = new Map(prev)
      next.set(pageNumber, highlights)
      return next
    })
  }

  function renderPageText(pageNumber: number, itemIndex: number, str: string): string {
    const range = highlightsByPage.get(pageNumber)?.get(itemIndex)
    if (!range) return escapeHtml(str)
    const [start, end] = range
    return (
      escapeHtml(str.slice(0, start)) +
      `<mark class="pdf-chunk-highlight rounded-sm bg-teal/12 text-transparent">${escapeHtml(str.slice(start, end))}</mark>` +
      escapeHtml(str.slice(end))
    )
  }

  function handleTextLayerRendered(pageNumber: number) {
    if (scrolledRef.current || !highlightsByPage.has(pageNumber)) return
    scrolledRef.current = true
    containerRef.current
      ?.querySelector<HTMLElement>(".pdf-chunk-highlight")
      ?.scrollIntoView({ behavior: "smooth", block: "center" })
  }

  return (
    <div ref={containerRef} className="h-full overflow-y-auto bg-muted px-4 py-4">
      {error && <p className="text-sm text-destructive">{error}</p>}

      {!error && pdfData && (
        <Document
          file={pdfData}
          onLoadSuccess={(doc) => setNumPages(doc.numPages)}
          onLoadError={() => setError("Couldn't render this PDF.")}
          loading={<p className="text-sm text-muted-foreground">Rendering PDF...</p>}
          error={<p className="text-sm text-destructive">Couldn't render this PDF.</p>}
          className="flex flex-col items-center gap-4"
        >
          {Array.from({ length: numPages }, (_, i) => i + 1).map((pageNumber) => (
            <Page
              key={pageNumber}
              pageNumber={pageNumber}
              width={containerWidth > 0 ? Math.min(containerWidth - 32, 800) : undefined}
              className="shadow-sm"
              renderAnnotationLayer={false}
              onGetTextSuccess={(textContent) => handleGetTextSuccess(pageNumber, textContent)}
              onRenderTextLayerSuccess={() => handleTextLayerRendered(pageNumber)}
              customTextRenderer={({ itemIndex, str }) => renderPageText(pageNumber, itemIndex, str)}
            />
          ))}
        </Document>
      )}
    </div>
  )
}

export default PdfPreview