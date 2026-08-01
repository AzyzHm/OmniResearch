import { useState } from "react"
import { X } from "lucide-react"

import type { Note } from "@/features/notes/api"
import { cn } from "@/shared/lib/utils"
import { Button } from "@/shared/components/ui/button"
import NotesSidebar from "@/features/notes/components/NotesSidebar"
import NoteItemsPanel from "@/features/notes/components/NoteItemsPanel"

interface NotesDrawerProps {
  projectId: string
  open: boolean
  onClose: () => void
  onJumpToChat?: (chatId: string) => void
}

function NotesDrawer({ projectId, open, onClose, onJumpToChat }: NotesDrawerProps) {
  const [selectedNote, setSelectedNote] = useState<Note | null>(null)

  return (
    <>
      <div
        onClick={onClose}
        aria-hidden={!open}
        className={cn(
          "fixed inset-0 z-40 bg-ink/30 backdrop-blur-[1px] transition-opacity duration-200",
          open ? "opacity-100" : "pointer-events-none opacity-0"
        )}
      />

      <aside
        className={cn(
          "fixed top-14 right-0 z-40 flex h-[calc(100vh-3.5rem)] w-full max-w-md flex-col border-l border-border bg-paper shadow-lg transition-transform duration-200",
          open ? "translate-x-0" : "translate-x-full"
        )}
        aria-hidden={!open}
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="font-display text-sm font-medium text-ink">Notes</h2>
          <Button
            type="button"
            size="icon-xs"
            variant="ghost"
            onClick={onClose}
            aria-label="Close notes panel"
          >
            <X className="size-4" />
          </Button>
        </div>

        <NotesSidebar
          projectId={projectId}
          selectedNoteId={selectedNote?.id ?? null}
          onSelect={setSelectedNote}
        />

        {selectedNote ? (
          <NoteItemsPanel
            note={selectedNote}
            onJumpToChat={
              onJumpToChat
                ? (chatId) => {
                    onJumpToChat(chatId)
                    onClose()
                  }
                : undefined
            }
          />
        ) : (
          <div className="flex flex-1 items-center justify-center px-4 text-center text-sm text-muted-foreground">
            Select a note above to see its saved messages.
          </div>
        )}
      </aside>
    </>
  )
}

export default NotesDrawer