import { useState } from "react"
import { ArrowUp } from "lucide-react"

import type { RetrievalMode } from "@/features/chat/api"
import { RETRIEVAL_MODES } from "@/features/chat/lib/chatMeta"
import { Button } from "@/shared/components/ui/button"
import { cn } from "@/shared/lib/utils"

interface ChatInputProps {
  disabled: boolean
  onSend: (message: string, retrievalMode: RetrievalMode) => void
}

function ChatInput({ disabled, onSend }: ChatInputProps) {
  const [value, setValue] = useState("")
  const [retrievalMode, setRetrievalMode] = useState<RetrievalMode>("semantic")

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    const trimmed = value.trim()
    if (!trimmed || disabled) return
    onSend(trimmed, retrievalMode)
    setValue("")
  }

  return (
    <form onSubmit={handleSubmit} className="border-t border-border p-3">
      <div className="mb-2 flex gap-1.5">
        {RETRIEVAL_MODES.map((mode) => (
          <button
            key={mode.value}
            type="button"
            title={mode.description}
            onClick={() => setRetrievalMode(mode.value)}
            className={cn(
              "rounded-full px-2.5 py-1 font-mono text-[0.7rem] font-medium transition-colors",
              retrievalMode === mode.value
                ? "bg-teal/15 text-teal"
                : "text-muted-foreground hover:bg-muted",
            )}
          >
            {mode.label}
          </button>
        ))}
      </div>

      <div className="flex items-end gap-2">
        <input
          value={value}
          onChange={(e) => setValue(e.target.value)}
          placeholder="Ask anything…"
          disabled={disabled}
          className="h-10 flex-1 rounded-full border border-input bg-background px-4 text-sm outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/50 disabled:opacity-60"
        />
        <Button
          type="submit"
          size="icon"
          className="rounded-full"
          disabled={disabled || !value.trim()}
          aria-label="Send message"
        >
          <ArrowUp className="size-4" />
        </Button>
      </div>
    </form>
  )
}

export default ChatInput
