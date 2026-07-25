import { useEffect, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"
import { MessageSquare, Pencil, Plus, Trash2 } from "lucide-react"

import {
  createChat,
  deleteChat,
  listChats,
  renameChat,
  type Chat,
} from "@/api/chats"
import { ApiError } from "@/lib/apiClient"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import ChatRenameDialog from "@/components/workspace/ChatRenameDialog"

interface ChatsSidebarProps {
  projectId: string
  selectedChatId: string | null
  onSelect: (chat: Chat) => void
}

function ChatsSidebar({ projectId, selectedChatId, onSelect }: ChatsSidebarProps) {
  const queryClient = useQueryClient()
  const queryKey = ["chats", projectId]

  const { data: chats, isLoading } = useQuery({
    queryKey,
    queryFn: () => listChats(projectId),
  })

  const [renameTarget, setRenameTarget] = useState<Chat | null>(null)
  const [renameInstance, setRenameInstance] = useState(0)
  const [renameError, setRenameError] = useState<string | null>(null)
  const [confirmingDeleteId, setConfirmingDeleteId] = useState<string | null>(null)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  useEffect(() => {
    if (!selectedChatId && chats && chats.length > 0) {
      onSelect(chats[0])
    }
  }, [chats, selectedChatId, onSelect])

  const [createError, setCreateError] = useState<string | null>(null)

  const createMutation = useMutation({
    mutationFn: () => createChat(projectId),
    onMutate: () => setCreateError(null),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey })
      onSelect(created)
    },
    onError: (err) => {
      setCreateError(err instanceof ApiError ? err.message : "Couldn't start a new chat.")
    },
  })

  const renameMutation = useMutation({
    mutationFn: ({ id, name }: { id: string; name: string }) =>
      renameChat(id, name),
    onSuccess: (updated) => {
      queryClient.invalidateQueries({ queryKey })
      setRenameTarget(null)
      setRenameError(null)
      if (selectedChatId === updated.id) onSelect(updated)
    },
    onError: (err) => {
      setRenameError(err instanceof ApiError ? err.message : "Something went wrong.")
    },
  })

  const deleteMutation = useMutation({
    mutationFn: deleteChat,
    onMutate: async () => {
      setDeleteError(null)
      await queryClient.cancelQueries({ queryKey })
    },
    onSuccess: (_data, chatId) => {
      queryClient.setQueryData<Chat[]>(queryKey, (old) =>
        old ? old.filter((c) => c.id !== chatId) : old
      )
      queryClient.invalidateQueries({ queryKey })
    },
    onError: (err) => {
      setDeleteError(err instanceof ApiError ? err.message : "Couldn't delete the chat.")
    },
    onSettled: () => setConfirmingDeleteId(null),
  })

  return (
    <div className="flex w-56 shrink-0 flex-col gap-2 border-r border-border p-3">
      <Button
        type="button"
        size="sm"
        className="w-full"
        onClick={() => createMutation.mutate()}
        disabled={createMutation.isPending}
      >
        <Plus className="size-3.5" data-icon="inline-start" />
        {createMutation.isPending ? "Starting..." : "New chat"}
      </Button>

      {createError && (
        <p className="px-1 text-sm text-destructive">{createError}</p>
      )}

      {isLoading && (
        <p className="px-1 text-sm text-muted-foreground">Loading...</p>
      )}

      {deleteError && (
        <p className="px-1 text-sm text-destructive">{deleteError}</p>
      )}

      <div className="flex flex-col gap-1 overflow-y-auto">
        {chats?.map((chat) => {
          const selected = chat.id === selectedChatId
          const confirming = confirmingDeleteId === chat.id

          return (
            <div
              key={chat.id}
              className={cn(
                "group flex items-center gap-1.5 rounded-lg px-2 py-1.5 text-sm transition-colors",
                selected ? "bg-teal/10 text-teal" : "text-ink hover:bg-muted"
              )}
            >
              <button
                type="button"
                onClick={() => onSelect(chat)}
                className="flex flex-1 items-center gap-2 overflow-hidden text-left"
              >
                <MessageSquare className="size-3.5 shrink-0" />
                <span className="truncate">{chat.name}</span>
              </button>

              {confirming ? (
                <div className="flex shrink-0 items-center gap-1">
                  <Button
                    type="button"
                    size="icon-xs"
                    variant="destructive"
                    disabled={deleteMutation.isPending}
                    onClick={() => deleteMutation.mutate(chat.id)}
                    aria-label="Confirm delete"
                  >
                    <Trash2 className="size-3" />
                  </Button>
                  <Button
                    type="button"
                    size="icon-xs"
                    variant="ghost"
                    disabled={deleteMutation.isPending}
                    onClick={() => setConfirmingDeleteId(null)}
                    aria-label="Cancel delete"
                  >
                    ×
                  </Button>
                </div>
              ) : (
                <div className="flex shrink-0 items-center gap-0.5 opacity-0 group-hover:opacity-100">
                  <Button
                    type="button"
                    size="icon-xs"
                    variant="ghost"
                    onClick={() => {
                      setRenameInstance((n) => n + 1)
                      setRenameTarget(chat)
                      setRenameError(null)
                    }}
                    aria-label="Rename chat"
                  >
                    <Pencil className="size-3" />
                  </Button>
                  <Button
                    type="button"
                    size="icon-xs"
                    variant="ghost"
                    onClick={() => setConfirmingDeleteId(chat.id)}
                    aria-label="Delete chat"
                  >
                    <Trash2 className="size-3" />
                  </Button>
                </div>
              )}
            </div>
          )
        })}
      </div>

      <ChatRenameDialog
        key={renameInstance}
        open={!!renameTarget}
        onOpenChange={(open) => {
          if (!open) {
            setRenameTarget(null)
            setRenameError(null)
          }
        }}
        initialName={renameTarget?.name ?? ""}
        isSubmitting={renameMutation.isPending}
        error={renameError}
        onSubmit={(name) => {
          if (renameTarget) renameMutation.mutate({ id: renameTarget.id, name })
        }}
      />
    </div>
  )
}

export default ChatsSidebar