import { useRef, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { Link2, Trash2, Upload } from "lucide-react"

import {
  addCollectionUrl,
  bulkUpdateCollectionItems,
  deleteCollectionItem,
  listCollectionItems,
  uploadCollectionFiles,
  type Collection,
  type CollectionItem,
} from "@/api/collections"
import { ApiError } from "@/lib/apiClient"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import StatusBadge from "@/components/workspace/StatusBadge"

const EXT_BY_TYPE: Record<string, string> = {
  documents: ".pdf",
  text: ".txt",
}

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
  const [pendingChanges, setPendingChanges] = useState<Record<string, boolean>>({})

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

  const deleteMutation = useMutation({
    mutationFn: (itemId: string) => deleteCollectionItem(collection.id, itemId),
    onMutate: (itemId) => setDeletingId(itemId),
    onSuccess: (_data, itemId) => {
      queryClient.setQueryData<CollectionItem[]>(queryKey, (old) =>
        old ? old.filter((i) => i.id !== itemId) : old
      )
      queryClient.invalidateQueries({ queryKey })
    },
    onSettled: () => setDeletingId(null),
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

  const dirty = Object.keys(pendingChanges).length > 0
  const accept = EXT_BY_TYPE[collection.type]

  return (
    <div className="flex-1 px-6 py-6">
      <div className="mb-6 flex items-start justify-between">
        <div>
          <h2 className="font-display text-lg font-medium text-ink">
            {collection.name}
          </h2>
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

      <div className="mb-6 flex flex-wrap items-center gap-3 rounded-xl border border-dashed border-border p-4">
        {collection.type === "urls" ? (
          <form onSubmit={handleAddUrl} className="flex flex-1 items-center gap-2">
            <Link2 className="size-4 shrink-0 text-muted-foreground" />
            <Input
              value={urlValue}
              onChange={(e) => setUrlValue(e.target.value)}
              placeholder="https://example.com/article"
              disabled={addUrlMutation.isPending}
            />
            <Button
              type="submit"
              size="sm"
              disabled={addUrlMutation.isPending || !urlValue.trim()}
            >
              {addUrlMutation.isPending ? "Adding..." : "Add URL"}
            </Button>
          </form>
        ) : (
          <>
            <input
              ref={fileInputRef}
              type="file"
              accept={accept}
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
              {uploadMutation.isPending
                ? "Uploading..."
                : `Upload ${accept ?? "files"}`}
            </Button>
            <span className="text-xs text-muted-foreground">
              Accepts {accept} files
            </span>
          </>
        )}
      </div>

      {urlError && <p className="mb-4 text-sm text-destructive">{urlError}</p>}
      {uploadError && <p className="mb-4 text-sm text-destructive">{uploadError}</p>}

      {isLoading && <p className="text-sm text-muted-foreground">Loading items...</p>}

      {!isLoading && items && items.length === 0 && (
        <p className="text-sm text-muted-foreground">
          No items yet — add one above to get started.
        </p>
      )}

      {!isLoading && items && items.length > 0 && (
        <div className="overflow-hidden rounded-xl border border-border">
          <table className="w-full text-sm">
            <tbody>
              {items.map((item) => {
                const checked = pendingChanges[item.id] ?? item.is_active
                return (
                  <tr
                    key={item.id}
                    className="border-b border-border last:border-0 hover:bg-muted/50"
                  >
                    <td className="w-10 px-3 py-2.5">
                      <input
                        type="checkbox"
                        checked={checked}
                        onChange={(e) => toggleItem(item, e.target.checked)}
                        aria-label={`Include ${item.name} in retrieval`}
                        className="size-4 rounded border-input accent-teal"
                      />
                    </td>
                    <td className="min-w-0 px-3 py-2.5">
                      <p className="truncate text-ink">{item.name}</p>
                      {item.status === "error" && item.error_message && (
                        <p className="truncate text-xs text-destructive">
                          {item.error_message}
                        </p>
                      )}
                    </td>
                    <td className="px-3 py-2.5">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="px-3 py-2.5 font-mono text-xs text-muted-foreground">
                      {item.status === "ready" ? `${item.chunk_count} chunks` : ""}
                    </td>
                    <td className="w-10 px-3 py-2.5 text-right">
                      <Button
                        type="button"
                        size="icon-xs"
                        variant="ghost"
                        disabled={deletingId === item.id}
                        onClick={() => deleteMutation.mutate(item.id)}
                        aria-label={`Delete ${item.name}`}
                      >
                        <Trash2 className="size-3.5" />
                      </Button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}

export default CollectionItemsPanel