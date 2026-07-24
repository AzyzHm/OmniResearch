import { useState } from "react"
import { FileText, Globe, Type } from "lucide-react"

import { COLLECTION_TYPES, type CollectionType } from "@/api/collections"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { cn } from "@/lib/utils"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog"

const TYPE_META: Record<
  CollectionType,
  { label: string; description: string; icon: typeof FileText }
> = {
  documents: {
    label: "Documents",
    description: "Upload PDF files",
    icon: FileText,
  },
  urls: {
    label: "URLs",
    description: "Add web pages by link",
    icon: Globe,
  },
  text: {
    label: "Text",
    description: "Upload plain .txt files",
    icon: Type,
  },
}

interface CollectionFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  isSubmitting: boolean
  error: string | null
  onSubmit: (name: string, type: CollectionType) => void
}

function CollectionFormDialog({
  open,
  onOpenChange,
  isSubmitting,
  error,
  onSubmit,
}: CollectionFormDialogProps) {
  const [name, setName] = useState("")
  const [type, setType] = useState<CollectionType>("documents")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = name.trim()
    if (!trimmed) return
    onSubmit(trimmed, type)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <form onSubmit={handleSubmit}>
          <DialogHeader>
            <DialogTitle>New collection</DialogTitle>
            <DialogDescription>
              Collections group related sources together for retrieval.
            </DialogDescription>
          </DialogHeader>

          <div className="flex flex-col gap-4">
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="collection-name">Collection name</Label>
              <Input
                id="collection-name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                maxLength={100}
                autoFocus
                placeholder="e.g. Background Reading"
              />
            </div>

            <div className="flex flex-col gap-1.5">
              <Label>Source type</Label>
              <div className="grid grid-cols-3 gap-2">
                {COLLECTION_TYPES.map((t) => {
                  const meta = TYPE_META[t]
                  const Icon = meta.icon
                  const selected = type === t
                  return (
                    <button
                      key={t}
                      type="button"
                      onClick={() => setType(t)}
                      className={cn(
                        "flex flex-col items-center gap-1.5 rounded-lg border p-3 text-center transition-colors",
                        selected
                          ? "border-teal bg-teal/10 text-teal"
                          : "border-border text-muted-foreground hover:border-teal/40 hover:text-ink"
                      )}
                    >
                      <Icon className="size-4" />
                      <span className="text-xs font-medium">{meta.label}</span>
                    </button>
                  )
                })}
              </div>
              <p className="text-xs text-muted-foreground">
                {TYPE_META[type].description}
              </p>
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
              {isSubmitting ? "Creating..." : "Create collection"}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

export default CollectionFormDialog