import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { FileText, Globe, Plus, Trash2, Type } from "lucide-react"

import {
  createCollection,
  deleteCollection,
  listCollections,
  type Collection,
  type CollectionType,
} from "@/api/collections"
import { ApiError } from "@/lib/apiClient"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import CollectionFormDialog from "@/components/workspace/CollectionFormDialog"

const TYPE_ICON: Record<CollectionType, typeof FileText> = {
  documents: FileText,
  urls: Globe,
  text: Type,
}

interface CollectionsSidebarProps {
  projectId: string
  selectedCollectionId: string | null
  onSelect: (collection: Collection) => void
}

function CollectionsSidebar({
  projectId,
  selectedCollectionId,
  onSelect,
}: CollectionsSidebarProps) {
  const queryClient = useQueryClient()
  const queryKey = ["collections", projectId]

  const { data: collections, isLoading } = useQuery({
    queryKey,
    queryFn: () => listCollections(projectId),
  })

  const [createOpen, setCreateOpen] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(
    null
  )

  const createMutation = useMutation({
    mutationFn: (payload: { name: string; type: CollectionType }) =>
      createCollection(projectId, payload),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey })
      setCreateOpen(false)
      setCreateError(null)
      onSelect(created)
    },
    onError: (err) => {
      setCreateError(err instanceof ApiError ? err.message : "Something went wrong.")
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteCollection,
    onSuccess: (_data, collectionId) => {
      queryClient.setQueryData<Collection[]>(queryKey, (old) =>
        old ? old.filter((c) => c.id !== collectionId) : old
      )
      queryClient.invalidateQueries({ queryKey })
    },
    onSettled: () => setConfirmingDeleteId(null),
  })

  return (
    <div className="flex w-64 shrink-0 flex-col gap-2 border-r border-border p-4">
      <div className="mb-1 flex items-center justify-between">
        <h2 className="font-mono text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Collections
        </h2>
        <Button
          type="button"
          size="icon-xs"
          variant="ghost"
          onClick={() => setCreateOpen(true)}
          aria-label="New collection"
        >
          <Plus className="size-3.5" />
        </Button>
      </div>

      {isLoading && (
        <p className="px-1 text-sm text-muted-foreground">Loading...</p>
      )}

      {!isLoading && collections?.length === 0 && (
        <p className="px-1 text-sm text-muted-foreground">
          No collections yet.
        </p>
      )}

      <div className="flex flex-col gap-1">
        {collections?.map((collection) => {
          const Icon = TYPE_ICON[collection.type]
          const selected = collection.id === selectedCollectionId
          const confirming = confirmingDeleteId === collection.id

          return (
            <div
              key={collection.id}
              className={cn(
                "group flex items-center gap-2 rounded-lg px-2 py-1.5 text-sm transition-colors",
                selected
                  ? "bg-teal/10 text-teal"
                  : "text-ink hover:bg-muted"
              )}
            >
              <button
                type="button"
                onClick={() => onSelect(collection)}
                className="flex flex-1 items-center gap-2 overflow-hidden text-left"
              >
                <Icon className="size-3.5 shrink-0" />
                <span className="truncate">{collection.name}</span>
              </button>

              {confirming ? (
                <div className="flex shrink-0 items-center gap-1">
                  <Button
                    type="button"
                    size="icon-xs"
                    variant="destructive"
                    disabled={deleteMutation.isPending}
                    onClick={() => deleteMutation.mutate(collection.id)}
                    aria-label="Confirm delete"
                  >
                    <Trash2 className="size-3" />
                  </Button>
                  <Button
                    type="button"
                    size="icon-xs"
                    variant="ghost"
                    disabled={deleteMutation.isPending}
                    onClick={() => setConfirmingDeleteId(null)}
                    aria-label="Cancel delete"
                  >
                    ×
                  </Button>
                </div>
              ) : (
                <Button
                  type="button"
                  size="icon-xs"
                  variant="ghost"
                  className="shrink-0 opacity-0 group-hover:opacity-100"
                  onClick={() => setConfirmingDeleteId(collection.id)}
                  aria-label="Delete collection"
                >
                  <Trash2 className="size-3" />
                </Button>
              )}
            </div>
          )
        })}
      </div>

      <CollectionFormDialog
        open={createOpen}
        onOpenChange={(open) => {
          setCreateOpen(open)
          if (!open) setCreateError(null)
        }}
        isSubmitting={createMutation.isPending}
        error={createError}
        onSubmit={(name, type) => createMutation.mutate({ name, type })}
      />
    </div>
  )
}

export default CollectionsSidebar