import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { NotebookText, Pencil, Plus, Trash2 } from "lucide-react"

import { createNote, deleteNote, listNotes, renameNote, type Note } from "@/features/notes/api"
import { ApiError } from "@/shared/lib/apiClient"
import { cn } from "@/shared/lib/utils"
import { Button } from "@/shared/components/ui/button"
import NoteFormDialog from "@/features/notes/components/NoteFormDialog"
import NoteRenameDialog from "@/features/notes/components/NoteRenameDialog"

interface NotesSidebarProps {
  projectId: string
  selectedNoteId: string | null
  onSelect: (note: Note | null) => void
}

function NotesSidebar({ projectId, selectedNoteId, onSelect }: NotesSidebarProps) {
  const queryClient = useQueryClient()
  const queryKey = ["notes", projectId]

  const { data: notes, isLoading } = useQuery({
    queryKey,
    queryFn: () => listNotes(projectId),
  })

  const [createOpen, setCreateOpen] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [renameTarget, setRenameTarget] = useState<Note | null>(null)
  const [renameInstance, setRenameInstance] = useState(0)
  const [renameError, setRenameError] = useState<string | null>(null)
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: (name: string) => createNote(projectId, name),
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

  const renameMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) => renameNote(id, name),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey })
      setRenameTarget(null)
      setRenameError(null)
      if (selectedNoteId === updated.id) onSelect(updated)
    },
    onError: (err) => {
      setRenameError(err instanceof ApiError ? err.message : "Something went wrong.")
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteNote,
    onMutate: async () => {
      setDeleteError(null)
      await queryClient.cancelQueries({ queryKey })
    },
    onSuccess: (_data, noteId) => {
      queryClient.setQueryData<Note[]>(queryKey, (old) =>
        old ? old.filter((n) => n.id !== noteId) : old,
      )
      queryClient.invalidateQueries({ queryKey })
      if (noteId === selectedNoteId) onSelect(null)
    },
    onError: (err) => {
      setDeleteError(err instanceof ApiError ? err.message : "Couldn't delete the note.")
    },
    onSettled: () => setConfirmingDeleteId(null),
  })

  return (
    <div className="flex max-h-56 shrink-0 flex-col gap-2 border-b border-border p-3">
      <div className="mb-1 flex items-center justify-between">
        <h2 className="font-mono text-xs font-medium tracking-wide text-muted-foreground uppercase">
          Notes
        </h2>
        <Button
          type="button"
          size="icon-xs"
          variant="ghost"
          onClick={() => setCreateOpen(true)}
          aria-label="New note"
        >
          <Plus className="size-3.5" />
        </Button>
      </div>

      {isLoading && <p className="px-1 text-sm text-muted-foreground">Loading...</p>}

      {!isLoading && notes?.length === 0 && (
        <p className="px-1 text-sm text-muted-foreground">No notes yet.</p>
      )}

      {deleteError && <p className="px-1 text-sm text-destructive">{deleteError}</p>}

      <div className="flex flex-col gap-1 overflow-y-auto">
        {notes?.map((note) => {
          const selected = note.id === selectedNoteId
          const confirming = confirmingDeleteId === note.id

          return (
            <div
              key={note.id}
              className={cn(
                "group flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm transition-colors",
                selected ? "bg-teal/10 text-teal" : "text-ink hover:bg-muted",
              )}
            >
              <button
                type="button"
                onClick={() => onSelect(note)}
                className="flex flex-1 items-center gap-2 overflow-hidden text-left"
              >
                <NotebookText className="size-3.5 shrink-0" />
                <span className="truncate">{note.name}</span>
              </button>

              {confirming ? (
                <div className="flex shrink-0 items-center gap-1">
                  <Button
                    type="button"
                    size="icon-xs"
                    variant="destructive"
                    disabled={deleteMutation.isPending}
                    onClick={() => deleteMutation.mutate(note.id)}
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
                <div className="flex shrink-0 items-center gap-0.5 opacity-100 md:opacity-0 md:group-hover:opacity-100">
                  <Button
                    type="button"
                    size="icon-xs"
                    variant="ghost"
                    onClick={() => {
                      setRenameInstance((n) => n + 1)
                      setRenameTarget(note)
                      setRenameError(null)
                    }}
                    aria-label="Rename note"
                  >
                    <Pencil className="size-3" />
                  </Button>
                  <Button
                    type="button"
                    size="icon-xs"
                    variant="ghost"
                    onClick={() => setConfirmingDeleteId(note.id)}
                    aria-label="Delete note"
                  >
                    <Trash2 className="size-3" />
                  </Button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <NoteFormDialog
        open={createOpen}
        onOpenChange={(open) => {
          setCreateOpen(open)
          if (!open) setCreateError(null)
        }}
        isSubmitting={createMutation.isPending}
        error={createError}
        onSubmit={(name) => createMutation.mutate(name)}
      />

      <NoteRenameDialog
        key={renameInstance}
        open={!!renameTarget}
        onOpenChange={(open) => {
          if (!open) {
            setRenameTarget(null)
            setRenameError(null)
          }
        }}
        initialName={renameTarget?.name ?? ""}
        isSubmitting={renameMutation.isPending}
        error={renameError}
        onSubmit={(name) => {
          if (renameTarget) renameMutation.mutate({ id: renameTarget.id, name })
        }}
      />
    </div>
  )
}

export default NotesSidebar
