import { useQuery } from "@tanstack/react-query"

import { getStats } from "@/features/admin/api"
import MetricCard from "@/features/admin/components/MetricCard"

function OverviewTab() {
  const { data: stats, isLoading, isError } = useQuery({
    queryKey: ["admin-stats"],
    queryFn: getStats,
  })

  if (isLoading) {
    return <p className="text-sm text-muted-foreground">Loading stats...</p>
  }

  if (isError || !stats) {
    return <p className="text-sm text-destructive">Failed to load stats.</p>
  }

  const isSuperadminView = stats.admin_users !== undefined

  return (
    <div>
      <div
        className={`grid gap-4 ${isSuperadminView ? "grid-cols-4" : "grid-cols-3"}`}
      >
        <MetricCard label="Total Users" value={stats.total_users} color="teal" />
        {isSuperadminView && (
          <MetricCard label="Total Admins" value={stats.admin_users!} color="amber" />
        )}
        <MetricCard
          label="Pending Approval"
          value={stats.pending_users}
          delta={stats.pending_users > 0 ? "⚠ Needs action" : undefined}
          color="amber"
        />
        <MetricCard label="Total Logins" value={stats.total_logins} color="ink" />
      </div>

      <div className="mt-8">
        <h2 className="mb-3 font-display text-base font-medium text-ink">
          Recent Login Activity
        </h2>
        {stats.recent_logins.length === 0 ? (
          <p className="text-sm text-muted-foreground">No login activity yet.</p>
        ) : (
          <div className="overflow-hidden rounded-xl border border-border">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/50 text-left text-xs text-muted-foreground">
                  <th className="px-3 py-2 font-medium">Username</th>
                  <th className="px-3 py-2 font-medium">Login Time</th>
                  <th className="px-3 py-2 font-medium">IP Address</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_logins.map((log, i) => (
                  <tr key={i} className="border-b border-border last:border-0">
                    <td className="px-3 py-2 text-ink">{log.username}</td>
                    <td className="px-3 py-2 font-mono text-xs text-muted-foreground">
                      {new Date(log.login_time).toLocaleString(undefined, {
                        year: "numeric",
                        month: "short",
                        day: "numeric",
                        hour: "2-digit",
                        minute: "2-digit",
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
        )}
      </div>
    </div>
  )
}

export default OverviewTab