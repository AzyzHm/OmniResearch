import { useState } from "react"
import { useParams, Link } from "react-router-dom"
import { ArrowLeft, Library } from "lucide-react"

import type { Chat } from "@/api/chats"
import { Button } from "@/components/ui/button"
import ChatsSidebar from "@/components/workspace/ChatsSidebar"
import ChatArea from "@/components/workspace/ChatArea"
import SourcesDrawer from "@/components/workspace/SourcesDrawer"

function ProjectDetail() {
  const { projectId } = useParams<{ projectId: string }>()
  const [selectedChat, setSelectedChat] = useState<Chat | null>(null)
  const [sourcesOpen, setSourcesOpen] = useState(false)

  if (!projectId) return null

  return (
    <div className="flex h-[calc(100vh-3.5rem)] flex-col">
      <div className="flex items-center justify-between border-b border-border px-4 py-2">
        <Link
          to="/app"
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-ink"
        >
          <ArrowLeft className="size-3.5" />
          Back to projects
        </Link>

        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => setSourcesOpen(true)}
        >
          <Library className="size-3.5" data-icon="inline-start" />
          Sources
        </Button>
      </div>

      <div className="flex flex-1 overflow-hidden">
        <ChatsSidebar
          projectId={projectId}
          selectedChatId={selectedChat?.id ?? null}
          onSelect={setSelectedChat}
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