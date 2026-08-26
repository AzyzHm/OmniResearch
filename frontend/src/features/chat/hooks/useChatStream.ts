import { useCallback, useEffect, useRef, useState } from "react"

import { streamChatMessage, type RetrievalMode } from "@/features/chat/api"
import { ApiError } from "@/shared/lib/apiClient"

export interface ChatStreamError {
  message: string
  code?: string
  used?: number
  limit?: number
  resetAt?: string
}

interface UseChatStreamResult {
  isStreaming: boolean
  nodeName: string | null
  error: ChatStreamError | null
  send: (chatId: string, message: string, retrievalMode: RetrievalMode) => void
  clearError: () => void
}

export function useChatStream(): UseChatStreamResult {
  const [isStreaming, setIsStreaming] = useState(false)
  const [nodeName, setNodeName] = useState<string | null>(null)
  const [error, setError] = useState<ChatStreamError | null>(null)
  const abortRef = useRef<AbortController | null>(null)

  useEffect(() => {
    return () => abortRef.current?.abort()
  }, [])

  const send = useCallback((chatId: string, message: string, retrievalMode: RetrievalMode) => {
    abortRef.current?.abort()
    const controller = new AbortController()
    abortRef.current = controller

    setError(null)
    setIsStreaming(true)
    setNodeName(null)

    ;(async () => {
      try {
        for await (const event of streamChatMessage(
          chatId,
          message,
          retrievalMode,
          controller.signal,
        )) {
          if (event.type === "node") {
            setNodeName(event.node)
          } else if (event.type === "error") {
            setError({
              message: event.detail,
              code: event.code,
              used: event.used,
              limit: event.limit,
              resetAt: event.reset_at,
            })
          }
        }
      } catch (err) {
        if (err instanceof DOMException && err.name === "AbortError") return
        setError({
          message: err instanceof ApiError ? err.message : "Something went wrong.",
        })
      } finally {
        setIsStreaming(false)
        setNodeName(null)
      }
    })()
  }, [])

  return {
    isStreaming,
    nodeName,
    error,
    send,
    clearError: () => setError(null),
  }
}
