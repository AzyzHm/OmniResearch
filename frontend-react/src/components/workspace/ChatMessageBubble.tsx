import ReactMarkdown from "react-markdown"
import { cn } from "@/lib/utils"

interface ChatMessageBubbleProps {
  role: "user" | "assistant" | string
  content: string
}

function ChatMessageBubble({ role, content }: ChatMessageBubbleProps) {
  const isUser = role === "user"

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isUser
            ? "bg-teal text-white"
            : "bg-surface text-ink border border-border"
        )}
      >
        {isUser ? (
          <p className="whitespace-pre-wrap">{content}</p>
        ) : (
          <div
            className={cn(
              "[&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
              "[&_p]:my-2 [&_ul]:my-2 [&_ol]:my-2 [&_ul]:list-disc [&_ol]:list-decimal [&_li]:my-0.5",
              "[&_ul]:pl-5 [&_ol]:pl-5 [&_strong]:font-semibold",
              "[&_a]:text-teal [&_a]:underline [&_a]:underline-offset-2",
              "[&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-xs",
              "[&_pre]:my-2 [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-ink [&_pre]:p-3 [&_pre]:text-xs [&_pre]:text-paper",
              "[&_pre_code]:bg-transparent [&_pre_code]:p-0"
            )}
          >
            <ReactMarkdown>{content}</ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  )
}

export default ChatMessageBubble