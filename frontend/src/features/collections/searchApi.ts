import { apiClient } from "@/shared/lib/apiClient"
import type { CollectionItem } from "@/features/collections/api"

export type SearchEngine = "tavily" | "exa"
export type TavilySearchDepth = "basic" | "advanced" | "fast" | "ultra-fast"

export interface WebSearchResult {
  url: string
  title: string
  content: string
}

export function searchWeb(
  engine: SearchEngine,
  query: string,
  numResults: number,
  searchDepth: TavilySearchDepth = "basic",
) {
  return apiClient
    .post<{ results: WebSearchResult[] }>("/search/web", {
      engine,
      query,
      num_results: numResults,
      search_depth: searchDepth,
    })
    .then((res) => res.results)
}

export function addSearchResults(collectionId: string, items: WebSearchResult[]) {
  return apiClient.post<{ added: CollectionItem[]; skipped: string[] }>(
    `/collections/${collectionId}/items/from-search`,
    { items },
  )
}
