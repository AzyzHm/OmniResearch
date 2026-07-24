import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { FolderKanban, Pencil, Trash2 } from "lucide-react"

import type { Project } from "@/api/projects"
import { Button } from "@/components/ui/button"

interface ProjectCardProps {
  project: Project
  onRename: (project: Project) => void
  onDelete: (project: Project) => void
  isDeleting: boolean
}

function ProjectCard({ project, onRename, onDelete, isDeleting }: ProjectCardProps) {
  const navigate = useNavigate()
  const [confirmingDelete, setConfirmingDelete] = useState(false)

  const updatedLabel = new Date(project.updated_at).toLocaleDateString(undefined, {
    month: "short",
    day: "numeric",
    year: "numeric",
  })

  return (
    <div
      role="button"
      tabIndex={0}
      onClick={() => navigate(`/app/projects/${project.id}`)}
      onKeyDown={(e) => {
        if (e.key === "Enter") navigate(`/app/projects/${project.id}`)
      }}
      className="group flex cursor-pointer flex-col gap-3 rounded-xl border border-border bg-surface p-4 text-left transition-colors hover:border-teal/40 hover:bg-teal/5"
    >
      <div className="flex items-start justify-between gap-2">
        <div className="flex size-9 shrink-0 items-center justify-center rounded-lg bg-teal/10 text-teal">
          <FolderKanban className="size-4.5" />
        </div>

        <div
          className="flex items-center gap-1 opacity-0 transition-opacity group-hover:opacity-100"
          onClick={(e) => e.stopPropagation()}
        >
          {confirmingDelete ? (
            <>
              <Button
                type="button"
                size="xs"
                variant="destructive"
                disabled={isDeleting}
                onClick={() => onDelete(project)}
              >
                {isDeleting ? "Deleting..." : "Confirm"}
              </Button>
              <Button
                type="button"
                size="xs"
                variant="ghost"
                disabled={isDeleting}
                onClick={() => setConfirmingDelete(false)}
              >
                Cancel
              </Button>
            </>
          ) : (
            <>
              <Button
                type="button"
                size="icon-xs"
                variant="ghost"
                onClick={() => onRename(project)}
                aria-label="Rename project"
              >
                <Pencil className="size-3.5" />
              </Button>
              <Button
                type="button"
                size="icon-xs"
                variant="ghost"
                onClick={() => setConfirmingDelete(true)}
                aria-label="Delete project"
              >
                <Trash2 className="size-3.5" />
              </Button>
            </>
          )}
        </div>
      </div>

      <div>
        <h3 className="font-display text-base font-medium text-ink">
          {project.name}
        </h3>
        <p className="mt-0.5 font-mono text-xs text-muted-foreground">
          Updated {updatedLabel}
        </p>
      </div>
    </div>
  )
}

export default ProjectCard