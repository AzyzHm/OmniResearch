import { useState } from "react"
import { Search } from "lucide-react"

import {
  addSearchResults,
  searchWeb,
  type SearchEngine,
  type TavilySearchDepth,
  type WebSearchResult,
} from "@/features/collections/searchApi"
import { ApiError } from "@/shared/lib/apiClient"
import { cn } from "@/shared/lib/utils"
import { Button } from "@/shared/components/ui/button"
import { Input } from "@/shared/components/ui/input"
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/shared/components/ui/dialog"
import SearchResultRow from "@/features/collections/components/SearchResultRow"

const ENGINES: { value: SearchEngine; label: string }[] = [
  { value: "tavily", label: "Tavily" },
  { value: "exa", label: "Exa" },
]

const DEPTHS: TavilySearchDepth[] = ["basic", "advanced", "fast", "ultra-fast"]

interface SearchModalProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  collectionId: string
  existingUrls: Set<string>
  onAdded: () => void
}

function SearchModal({
  open,
  onOpenChange,
  collectionId,
  existingUrls,
  onAdded,
}: SearchModalProps) {
  const [query, setQuery] = useState("")
  const [engine, setEngine] = useState<SearchEngine>("tavily")
  const [numResults, setNumResults] = useState(10)
  const [searchDepth, setSearchDepth] = useState<TavilySearchDepth>("basic")

  const [latestResults, setLatestResults] = useState<WebSearchResult[]>([])
  const [selectedItems, setSelectedItems] = useState<Record<string, WebSearchResult>>({})

  const [isSearching, setIsSearching] = useState(false)
  const [searchError, setSearchError] = useState<string | null>(null)
  const [isAdding, setIsAdding] = useState(false)
  const [addError, setAddError] = useState<string | null>(null)

  async function handleSearch(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = query.trim()
    if (!trimmed) return

    setIsSearching(true)
    setSearchError(null)
    try {
      const results = await searchWeb(engine, trimmed, numResults, searchDepth)
      const deduped = new Map<string, WebSearchResult>()
      results.forEach((r) => {
        if (r.url) deduped.set(r.url, r)
      })
      setLatestResults(Array.from(deduped.values()))
    } catch (err) {
      setSearchError(err instanceof ApiError ? err.message : "Search failed.")
    } finally {
      setIsSearching(false)
    }
  }

  function toggleResult(result: WebSearchResult, checked: boolean) {
    setSelectedItems((prev) => {
      const next = { ...prev }
      if (checked) next[result.url] = result
      else delete next[result.url]
      return next
    })
  }

  function selectAllEligible() {
    setSelectedItems((prev) => {
      const next = { ...prev }
      latestResults.forEach((r) => {
        if (!existingUrls.has(r.url) && r.content?.trim()) next[r.url] = r
      })
      return next
    })
  }

  function deselectAllLatest() {
    setSelectedItems((prev) => {
      const next = { ...prev }
      latestResults.forEach((r) => delete next[r.url])
      return next
    })
  }

  async function handleAdd() {
    const items = Object.values(selectedItems)
    if (items.length === 0) return
    setIsAdding(true)
    setAddError(null)
    try {
      await addSearchResults(collectionId, items)
      onAdded()
      onOpenChange(false)
    } catch (err) {
      setAddError(err instanceof ApiError ? err.message : "Couldn't add results.")
    } finally {
      setIsAdding(false)
    }
  }

  const latestUrls = new Set(latestResults.map((r) => r.url))
  const carriedOver = Object.values(selectedItems).filter((r) => !latestUrls.has(r.url))
  const selectedCount = Object.keys(selectedItems).length

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-xl">
        <DialogHeader>
          <DialogTitle>Search the web</DialogTitle>
          <DialogDescription>
            Find pages with Tavily or Exa, then add the ones you want as sources.
          </DialogDescription>
        </DialogHeader>

        <form onSubmit={handleSearch} className="flex flex-col gap-3">
          <div className="flex gap-2">
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search query"
              autoFocus
            />
            <Button type="submit" disabled={isSearching || !query.trim()}>
              <Search className="size-3.5" data-icon="inline-start" />
              {isSearching ? "Searching..." : "Search"}
            </Button>
          </div>

          <div className="flex flex-wrap items-center gap-4">
            <div className="flex items-center gap-1.5">
              <span className="text-xs text-muted-foreground">Engine</span>
              <div className="flex gap-1">
                {ENGINES.map((e) => (
                  <button
                    key={e.value}
                    type="button"
                    onClick={() => setEngine(e.value)}
                    className={cn(
                      "rounded-full px-2.5 py-1 font-mono text-[0.7rem] font-medium transition-colors",
                      engine === e.value
                        ? "bg-teal/15 text-teal"
                        : "text-muted-foreground hover:bg-muted",
                    )}
                  >
                    {e.label}
                  </button>
                ))}
              </div>
            </div>

            <label className="flex items-center gap-1.5 text-xs text-muted-foreground">
              Results
              <input
                type="range"
                min={1}
                max={20}
                value={numResults}
                onChange={(e) => setNumResults(Number(e.target.value))}
                className="accent-teal"
              />
              <span className="font-mono text-ink">{numResults}</span>
            </label>

            {engine === "tavily" ? (
              <div className="flex items-center gap-1.5">
                <span className="text-xs text-muted-foreground">Depth</span>
                <div className="flex gap-1">
                  {DEPTHS.map((d) => (
                    <button
                      key={d}
                      type="button"
                      onClick={() => setSearchDepth(d)}
                      className={cn(
                        "rounded-full px-2 py-1 font-mono text-[0.7rem] font-medium transition-colors",
                        searchDepth === d
                          ? "bg-teal/15 text-teal"
                          : "text-muted-foreground hover:bg-muted",
                      )}
                    >
                      {d}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <span className="text-xs text-muted-foreground">Depth: N/A for Exa</span>
            )}
          </div>
        </form>

        {searchError && <p className="mt-2 text-sm text-destructive">{searchError}</p>}

        <div className="mt-3 max-h-72 overflow-y-auto rounded-lg border border-border p-2">
          {latestResults.length === 0 && carriedOver.length === 0 && (
            <p className="p-2 text-sm text-muted-foreground">No searches yet. Run one above.</p>
          )}

          {latestResults.length > 0 && (
            <>
              <div className="mb-1 flex items-center justify-between px-1">
                <p className="text-xs text-muted-foreground">
                  {latestResults.length} result(s) — check the ones to add
                </p>
                <div className="flex gap-1">
                  <Button type="button" size="xs" variant="outline" onClick={selectAllEligible}>
                    Select all
                  </Button>
                  <Button type="button" size="xs" variant="outline" onClick={deselectAllLatest}>
                    Deselect all
                  </Button>
                </div>
              </div>
              {latestResults.map((r) => (
                <SearchResultRow
                  key={r.url}
                  result={r}
                  selected={r.url in selectedItems}
                  alreadyExists={existingUrls.has(r.url)}
                  onToggle={(checked) => toggleResult(r, checked)}
                />
              ))}
            </>
          )}

          {carriedOver.length > 0 && (
            <>
              <p className="mt-2 mb-1 px-1 font-mono text-[0.7rem] tracking-wide text-muted-foreground uppercase">
                Selected sources
              </p>
              {carriedOver.map((r) => (
                <SearchResultRow
                  key={r.url}
                  result={r}
                  selected
                  alreadyExists={existingUrls.has(r.url)}
                  onToggle={(checked) => toggleResult(r, checked)}
                />
              ))}
            </>
          )}
        </div>

        {addError && <p className="mt-2 text-sm text-destructive">{addError}</p>}

        <div className="mt-4 flex gap-2">
          <Button
            type="button"
            className="flex-1"
            disabled={selectedCount === 0 || isAdding}
            onClick={handleAdd}
          >
            {isAdding ? "Adding..." : `Add ${selectedCount} selected`}
          </Button>
          <Button
            type="button"
            variant="outline"
            className="flex-1"
            onClick={() => onOpenChange(false)}
          >
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

export default SearchModal
