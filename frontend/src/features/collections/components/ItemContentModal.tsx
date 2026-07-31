import { useEffect, useState } from "react"

import {
  getCollectionItemContentText,
  getCollectionItemContentUrl,
  type CollectionItem,
} from "@/features/collections/api"
import { ApiError } from "@/shared/lib/apiClient"
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/shared/components/ui/dialog"

interface ItemContentModalProps {
  collectionId: string
  item: CollectionItem | null
  onOpenChange: (open: boolean) => void
}

interface ItemContentBodyProps {
  collectionId: string
  item: CollectionItem
}

function ItemContentBody({ collectionId, item }: ItemContentBodyProps) {
  const [text, setText] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(item.source_type === "txt")

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

  if (item.source_type === "pdf") {
    return (
      <iframe
        src={getCollectionItemContentUrl(collectionId, item.id)}
        title={item.name}
        className="size-full border-0"
      />
    )
  }

  if (item.source_type === "txt") {
    return (
      <div className="h-full overflow-y-auto px-5 py-4">
        {loading && <p className="text-sm text-muted-foreground">Loading...</p>}
        {error && <p className="text-sm text-destructive">{error}</p>}
        {!loading && !error && (
          <pre className="whitespace-pre-wrap wrap-break-words font-mono text-sm text-ink">
            {text}
          </pre>
        )}
      </div>
    )
  }

  return null
}

function ItemContentModal({ collectionId, item, onOpenChange }: ItemContentModalProps) {
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
          {item && <ItemContentBody key={item.id} collectionId={collectionId} item={item} />}
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default ItemContentModal