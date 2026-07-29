import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { ArrowLeft, Library, Menu } from "lucide-react"

import type { Chat } from "@/features/chat/api"
import { Button } from "@/shared/components/ui/button"
import ChatsSidebar from "@/features/chat/components/ChatsSidebar"
import ChatArea from "@/features/chat/components/ChatArea"
import SourcesDrawer from "@/features/workspace/components/SourcesDrawer"

function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null)
  const [sourcesOpen, setSourcesOpen] = useState(false)
  const [chatsOpen, setChatsOpen] = useState(false)

  if (!projectId) return null

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

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setSourcesOpen(true)}
          className="shrink-0"
        >
          <Library className="size-3.5" data-icon="inline-start" />
          <span className="hidden sm:inline">Sources</span>
        </Button>
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
    </div>
  )
}

export default ProjectDetail