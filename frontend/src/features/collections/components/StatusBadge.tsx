import { cn } from "@/shared/lib/utils"
import type { CollectionItem } from "@/features/collections/api"

const STATUS_STYLES: Record<string, string> = {
  processing: "bg-amber/15 text-amber",
  ready: "bg-teal/15 text-teal",
  error: "bg-destructive/10 text-destructive",
}

const STATUS_LABELS: Record<string, string> = {
  processing: "Processing",
  ready: "Ready",
  error: "Error",
}

function StatusBadge({ status }: { status: CollectionItem["status"] }) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full px-2 py-0.5 font-mono text-[0.7rem] font-medium",
        STATUS_STYLES[status] ?? "bg-muted text-muted-foreground"
      )}
    >
      {status === "processing" && (
        <span className="size-1.5 animate-pulse rounded-full bg-amber" />
      )}
      {STATUS_LABELS[status] ?? status}
    </span>
  )
}

export default StatusBadge