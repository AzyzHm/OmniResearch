import { TriangleAlert } from "lucide-react"

function ChatErrorCard({ message }: { message: string }) {
  return (
    <div className="rounded-xl border border-destructive/40 bg-destructive/10 p-4">
      <div className="flex items-center gap-2">
        <TriangleAlert className="size-4 text-destructive" />
        <span className="text-sm font-semibold text-destructive">Something went wrong</span>
      </div>
      <p className="mt-1.5 text-sm text-ink">{message}</p>
    </div>
  )
}

export default ChatErrorCard
