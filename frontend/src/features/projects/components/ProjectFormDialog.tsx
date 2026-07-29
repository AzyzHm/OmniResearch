import { useState, type ReactNode } from "react"

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

interface ProjectFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  mode: "create" | "rename"
  initialName?: string
  isSubmitting: boolean
  error: string | null
  onSubmit: (name: string) => void
  trigger?: ReactNode
}

function ProjectFormDialog({
  open,
  onOpenChange,
  mode,
  initialName = "",
  isSubmitting,
  error,
  onSubmit,
  trigger,
}: ProjectFormDialogProps) {
  const [name, setName] = useState(initialName)

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    onSubmit(trimmed)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      {trigger}
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>
              {mode === "create" ? "New project" : "Rename project"}
            </DialogTitle>
            <DialogDescription>
              {mode === "create"
                ? "Give your project a name. You can rename it later."
                : "Choose a new name for this project."}
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-1.5">
            <Label htmlFor="project-name">Project name</Label>
            <Input
              id="project-name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              maxLength={100}
              autoFocus
              placeholder="e.g. Thesis Literature Review"
            />
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
              {isSubmitting
                ? "Saving..."
                : mode === "create"
                  ? "Create project"
                  : "Save changes"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default ProjectFormDialog