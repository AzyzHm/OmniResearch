import type { RetrievalMode } from "@/features/chat/api"

export const NODE_LABELS: Record<string, string> = {
  router: "Deciding if I need to search your sources…",
  refine_query: "Refining your question…",
  retrieve: "Searching your sources…",
  rerank: "Ranking the most relevant chunks…",
  validate: "Checking if I found enough…",
  generate: "Writing the answer…",
}

export function nodeLabel(node: string): string {
  return NODE_LABELS[node] ?? `Running ${node}…`
}

export const RETRIEVAL_MODES: {
  value: RetrievalMode
  label: string
  description: string
}[] = [
  {
    value: "semantic",
    label: "Semantic",
    description: "Meaning-based similarity search (the default).",
  },
  {
    value: "keyword",
    label: "Keyword",
    description: "BM25 lexical search — best for exact terms, names, or identifiers.",
  },
  {
    value: "hybrid",
    label: "Hybrid",
    description: "Combines both via Reciprocal Rank Fusion.",
  },
]