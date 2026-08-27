import type { CollectionItem } from "@/features/collections/api"

const TYPE_LABELS: Record<string, string> = {
  pdf: "PDF",
  txt: "TXT",
  url: "URL",
}

function pluralize(count: number, noun: string): string {
  return `${count.toLocaleString()} ${noun}${count === 1 ? "" : "s"}`
}

function ItemMetaBadges({ item }: { item: CollectionItem }) {
  const typeLabel = TYPE_LABELS[item.source_type] ?? item.source_type.toUpperCase()

  let countLabel: string | null = null
  if (item.status === "ready") {
    if (item.source_type === "pdf" && item.page_count != null) {
      countLabel = pluralize(item.page_count, "page")
    } else if (item.source_type === "txt" && item.word_count != null) {
      countLabel = pluralize(item.word_count, "word")
    }
  }

  return (
    <div className="flex shrink-0 items-center gap-1.5">
      <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 font-mono text-[0.7rem] font-medium text-muted-foreground">
        {typeLabel}
      </span>
      {countLabel && (
        <span className="inline-flex items-center rounded-full bg-muted px-2 py-0.5 font-mono text-[0.7rem] font-medium text-muted-foreground">
          {countLabel}
        </span>
      )}
    </div>
  )
}

export default ItemMetaBadges
