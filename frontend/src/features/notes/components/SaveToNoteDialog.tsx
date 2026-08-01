import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { NotebookText, Plus } from "lucide-react"

import {
  createNote,
  listNotes,
  saveMessageToNote,
  type Note,
} from "@/features/notes/api"
import { ApiError } from "@/shared/lib/apiClient"
import { Button } from "@/shared/components/ui/button"
import { Input } from "@/shared/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/shared/components/ui/dialog"

interface SaveToNoteDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  projectId: string
  messageId: string
  onSaved?: () => void
}

function SaveToNoteDialog({
  open,
  onOpenChange,
  projectId,
  messageId,
  onSaved,
}: SaveToNoteDialogProps) {
  const queryClient = useQueryClient()
  const notesQueryKey = ["notes", projectId]

  const { data: notes, isLoading } = useQuery({
    queryKey: notesQueryKey,
    queryFn: () => listNotes(projectId),
    enabled: open,
  })

  const [newNoteName, setNewNoteName] = useState("")
  const [showNewNoteInput, setShowNewNoteInput] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [savedNoteId, setSavedNoteId] = useState<string | null>(null)

  function handleSaved(noteId: string) {
    setError(null)
    setSavedNoteId(noteId)
    queryClient.invalidateQueries({ queryKey: ["note-items", noteId] })
    onSaved?.()
  }

  const saveMutation = useMutation({
    mutationFn: (note: Note) => saveMessageToNote(note.id, messageId),
    onSuccess: (_data, note) => handleSaved(note.id),
    onError: (err, note) => {
      // Already saved to this note — treat as a soft success, not an error.
      if (err instanceof ApiError && err.status === 409) {
        handleSaved(note.id)
        return
      }
      setError(err instanceof ApiError ? err.message : "Couldn't save this message.")
    },
  })

  const createAndSaveMutation = useMutation({
    mutationFn: async (name: string) => {
      const note = await createNote(projectId, name)
      await saveMessageToNote(note.id, messageId)
      return note
    },
    onSuccess: (note) => {
      queryClient.invalidateQueries({ queryKey: notesQueryKey })
      setNewNoteName("")
      setShowNewNoteInput(false)
      handleSaved(note.id)
    },
    onError: (err) => {
      setError(err instanceof ApiError ? err.message : "Couldn't create the note.")
    },
  })

  function handleCreateAndSave(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = newNoteName.trim()
    if (!trimmed) return
    createAndSaveMutation.mutate(trimmed)
  }

  function handleOpenChange(next: boolean) {
    if (!next) {
      setShowNewNoteInput(false)
      setNewNoteName("")
      setError(null)
      setSavedNoteId(null)
    }
    onOpenChange(next)
  }

  const busy = saveMutation.isPending || createAndSaveMutation.isPending

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Save to note</DialogTitle>
          <DialogDescription>
            Choose a note to save this message and its sources into.
          </DialogDescription>
        </DialogHeader>

        <div className="flex flex-col gap-4">
          <div className="flex max-h-64 flex-col gap-1.5 overflow-y-auto">
            {isLoading && (
              <p className="px-1 text-sm text-muted-foreground">Loading notes...</p>
            )}

            {!isLoading && notes?.length === 0 && !showNewNoteInput && (
              <p className="px-1 text-sm text-muted-foreground">
                No notes yet. Create one below.
              </p>
            )}

            {notes?.map((note) => {
              const justSaved = savedNoteId === note.id
              return (
                <Button
                  key={note.id}
                  type="button"
                  variant="outline"
                  className="justify-start"
                  disabled={busy}
                  onClick={() => saveMutation.mutate(note)}
                >
                  <NotebookText className="size-3.5" data-icon="inline-start" />
                  <span className="flex-1 truncate text-left">{note.name}</span>
                  {justSaved && (
                    <span className="shrink-0 text-xs text-teal">Saved ✓</span>
                  )}
                </Button>
              )
            })}
          </div>

          {error && <p className="px-1 text-sm text-destructive">{error}</p>}

          <div className="border-t border-border pt-4">
            {showNewNoteInput ? (
              <form onSubmit={handleCreateAndSave} className="flex items-center gap-2">
                <Input
                  value={newNoteName}
                  onChange={(e) => setNewNoteName(e.target.value)}
                  placeholder="New note name"
                  maxLength={100}
                  autoFocus
                  disabled={createAndSaveMutation.isPending}
                />
                <Button
                  type="submit"
                  size="sm"
                  disabled={createAndSaveMutation.isPending || !newNoteName.trim()}
                >
                  {createAndSaveMutation.isPending ? "Saving..." : "Create & save"}
                </Button>
              </form>
            ) : (
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => setShowNewNoteInput(true)}
                disabled={busy}
              >
                <Plus className="size-3.5" data-icon="inline-start" />
                New note
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default SaveToNoteDialog