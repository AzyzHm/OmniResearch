import { lazy, Suspense, useEffect, useMemo, useRef, useState } from "react"

import { getCollectionItemContentText, type CollectionItem } from "@/features/collections/api"
import { ApiError } from "@/shared/lib/apiClient"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/shared/components/ui/dialog"
import { findHighlightRange } from "@/features/collections/lib/textHighlight"

const PdfPreview = lazy(() => import("@/features/collections/components/PdfPreview"))

type PreviewableItem = Pick<CollectionItem, "id" | "name" | "source_type">

interface ItemContentModalProps {
  collectionId: string
  item: PreviewableItem | null
  onOpenChange: (open: boolean) => void
  highlightText?: string | null
}

interface ItemContentBodyProps {
  collectionId: string
  item: PreviewableItem
  highlightText?: string | null
}

function ItemContentBody({ collectionId, item, highlightText }: ItemContentBodyProps) {
  const [text, setText] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(item.source_type === "txt")
  const highlightRef = useRef<HTMLElement | null>(null)

  useEffect(() => {
    if (item.source_type !== "txt") return

    let cancelled = false
    getCollectionItemContentText(collectionId, item.id)
      .then((content) => {
        if (!cancelled) setText(content)
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Couldn't load this file's content.")
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [collectionId, item.id, item.source_type])

  const highlightSplit = useMemo(() => {
    if (text === null) return null
    const range = findHighlightRange(text, highlightText)
    if (!range) return null
    return {
      before: text.slice(0, range.start),
      match: text.slice(range.start, range.end),
      after: text.slice(range.end),
    }
  }, [text, highlightText])

  useEffect(() => {
    highlightRef.current?.scrollIntoView({ behavior: "smooth", block: "center" })
  }, [highlightSplit])

  if (item.source_type === "pdf") {
    return (
      <Suspense fallback={<p className="p-4 text-sm text-muted-foreground">Loading...</p>}>
        <PdfPreview collectionId={collectionId} itemId={item.id} highlightText={highlightText} />
      </Suspense>
    )
  }

  if (item.source_type === "txt") {
    return (
      <div className="h-full overflow-y-auto px-5 py-4">
        {loading && <p className="text-sm text-muted-foreground">Loading...</p>}
        {error && <p className="text-sm text-destructive">{error}</p>}
        {!loading && !error && (
          <pre className="whitespace-pre-wrap wrap-break-words font-mono text-sm text-ink">
            {highlightSplit ? (
              <>
                {highlightSplit.before}
                <mark ref={highlightRef} className="rounded-sm bg-teal/25 text-ink">
                  {highlightSplit.match}
                </mark>
                {highlightSplit.after}
              </>
            ) : (
              text
            )}
          </pre>
        )}
      </div>
    )
  }

  return null
}

function ItemContentModal({ collectionId, item, onOpenChange, highlightText }: ItemContentModalProps) {
  const open = item !== null

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex h-[85vh] w-[92vw] max-w-4xl flex-col gap-0 p-0">
        <DialogHeader className="mb-0 border-b border-border px-5 py-4 pr-10">
          <DialogTitle className="truncate" title={item?.name}>
            {item?.name}
          </DialogTitle>
        </DialogHeader>

        <div className="min-h-0 flex-1 overflow-hidden">
          {item && (
            <ItemContentBody
              key={item.id}
              collectionId={collectionId}
              item={item}
              highlightText={highlightText}
            />
          )}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default ItemContentModal