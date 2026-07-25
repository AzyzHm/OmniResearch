import { useEffect, useMemo, useRef, useState } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { MessageSquare } from "lucide-react"

import { listMessages, type RetrievalMode } from "@/api/chats"
import { useChatStream } from "@/hooks/useChatStream"
import { nodeLabel } from "@/lib/chatMeta"
import ChatMessageBubble from "@/components/workspace/ChatMessageBubble"
import ChatInput from "@/components/workspace/ChatInput"
import QuotaExceededCard from "@/components/workspace/QuotaExceededCard"
import ChatErrorCard from "@/components/workspace/ChatErrorCard"

interface ChatAreaProps {
  chatId: string
  chatName: string
}

function ChatArea({ chatId, chatName }: ChatAreaProps) {
  const queryClient = useQueryClient()
  const queryKey = useMemo(() => ["messages", chatId], [chatId])
  const bottomRef = useRef<HTMLDivElement>(null)

  const { data: messages, isLoading } = useQuery({
    queryKey,
    queryFn: () => listMessages(chatId),
  })

  const chatStream = useChatStream()
  const [pendingUserEcho, setPendingUserEcho] = useState<string | null>(null)

  const wasStreamingRef = useRef(false)
  useEffect(() => {
    if (wasStreamingRef.current && !chatStream.isStreaming) {
      queryClient.invalidateQueries({ queryKey }).then(() => {
        setPendingUserEcho(null)
      })
    }
    wasStreamingRef.current = chatStream.isStreaming
  }, [chatStream.isStreaming, queryClient, queryKey])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, pendingUserEcho, chatStream.nodeName, chatStream.error])

  function handleSend(message: string, mode: RetrievalMode) {
    setPendingUserEcho(message)
    chatStream.send(chatId, message, mode)
  }

  return (
    <div className="flex h-full flex-1 flex-col">
      <div className="border-b border-border px-4 py-3">
        <p className="text-sm text-muted-foreground">
          Chat: <span className="font-medium text-ink">{chatName}</span>
        </p>
      </div>

      <div className="flex-1 space-y-3 overflow-y-auto px-4 py-4">
        {isLoading && (
          <p className="text-sm text-muted-foreground">Loading messages...</p>
        )}

        {!isLoading && messages && messages.length === 0 && !pendingUserEcho && (
          <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
            <MessageSquare className="size-6" />
            <p className="text-sm">
              No messages yet. Type below to start the conversation.
            </p>
          </div>
        )}

        {messages?.map((msg) => (
          <ChatMessageBubble key={msg.id} role={msg.role} content={msg.content} />
        ))}

        {pendingUserEcho && (
          <ChatMessageBubble role="user" content={pendingUserEcho} />
        )}

        {chatStream.isStreaming && (
          <ChatMessageBubble
            role="assistant"
            content={
              chatStream.nodeName ? `_${nodeLabel(chatStream.nodeName)}_` : "_Thinking…_"
            }
          />
        )}

        {chatStream.error &&
          (chatStream.error.code === "quota_exceeded" ? (
            <QuotaExceededCard
              used={chatStream.error.used}
              limit={chatStream.error.limit}
              resetAt={chatStream.error.resetAt}
            />
          ) : (
            <ChatErrorCard message={chatStream.error.message} />
          ))}

        <div ref={bottomRef} />
      </div>

      <ChatInput disabled={chatStream.isStreaming} onSend={handleSend} />
    </div>
  )
}

export default ChatArea