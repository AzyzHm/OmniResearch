import { useState } from "react"
import { useQuery } from "@tanstack/react-query"
import {
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

import { getLogs } from "@/features/admin/api"
import { Button } from "@/shared/components/ui/button"
import { Input } from "@/shared/components/ui/input"

const LIMIT_OPTIONS = [50, 100, 200, 500]

function LogsTab() {
  const [usernameFilter, setUsernameFilter] = useState("")
  const [limit, setLimit] = useState(100)
  const [loaded, setLoaded] = useState(false)

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["admin-logs", limit, usernameFilter],
    queryFn: () => getLogs(limit, 0, usernameFilter || undefined),
    enabled: false,
  })

  function handleLoad() {
    setLoaded(true)
    refetch()
  }

  const chartData = (() => {
    if (!data?.logs?.length) return []
    const counts = new Map<string, number>()
    data.logs.forEach((log) => {
      const date = new Date(log.login_time).toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      })
      counts.set(date, (counts.get(date) ?? 0) + 1)
    })
    return Array.from(counts.entries()).map(([date, logins]) => ({ date, logins }))
  })()

  return (
    <div>
      <h2 className="mb-4 font-display text-base font-medium text-ink">
        Login Activity Log
      </h2>

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Input
          value={usernameFilter}
          onChange={(e) => setUsernameFilter(e.target.value)}
          placeholder="Filter by username (leave blank for all)"
          className="max-w-xs"
        />
        <div className="flex gap-1">
          {LIMIT_OPTIONS.map((n) => (
            <Button
              key={n}
              type="button"
              size="sm"
              variant={limit === n ? "default" : "outline"}
              onClick={() => setLimit(n)}
            >
              {n}
            </Button>
          ))}
        </div>
        <Button type="button" size="sm" onClick={handleLoad}>
          Load Logs
        </Button>
      </div>

      {!loaded && (
        <p className="text-sm text-muted-foreground">
          Choose your filters and click "Load Logs".
        </p>
      )}

      {loaded && isLoading && (
        <p className="text-sm text-muted-foreground">Loading logs...</p>
      )}
      {loaded && isError && (
        <p className="text-sm text-destructive">Failed to load logs.</p>
      )}

      {loaded && data && (
        <>
          <p className="mb-2 text-sm text-muted-foreground">
            {data.total} total log entries (showing {data.logs.length})
          </p>

          {data.logs.length === 0 ? (
            <p className="text-sm text-muted-foreground">No login logs found.</p>
          ) : (
            <>
              <div className="overflow-x-auto rounded-xl border border-border">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border bg-muted/50 text-left text-xs text-muted-foreground">
                      <th className="px-3 py-2 font-medium">Username</th>
                      <th className="px-3 py-2 font-medium">Login Time (UTC)</th>
                      <th className="px-3 py-2 font-medium">IP Address</th>
                    </tr>
                  </thead>
                  <tbody>
                    {data.logs.map((log) => (
                      <tr key={log.id} className="border-b border-border last:border-0">
                        <td className="px-3 py-2 text-ink">{log.username}</td>
                        <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                          {new Date(log.login_time).toLocaleString(undefined, {
                            year: "numeric",
                            month: "short",
                            day: "numeric",
                            hour: "2-digit",
                            minute: "2-digit",
                            second: "2-digit",
                          })}
                        </td>
                        <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                          {log.ip_address ?? "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <h3 className="mt-6 mb-2 font-display text-base font-medium text-ink">
                Logins Per Day
              </h3>
              <div className="h-64 rounded-xl border border-border p-3">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={chartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="date" tick={{ fontSize: 12 }} />
                    <YAxis allowDecimals={false} tick={{ fontSize: 12 }} />
                    <Tooltip />
                    <Bar dataKey="logins" fill="var(--color-teal)" radius={4} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}

export default LogsTab