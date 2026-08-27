import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { useQuery } from "@tanstack/react-query"
import { ArrowLeft, Library, Menu, NotebookText } from "lucide-react"

import type { Chat } from "@/features/chat/api"
import { listChats } from "@/features/chat/api"
import { Button } from "@/shared/components/ui/button"
import ChatsSidebar from "@/features/chat/components/ChatsSidebar"
import ChatArea from "@/features/chat/components/ChatArea"
import SourcesDrawer from "@/features/workspace/components/SourcesDrawer"
import NotesDrawer from "@/features/workspace/components/NotesDrawer"

function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null)
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const [notesOpen, setNotesOpen] = useState(false)
  const [chatsOpen, setChatsOpen] = useState(false)

  const { data: chats } = useQuery({
    queryKey: ["chats", projectId],
    queryFn: () => listChats(projectId as string),
    enabled: !!projectId,
  })

  if (!projectId) return null

  function handleJumpToChat(chatId: string) {
    const chat = chats?.find((c) => c.id === chatId)
    if (chat) setSelectedChat(chat)
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      <div className="flex items-center justify-between gap-2 border-b border-border px-3 py-2 sm:px-4">
        <div className="flex min-w-0 items-center gap-1">
          <Button
            type="button"
            size="icon-xs"
            variant="ghost"
            className="md:hidden"
            onClick={() => setChatsOpen(true)}
            aria-label="Open chats"
          >
            <Menu className="size-4" />
          </Button>

          <Link
            to="/app"
            className="inline-flex shrink-0 items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-ink"
          >
            <ArrowLeft className="size-3.5" />
            <span className="hidden sm:inline">Back to projects</span>
          </Link>

          {selectedChat && (
            <span className="truncate text-sm font-medium text-ink sm:hidden">
              {selectedChat.name}
            </span>
          )}
        </div>

        <div className="flex shrink-0 items-center gap-2">
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setNotesOpen(true)}
          >
            <NotebookText className="size-3.5" data-icon="inline-start" />
            <span className="hidden sm:inline">Notes</span>
          </Button>

          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => setSourcesOpen(true)}
          >
            <Library className="size-3.5" data-icon="inline-start" />
            <span className="hidden sm:inline">Sources</span>
          </Button>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <ChatsSidebar
          projectId={projectId}
          selectedChatId={selectedChat?.id ?? null}
          onSelect={setSelectedChat}
          mobileOpen={chatsOpen}
          onMobileClose={() => setChatsOpen(false)}
        />

        {selectedChat ? (
          <ChatArea
            key={selectedChat.id}
            projectId={projectId}
            chatId={selectedChat.id}
            chatName={selectedChat.name}
          />
        ) : (
          <div className="flex flex-1 items-center justify-center text-center text-sm text-muted-foreground">
            Start a chat to begin exploring this project.
          </div>
        )}
      </div>

      <SourcesDrawer
        projectId={projectId}
        open={sourcesOpen}
        onClose={() => setSourcesOpen(false)}
      />

      <NotesDrawer
        projectId={projectId}
        open={notesOpen}
        onClose={() => setNotesOpen(false)}
        onJumpToChat={handleJumpToChat}
      />
    </div>
  )
}

export default ProjectDetail