import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { ArrowLeft, FolderKanban } from "lucide-react"

import type { Collection } from "@/api/collections"
import CollectionsSidebar from "@/components/workspace/CollectionsSidebar"
import CollectionItemsPanel from "@/components/workspace/CollectionItemsPanel"

function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(
    null
  )

  if (!projectId) return null

  return (
    <div className="flex min-h-[calc(100vh-3.5rem)] flex-col">
      <div className="border-b border-border px-6 py-4">
        <Link
          to="/app"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-ink"
        >
          <ArrowLeft className="size-3.5" />
          Back to projects
        </Link>
      </div>

      <div className="flex flex-1">
        <CollectionsSidebar
          projectId={projectId}
          selectedCollectionId={selectedCollection?.id ?? null}
          onSelect={setSelectedCollection}
        />

        {selectedCollection ? (
          <CollectionItemsPanel collection={selectedCollection} />
        ) : (
          <div className="flex flex-1 flex-col items-center justify-center gap-3 text-center">
            <div className="flex size-12 items-center justify-center rounded-full bg-teal/10 text-teal">
              <FolderKanban className="size-5" />
            </div>
            <div>
              <p className="font-medium text-ink">Select a collection</p>
              <p className="mt-1 max-w-sm text-sm text-muted-foreground">
                Choose a collection on the left, or create a new one to start
                adding sources.
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default ProjectDetail