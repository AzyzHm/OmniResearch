import { useState } from "react"
import ReactMarkdown from "react-markdown"
import { BookmarkPlus, Check, ExternalLink } from "lucide-react"

import type { Source } from "@/features/chat/api"
import { shortenUrl } from "@/shared/lib/shortenUrl"
import { cn } from "@/shared/lib/utils"
import { Button } from "@/shared/components/ui/button"
import SaveToNoteDialog from "@/features/notes/components/SaveToNoteDialog"
import ItemContentModal from "@/features/collections/components/ItemContentModal"

interface ChatMessageBubbleProps {
  role: "user" | "assistant" | string
  content: string
  sources?: Source[] | null
  messageId?: string
  projectId?: string
}

function isUrl(value: string): boolean {
  try {
    new URL(value)
    return true
  } catch {
    return false
  }
}

/** Collections only ever ingest PDF or TXT uploads, keyed off the filename
 * extension (see backend EXT_TO_SOURCE_TYPE) — non-URL sources are always
 * one of the two. */
function fileSourceType(sourceName: string): "pdf" | "txt" {
  return sourceName.toLowerCase().endsWith(".pdf") ? "pdf" : "txt"
}

function ChatMessageBubble({
  role,
  content,
  sources,
  messageId,
  projectId,
}: ChatMessageBubbleProps) {
  const isUser = role === "user"
  const canSave = !isUser && !!messageId && !!projectId

  const [saveDialogOpen, setSaveDialogOpen] = useState(false)
  const [justSaved, setJustSaved] = useState(false)
  const [previewSource, setPreviewSource] = useState<Source | null>(null)

  function handleSaved() {
    setJustSaved(true)
    window.setTimeout(() => setJustSaved(false), 2000)
  }

  return (
    <div className={cn("flex", isUser ? "justify-end" : "justify-start")}>
      <div
        className={cn(
          "group/bubble relative max-w-[85%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed",
          isUser ? "bg-teal text-white" : "bg-surface text-ink border border-border",
        )}
      >
        {canSave && (
          <Button
            type="button"
            size="icon-xs"
            variant="ghost"
            className="absolute top-1.5 right-1.5 opacity-100 md:opacity-0 md:group-hover/bubble:opacity-100"
            onClick={() => setSaveDialogOpen(true)}
            aria-label="Save to note"
            title="Save to note"
          >
            {justSaved ? (
              <Check className="size-3.5 text-teal" />
            ) : (
              <BookmarkPlus className="size-3.5" />
            )}
          </Button>
        )}

        {isUser ? (
          <p className="whitespace-pre-wrap">{content}</p>
        ) : (
          <>
            <div
              className={cn(
                "[&>*:first-child]:mt-0 [&>*:last-child]:mb-0",
                canSave && "pr-6",
                "[&_p]:my-2 [&_ul]:my-2 [&_ol]:my-2 [&_ul]:list-disc [&_ol]:list-decimal [&_li]:my-0.5",
                "[&_ul]:pl-5 [&_ol]:pl-5 [&_strong]:font-semibold",
                "[&_a]:text-teal [&_a]:underline [&_a]:underline-offset-2",
                "[&_code]:rounded [&_code]:bg-muted [&_code]:px-1 [&_code]:py-0.5 [&_code]:font-mono [&_code]:text-xs",
                "[&_pre]:my-2 [&_pre]:overflow-x-auto [&_pre]:rounded-lg [&_pre]:bg-ink [&_pre]:p-3 [&_pre]:text-xs [&_pre]:text-paper",
                "[&_pre_code]:bg-transparent [&_pre_code]:p-0",
              )}
            >
              <ReactMarkdown>{content}</ReactMarkdown>
            </div>

            {sources && sources.length > 0 && (
              <div className="mt-2 border-t border-border pt-2">
                <p className="mb-1 font-mono text-[0.65rem] tracking-wide text-muted-foreground uppercase">
                  Sources
                </p>
                <ul className="space-y-1">
                  {sources.map((s) => (
                    <li key={s.index} className="flex items-start gap-1.5 text-xs">
                      <span className="shrink-0 font-mono text-muted-foreground">[{s.index}]</span>
                      {isUrl(s.source_name) ? (
                        <a
                          href={s.source_name}
                          target="_blank"
                          rel="noopener noreferrer"
                          title={s.source_name}
                          className="inline-flex min-w-0 items-center gap-1 text-teal hover:underline"
                        >
                          <span className="truncate">{shortenUrl(s.source_name)}</span>
                          <ExternalLink className="size-2.5 shrink-0" />
                        </a>
                      ) : s.collection_id && s.item_id ? (
                        <button
                          type="button"
                          onClick={() => setPreviewSource(s)}
                          title={s.source_name}
                          className="min-w-0 truncate text-left text-teal hover:underline"
                        >
                          {s.source_name}
                        </button>
                      ) : (
                        <span className="truncate text-muted-foreground">{s.source_name}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </>
        )}
      </div>

      {!isUser && messageId && projectId && (
        <SaveToNoteDialog
          open={saveDialogOpen}
          onOpenChange={setSaveDialogOpen}
          projectId={projectId}
          messageId={messageId}
          onSaved={handleSaved}
        />
      )}

      {!isUser && (
        <ItemContentModal
          collectionId={previewSource?.collection_id ?? ""}
          item={
            previewSource?.item_id
              ? {
                  id: previewSource.item_id,
                  name: previewSource.source_name,
                  source_type: fileSourceType(previewSource.source_name),
                }
              : null
          }
          onOpenChange={(open) => {
            if (!open) setPreviewSource(null)
          }}
          highlightText={previewSource?.content}
        />
      )}
    </div>
  )
}

export default ChatMessageBubble
