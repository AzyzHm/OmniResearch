import type { WebSearchResult } from "@/features/collections/searchApi"

interface SearchResultRowProps {
  result: WebSearchResult
  selected: boolean
  alreadyExists: boolean
  onToggle: (checked: boolean) => void
}

function SearchResultRow({ result, selected, alreadyExists, onToggle }: SearchResultRowProps) {
  const hasContent = Boolean(result.content?.trim())
  const disabled = alreadyExists || !hasContent
  const preview = result.content?.trim()
    ? result.content.trim().slice(0, 130) + (result.content.trim().length > 130 ? "…" : "")
    : null

  return (
    <div className="flex items-start gap-2.5 border-b border-border py-2 last:border-0">
      <input
        type="checkbox"
        checked={selected}
        disabled={disabled}
        onChange={(e) => onToggle(e.target.checked)}
        aria-label={`Select ${result.title || result.url}`}
        className="mt-1 size-4 shrink-0 rounded border-input accent-teal disabled:opacity-40"
      />
      <div className="min-w-0 flex-1">
        <a
          href={result.url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-sm font-medium text-teal hover:underline"
        >
          {result.title || result.url}
        </a>
        <p className="mt-0.5 text-xs">
          {alreadyExists ? (
            <span className="text-teal">✓ already in this collection</span>
          ) : !hasContent ? (
            <span className="text-amber">⚠ no content returned</span>
          ) : (
            <span className="text-muted-foreground">{preview}</span>
          )}
        </p>
      </div>
    </div>
  )
}

export default SearchResultRow
