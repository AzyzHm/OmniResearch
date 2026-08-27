import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import ReactMarkdown from "react-markdown"
import { ExternalLink, MessageSquareText, Trash2 } from "lucide-react"

import { listNoteItems, removeNoteItem, type Note, type NoteItem } from "@/features/notes/api"
import { ApiError } from "@/shared/lib/apiClient"
import { shortenUrl } from "@/shared/lib/shortenUrl"
import { Button } from "@/shared/components/ui/button"

function isUrl(value: string): boolean {
  try {
    new URL(value)
    return true
  } catch {
    return false
  }
}

interface NoteItemsPanelProps {
  note: Note
  onJumpToChat?: (chatId: string) => void
}

function NoteItemsPanel({ note, onJumpToChat }: NoteItemsPanelProps) {
  const queryClient = useQueryClient()
  const queryKey = ["note-items", note.id]

  const { data: items, isLoading } = useQuery({
    queryKey,
    queryFn: () => listNoteItems(note.id),
  })

  const removeMutation = useMutation({
    mutationFn: (itemId: string) => removeNoteItem(note.id, itemId),
    onMutate: async (itemId) => {
      await queryClient.cancelQueries({ queryKey })
      queryClient.setQueryData<NoteItem[]>(queryKey, (old) =>
        old ? old.filter((i) => i.id !== itemId) : old,
      )
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey }),
  })

  return (
    <div className="flex-1 overflow-y-auto px-4 py-4">
      <div className="mb-4">
        <h2 className="font-display text-lg font-medium text-ink">{note.name}</h2>
        <p className="text-sm text-muted-foreground">
          {items?.length ?? 0} saved message{items?.length === 1 ? "" : "s"}
        </p>
      </div>

      {removeMutation.error && (
        <p className="mb-4 text-sm text-destructive">
          {removeMutation.error instanceof ApiError
            ? removeMutation.error.message
            : "Couldn't remove that message."}
        </p>
      )}

      {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}

      {!isLoading && items && items.length === 0 && (
        <div className="flex flex-col items-center gap-2 py-8 text-center text-muted-foreground">
          <MessageSquareText className="size-6" />
          <p className="text-sm">
            No messages saved yet. Use the save button on any chat reply to add it here.
          </p>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {items?.map((item) => (
          <div key={item.id} className="rounded-xl border border-border p-3 text-sm">
            <div className="mb-2 flex items-start justify-between gap-2">
              <span className="font-mono text-[0.65rem] tracking-wide text-muted-foreground uppercase">
                {item.role === "user" ? "You" : "Assistant"}
              </span>
              <div className="flex shrink-0 items-center gap-1">
                {onJumpToChat && (
                  <Button
                    type="button"
                    size="xs"
                    variant="ghost"
                    onClick={() => onJumpToChat(item.chat_id)}
                  >
                    Open chat
                  </Button>
                )}
                <Button
                  type="button"
                  size="icon-xs"
                  variant="ghost"
                  disabled={removeMutation.isPending}
                  onClick={() => removeMutation.mutate(item.id)}
                  aria-label="Remove from note"
                >
                  <Trash2 className="size-3.5" />
                </Button>
              </div>
            </div>

            <div
              className={
                "text-ink [&>*:first-child]:mt-0 [&>*:last-child]:mb-0 " +
                "[&_p]:my-1.5 [&_ul]:my-1.5 [&_ol]:my-1.5 [&_ul]:list-disc [&_ol]:list-decimal " +
                "[&_ul]:pl-5 [&_ol]:pl-5 [&_strong]:font-semibold"
              }
            >
              <ReactMarkdown>{item.content}</ReactMarkdown>
            </div>

            {item.sources && item.sources.length > 0 && (
              <div className="mt-2 border-t border-border pt-2">
                <p className="mb-1 font-mono text-[0.65rem] tracking-wide text-muted-foreground uppercase">
                  Sources
                </p>
                <ul className="space-y-1">
                  {item.sources.map((s) => (
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
                      ) : (
                        <span className="truncate text-muted-foreground">{s.source_name}</span>
                      )}
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default NoteItemsPanel
