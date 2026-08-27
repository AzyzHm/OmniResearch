import { useRef, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { ExternalLink, Eye, Link2, Search, Trash2, Upload } from "lucide-react"

import {
  addCollectionUrl,
  bulkUpdateCollectionItems,
  deleteCollectionItem,
  listCollectionItems,
  uploadCollectionFiles,
  type Collection,
  type CollectionItem,
} from "@/features/collections/api"
import { ApiError } from "@/shared/lib/apiClient"
import { shortenUrl } from "@/shared/lib/shortenUrl"
import { Button } from "@/shared/components/ui/button"
import { Input } from "@/shared/components/ui/input"
import StatusBadge from "@/features/collections/components/StatusBadge"
import ItemMetaBadges from "@/features/collections/components/ItemMetaBadges"
import ItemContentModal from "@/features/collections/components/ItemContentModal"
import SearchModal from "@/features/collections/components/SearchModal"

const UPLOAD_ACCEPT = ".pdf,.txt"

interface CollectionItemsPanelProps {
  collection: Collection
}

function CollectionItemsPanel({ collection }: CollectionItemsPanelProps) {
  const queryClient = useQueryClient()
  const queryKey = ["collection-items", collection.id]
  const fileInputRef = useRef<HTMLInputElement>(null)

  const { data: items, isLoading } = useQuery({
    queryKey,
    queryFn: () => listCollectionItems(collection.id),
    refetchInterval: (query) => {
      const data = query.state.data
      return data?.some((item) => item.status === "processing") ? 3000 : false
    },
  })

  const [urlValue, setUrlValue] = useState("")
  const [urlError, setUrlError] = useState<string | null>(null)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const [deletingId, setDeletingId] = useState<string | null>(null)
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null)
  const [pendingChanges, setPendingChanges] = useState<Record<string, boolean>>({})
  const [searchModalOpen, setSearchModalOpen] = useState(false)
  const [searchInstance, setSearchInstance] = useState(0)
  const [previewItem, setPreviewItem] = useState<CollectionItem | null>(null)

  const uploadMutation = useMutation({
    mutationFn: (files: File[]) => uploadCollectionFiles(collection.id, files),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
      setUploadError(null)
    },
    onError: (err) => {
      setUploadError(err instanceof ApiError ? err.message : "Upload failed.")
    },
  })

  const addUrlMutation = useMutation({
    mutationFn: (url: string) => addCollectionUrl(collection.id, url),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
      setUrlValue("")
      setUrlError(null)
    },
    onError: (err) => {
      setUrlError(err instanceof ApiError ? err.message : "Something went wrong.")
    },
  })

  const bulkMutation = useMutation({
    mutationFn: (updates: { item_id: string; is_active: boolean }[]) =>
      bulkUpdateCollectionItems(collection.id, updates),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey })
      setPendingChanges({})
    },
  })

  const [deleteItemError, setDeleteItemError] = useState<string | null>(null)

  const deleteMutation = useMutation({
    mutationFn: (itemId: string) => deleteCollectionItem(collection.id, itemId),
    onMutate: async (itemId) => {
      setDeletingId(itemId)
      setDeleteItemError(null)
      await queryClient.cancelQueries({ queryKey })
    },
    onSuccess: (_data, itemId) => {
      queryClient.setQueryData<CollectionItem[]>(queryKey, (old) =>
        old ? old.filter((i) => i.id !== itemId) : old,
      )
      queryClient.invalidateQueries({ queryKey })
    },
    onError: (err) => {
      setDeleteItemError(err instanceof ApiError ? err.message : "Couldn't delete the item.")
    },
    onSettled: () => {
      setDeletingId(null)
      setConfirmingDeleteId(null)
    },
  })

  function handleFilesSelected(e: React.ChangeEvent<HTMLInputElement>) {
    const files = Array.from(e.target.files ?? [])
    if (files.length > 0) uploadMutation.mutate(files)
    e.target.value = ""
  }

  function handleAddUrl(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = urlValue.trim()
    if (!trimmed) return
    addUrlMutation.mutate(trimmed)
  }

  function toggleItem(item: CollectionItem, nextValue: boolean) {
    setPendingChanges((prev) => {
      const next = { ...prev }
      if (nextValue === item.is_active) {
        delete next[item.id]
      } else {
        next[item.id] = nextValue
      }
      return next
    })
  }

  function saveChanges() {
    const updates = Object.entries(pendingChanges).map(([item_id, is_active]) => ({
      item_id,
      is_active,
    }))
    if (updates.length > 0) bulkMutation.mutate(updates)
  }

  const readyItems = items?.filter((i) => i.status === "ready") ?? []

  function selectAll() {
    setPendingChanges((prev) => {
      const next = { ...prev }
      readyItems.forEach((item) => {
        if (item.is_active) delete next[item.id]
        else next[item.id] = true
      })
      return next
    })
  }

  function deselectAll() {
    setPendingChanges((prev) => {
      const next = { ...prev }
      readyItems.forEach((item) => {
        if (!item.is_active) delete next[item.id]
        else next[item.id] = false
      })
      return next
    })
  }

  const dirty = Object.keys(pendingChanges).length > 0

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      <div className="mb-4 flex items-start justify-between">
        <div>
          <h2 className="font-display text-lg font-medium text-ink">{collection.name}</h2>
          <p className="text-sm text-muted-foreground">
            {items?.length ?? 0} item{items?.length === 1 ? "" : "s"}
          </p>
        </div>

        {dirty && (
          <Button type="button" onClick={saveChanges} disabled={bulkMutation.isPending}>
            {bulkMutation.isPending ? "Saving..." : "Save changes"}
          </Button>
        )}
      </div>

      {readyItems.length > 0 && (
        <div className="mb-4 flex gap-2">
          <Button type="button" variant="outline" size="sm" onClick={selectAll}>
            Select all
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={deselectAll}>
            Deselect all
          </Button>
        </div>
      )}

      {/* Every collection accepts both uploads and URLs now, so both
          controls render together rather than switching on collection type. */}
      <div className="mb-6 flex flex-col gap-4 rounded-xl border border-dashed border-border p-4">
        <div className="flex flex-wrap items-center gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept={UPLOAD_ACCEPT}
            multiple
            className="hidden"
            onChange={handleFilesSelected}
          />
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => fileInputRef.current?.click()}
            disabled={uploadMutation.isPending}
          >
            <Upload className="size-3.5" data-icon="inline-start" />
            {uploadMutation.isPending ? "Uploading..." : "Upload files"}
          </Button>
          <span className="text-xs text-muted-foreground">Accepts {UPLOAD_ACCEPT} files</span>
        </div>

        <div className="border-t border-border/60 pt-4">
          <form onSubmit={handleAddUrl} className="flex flex-wrap items-center gap-2">
            <Link2 className="size-4 shrink-0 text-muted-foreground" />
            <Input
              value={urlValue}
              onChange={(e) => setUrlValue(e.target.value)}
              placeholder="https://example.com/article"
              disabled={addUrlMutation.isPending}
              className="min-w-0 flex-1"
            />
            <Button type="submit" size="sm" disabled={addUrlMutation.isPending || !urlValue.trim()}>
              {addUrlMutation.isPending ? "Adding..." : "Add URL"}
            </Button>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => {
                setSearchInstance((n) => n + 1)
                setSearchModalOpen(true)
              }}
            >
              <Search className="size-3.5" data-icon="inline-start" />
              Search the web
            </Button>
          </form>
        </div>
      </div>

      {urlError && <p className="mb-4 text-sm text-destructive">{urlError}</p>}
      {uploadError && <p className="mb-4 text-sm text-destructive">{uploadError}</p>}
      {deleteItemError && <p className="mb-4 text-sm text-destructive">{deleteItemError}</p>}

      {isLoading && <p className="text-sm text-muted-foreground">Loading items...</p>}

      {!isLoading && items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">No items yet, add one above to get started.</p>
      )}

      {!isLoading && items && items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border">
          {items.map((item) => {
            const checked = pendingChanges[item.id] ?? item.is_active
            const confirming = confirmingDeleteId === item.id
            return (
              <div
                key={item.id}
                className="flex items-center gap-3 border-b border-border px-3 py-2.5 last:border-0 hover:bg-muted/50"
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={item.status !== "ready"}
                  onChange={(e) => toggleItem(item, e.target.checked)}
                  aria-label={`Include ${item.name} in retrieval`}
                  className="size-4 shrink-0 rounded border-input accent-teal disabled:opacity-40"
                />
                <div className="min-w-0 flex-1">
                  {item.source_type === "url" ? (
                    <a
                      href={item.name}
                      target="_blank"
                      rel="noopener noreferrer"
                      title={item.name}
                      className="flex w-full min-w-0 items-center gap-1 text-teal hover:underline"
                    >
                      <span className="min-w-0 truncate">{shortenUrl(item.name)}</span>
                      <ExternalLink className="size-3 shrink-0" />
                    </a>
                  ) : item.status === "ready" && item.storage_path ? (
                    <button
                      type="button"
                      onClick={() => setPreviewItem(item)}
                      title={`View ${item.name}`}
                      aria-label={`View ${item.name}`}
                      className="flex w-full min-w-0 items-center gap-1 text-left text-teal hover:underline"
                    >
                      <span className="min-w-0 truncate">{item.name}</span>
                      <Eye className="size-3 shrink-0" />
                    </button>
                  ) : (
                    <p className="truncate text-ink" title={item.name}>
                      {item.name}
                    </p>
                  )}
                  {item.status === "error" && item.error_message && (
                    <p className="truncate text-xs text-destructive">{item.error_message}</p>
                  )}
                </div>
                <div className="flex shrink-0 flex-wrap items-center justify-end gap-1.5">
                  <StatusBadge status={item.status} />
                  <ItemMetaBadges item={item} />
                  {confirming ? (
                    <div className="flex flex-col items-end gap-1">
                      <Button
                        type="button"
                        size="xs"
                        variant="destructive"
                        disabled={deletingId === item.id}
                        onClick={() => deleteMutation.mutate(item.id)}
                      >
                        {deletingId === item.id ? "Deleting..." : "Confirm"}
                      </Button>
                      <Button
                        type="button"
                        size="xs"
                        variant="ghost"
                        disabled={deletingId === item.id}
                        onClick={() => setConfirmingDeleteId(null)}
                      >
                        Cancel
                      </Button>
                    </div>
                  ) : (
                    <Button
                      type="button"
                      size="icon-xs"
                      variant="ghost"
                      onClick={() => setConfirmingDeleteId(item.id)}
                      aria-label={`Delete ${item.name}`}
                    >
                      <Trash2 className="size-3.5" />
                    </Button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      )}

      <ItemContentModal
        collectionId={collection.id}
        item={previewItem}
        onOpenChange={(open) => {
          if (!open) setPreviewItem(null)
        }}
      />

      <SearchModal
        key={searchInstance}
        open={searchModalOpen}
        onOpenChange={setSearchModalOpen}
        collectionId={collection.id}
        existingUrls={
          new Set((items ?? []).filter((i) => i.source_type === "url").map((i) => i.name))
        }
        onAdded={() => queryClient.invalidateQueries({ queryKey })}
      />
    </div>
  )
}

export default CollectionItemsPanel
