import { useState } from "react"

import { Button } from "@/shared/components/ui/button"
import { Input } from "@/shared/components/ui/input"
import { Label } from "@/shared/components/ui/label"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/shared/components/ui/dialog"

interface NoteFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  isSubmitting: boolean
  error: string | null
  onSubmit: (name: string) => void
}

function NoteFormDialog({
  open,
  onOpenChange,
  isSubmitting,
  error,
  onSubmit,
}: NoteFormDialogProps) {
  const [name, setName] = useState("")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    onSubmit(trimmed)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>New note</DialogTitle>
            <DialogDescription>
              Notes collect messages you save from your chats, along with
              their sources, for this project.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="note-name">Note name</Label>
              <Input
                id="note-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={100}
                autoFocus
                placeholder="e.g. Key Findings"
              />
            </div>

            {error && <p className="text-sm text-destructive">{error}</p>}
          </div>

          <DialogFooter>
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button type="submit" disabled={isSubmitting || !name.trim()}>
              {isSubmitting ? "Creating..." : "Create note"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default NoteFormDialog