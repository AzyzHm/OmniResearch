import { useState } from "react"
import { X } from "lucide-react"

import type { Collection } from "@/api/collections"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import CollectionsSidebar from "@/components/workspace/CollectionsSidebar"
import CollectionItemsPanel from "@/components/workspace/CollectionItemsPanel"

interface SourcesDrawerProps {
  projectId: string
  open: boolean
  onClose: () => void
}

function SourcesDrawer({ projectId, open, onClose }: SourcesDrawerProps) {
  const [selectedCollection, setSelectedCollection] = useState<Collection | null>(
    null
  )

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
          <h2 className="font-display text-sm font-medium text-ink">Sources</h2>
          <Button
            type="button"
            size="icon-xs"
            variant="ghost"
            onClick={onClose}
            aria-label="Close sources panel"
          >
            <X className="size-4" />
          </Button>
        </div>

        <CollectionsSidebar
          projectId={projectId}
          selectedCollectionId={selectedCollection?.id ?? null}
          onSelect={setSelectedCollection}
        />

        {selectedCollection ? (
          <CollectionItemsPanel collection={selectedCollection} />
        ) : (
          <div className="flex flex-1 items-center justify-center px-4 text-center text-sm text-muted-foreground">
            Select a collection above to manage its sources.
          </div>
        )}
      </aside>
    </>
  )
}

export default SourcesDrawer