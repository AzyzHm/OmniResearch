import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { FolderKanban, Plus } from "lucide-react"

import {
  createProject,
  deleteProject,
  listProjects,
  renameProject,
  type Project,
} from "@/api/projects"
import { ApiError } from "@/lib/apiClient"
import { Button } from "@/components/ui/button"
import { DialogTrigger } from "@/components/ui/dialog"
import ProjectCard from "@/components/workspace/ProjectCard"
import ProjectFormDialog from "@/components/workspace/ProjectFormDialog"

const PROJECTS_QUERY_KEY = ["projects"]

function ProjectsList() {
  const queryClient = useQueryClient()

  const { data: projects, isLoading, isError } = useQuery({
    queryKey: PROJECTS_QUERY_KEY,
    queryFn: listProjects,
  })

  const [createOpen, setCreateOpen] = useState(false)
  const [createError, setCreateError] = useState<string | null>(null)
  const [createInstance, setCreateInstance] = useState(0)

  const [renameTarget, setRenameTarget] = useState<Project | null>(null)
  const [renameError, setRenameError] = useState<string | null>(null)
  const [renameInstance, setRenameInstance] = useState(0)

  function openCreateDialog() {
    setCreateInstance((n) => n + 1)
    setCreateOpen(true)
  }

  const [deletingId, setDeletingId] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: createProject,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY })
      setCreateOpen(false)
      setCreateError(null)
    },
    onError: (err) => {
      setCreateError(err instanceof ApiError ? err.message : "Something went wrong.")
    },
  })

  const renameMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      renameProject(id, { name }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY })
      setRenameTarget(null)
      setRenameError(null)
    },
    onError: (err) => {
      setRenameError(err instanceof ApiError ? err.message : "Something went wrong.")
    },
  })

  const [deleteError, setDeleteError] = useState<string | null>(null)

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onMutate: async (id: string) => {
      setDeletingId(id)
      setDeleteError(null)
      await queryClient.cancelQueries({ queryKey: PROJECTS_QUERY_KEY })
    },
    onSuccess: (_data, id) => {
      queryClient.setQueryData<Project[]>(PROJECTS_QUERY_KEY, (old) =>
        old ? old.filter((p) => p.id !== id) : old
      )
      queryClient.invalidateQueries({ queryKey: PROJECTS_QUERY_KEY })
    },
    onError: (err) => {
      setDeleteError(
        err instanceof ApiError ? err.message : "Couldn't delete the project."
      )
    },
    onSettled: () => setDeletingId(null),
  })

  return (
    <div className="mx-auto max-w-5xl px-6 py-10">
      <div className="mb-8 flex items-center justify-between">
        <div>
          <h1 className="font-display text-2xl font-medium text-ink">Projects</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Organize your research into separate projects, each with its own
            collections and chats.
          </p>
        </div>

        <ProjectFormDialog
          key={createInstance}
          open={createOpen}
          onOpenChange={(open) => {
            if (open) openCreateDialog()
            else {
              setCreateOpen(false)
              setCreateError(null)
            }
          }}
          mode="create"
          isSubmitting={createMutation.isPending}
          error={createError}
          onSubmit={(name) => createMutation.mutate({ name })}
          trigger={
            <DialogTrigger
              render={
                <Button type="button">
                  <Plus className="size-4" data-icon="inline-start" />
                  New project
                </Button>
              }
            />
          }
        />
      </div>

      {isLoading && (
        <p className="text-sm text-muted-foreground">Loading projects...</p>
      )}

      {isError && (
        <p className="text-sm text-destructive">
          Couldn't load your projects. Try refreshing the page.
        </p>
      )}

      {deleteError && <p className="mb-4 text-sm text-destructive">{deleteError}</p>}

      {!isLoading && !isError && projects && projects.length === 0 && (
        <div className="flex flex-col items-center gap-3 rounded-xl border border-dashed border-border py-16 text-center">
          <div className="flex size-12 items-center justify-center rounded-full bg-teal/10 text-teal">
            <FolderKanban className="size-5" />
          </div>
          <div>
            <p className="font-medium text-ink">No projects yet</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Create your first project to start uploading documents and asking
              questions.
            </p>
          </div>
          <Button type="button" className="mt-2" onClick={openCreateDialog}>
            <Plus className="size-4" data-icon="inline-start" />
            New project
          </Button>
        </div>
      )}

      {!isLoading && !isError && projects && projects.length > 0 && (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {projects.map((project) => (
            <ProjectCard
              key={project.id}
              project={project}
              onRename={(p) => {
                setRenameInstance((n) => n + 1)
                setRenameTarget(p)
                setRenameError(null)
              }}
              onDelete={(p) => deleteMutation.mutate(p.id)}
              isDeleting={deletingId === project.id}
            />
          ))}
        </div>
      )}

      <ProjectFormDialog
        key={renameInstance}
        open={!!renameTarget}
        onOpenChange={(open) => {
          if (!open) {
            setRenameTarget(null)
            setRenameError(null)
          }
        }}
        mode="rename"
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

export default ProjectsList