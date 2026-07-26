import { useEffect, useState } from "react"
import { Hourglass } from "lucide-react"

interface QuotaExceededCardProps {
  used?: number
  limit?: number
  resetAt?: string
}

function formatCountdown(resetAt: string): string | null {
  const resetTime = new Date(resetAt).getTime()
  if (Number.isNaN(resetTime)) return null
  const remainingMs = resetTime - Date.now()
  const totalMinutes = Math.max(Math.floor(remainingMs / 60000), 0)
  const hours = Math.floor(totalMinutes / 60)
  const minutes = totalMinutes % 60
  return `${hours}h ${minutes}m`
}

function QuotaExceededCard({ used, limit, resetAt }: QuotaExceededCardProps) {
  const [, forceTick] = useState(0)
  useEffect(() => {
    const id = setInterval(() => forceTick((n) => n + 1), 60000)
    return () => clearInterval(id)
  }, [])

  const pct =
    used !== undefined && limit !== undefined && limit > 0
      ? Math.min(Math.round((used / limit) * 100), 100)
      : null
  const countdown = resetAt ? formatCountdown(resetAt) : null
  const resetLabel = resetAt
    ? new Date(resetAt).toLocaleString(undefined, {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      })
    : null

  return (
    <div className="rounded-xl border border-amber/40 bg-amber/10 p-4">
      <div className="flex items-center gap-2">
        <Hourglass className="size-4 text-amber" />
        <span className="text-sm font-semibold text-amber">
          Daily token quota reached
        </span>
      </div>
      <p className="mt-1.5 text-sm text-ink">
        You&apos;ve used all of your daily tokens for today. You can send
        messages again once your quota resets.
      </p>

      {pct !== null && (
        <div className="mt-3">
          <div className="h-2 overflow-hidden rounded-full bg-muted">
            <div className="h-full bg-amber" style={{ width: `${pct}%` }} />
          </div>
          <p className="mt-1 font-mono text-xs text-muted-foreground">
            {used?.toLocaleString()} / {limit?.toLocaleString()} tokens used
            today
          </p>
        </div>
      )}

      {resetLabel && (
        <p className="mt-2 text-xs text-muted-foreground">
          Resets at <span className="font-medium text-ink">{resetLabel}</span>
          {countdown && (
            <>
              {" "}
              • in <span className="font-medium text-ink">{countdown}</span>
            </>
          )}
        </p>
      )}
    </div>
  )
}

export default QuotaExceededCard