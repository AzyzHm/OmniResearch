import { apiClient, ApiError, API_BASE_URL } from "@/lib/apiClient"

export type RetrievalMode = "semantic" | "keyword" | "hybrid"

export interface Chat {
  id: string
  project_id: string
  name: string
  created_at: string
}

export interface Source {
  index: number
  source_name: string
  collection_id: string | null
  item_id: string | null
}

export interface Message {
  id: string
  chat_id: string
  role: "user" | "assistant" | string
  content: string
  created_at: string
  sources?: Source[] | null
}

export interface ChatStreamNodeEvent {
  type: "node"
  node: string
}

export interface ChatStreamDoneEvent {
  type: "done"
  answer: string
  sources: Source[]
}

export interface ChatStreamErrorEvent {
  type: "error"
  detail: string
  code?: string
  used?: number
  limit?: number
  reset_at?: string
}

export type ChatStreamEvent =
  | ChatStreamNodeEvent
  | ChatStreamDoneEvent
  | ChatStreamErrorEvent

export function listChats(projectId: string) {
  return apiClient.get<Chat[]>(`/projects/${projectId}/chats`)
}

export function createChat(projectId: string, name?: string) {
  return apiClient.post<Chat>(`/projects/${projectId}/chats`, { name: name ?? "New Chat" })
}

export function renameChat(chatId: string, name: string) {
  return apiClient.put<Chat>(`/chats/${chatId}`, { name })
}

export function deleteChat(chatId: string) {
  return apiClient.delete<void>(`/chats/${chatId}`)
}

export function listMessages(chatId: string) {
  return apiClient.get<Message[]>(`/chats/${chatId}/messages`)
}

/**
 * Streams a chat reply via SSE. The backend's route accepts POST with a JSON
 * body and returns text/event-stream, so this can't use the native
 * EventSource API (GET-only, no custom body) — it reads the raw response
 * stream and parses "data: {...}\n\n" frames by hand instead.
 */
export async function* streamChatMessage(
  chatId: string,
  message: string,
  retrievalMode: RetrievalMode,
  signal?: AbortSignal
): AsyncGenerator<ChatStreamEvent> {
  const response = await fetch(`${API_BASE_URL}/chats/${chatId}/message/stream`, {
    method: "POST",
    credentials: "include",
    cache: "no-store",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, retrieval_mode: retrievalMode }),
    signal,
  })

  if (!response.ok || !response.body) {
    const text = await response.text().catch(() => "")
    let detail: unknown = "Failed to send message."
    try {
      detail = JSON.parse(text)?.detail ?? detail
    } catch {
      // Non-JSON error body — fall back to the generic message above.
    }
    throw new ApiError(response.status, detail)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    let separatorIndex: number
    while ((separatorIndex = buffer.indexOf("\n\n")) !== -1) {
      const rawFrame = buffer.slice(0, separatorIndex)
      buffer = buffer.slice(separatorIndex + 2)

      const line = rawFrame.trim()
      if (!line.startsWith("data:")) continue

      const jsonText = line.slice("data:".length).trim()
      try {
        yield JSON.parse(jsonText) as ChatStreamEvent
      } catch {
        // Skip a malformed frame rather than breaking the whole stream.
      }
    }
  }
}