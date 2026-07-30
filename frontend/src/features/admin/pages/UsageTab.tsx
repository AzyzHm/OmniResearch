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

import { getLlmUsage, getSearchUsage } from "@/features/admin/api"
import { Button } from "@/shared/components/ui/button"
import MetricCard from "@/features/admin/components/MetricCard"

function UsageTab() {
  const llmQuery = useQuery({ queryKey: ["admin-llm-usage"], queryFn: getLlmUsage })
  const searchQuery = useQuery({
    queryKey: ["admin-search-usage"],
    queryFn: getSearchUsage,
  })

  const llmRows = llmQuery.data?.users ?? []
  const searchRows = searchQuery.data?.users ?? []

  const totalTokens = llmRows.reduce((sum, r) => sum + r.total_tokens, 0)
  const totalCalls = llmRows.reduce((sum, r) => sum + r.total_calls, 0)
  const mistralCalls = llmRows.reduce((sum, r) => sum + r.mistral_calls, 0)

  const totalCredits = searchRows.reduce((sum, r) => sum + r.total_credits, 0)
  const tavilyCredits = searchRows.reduce((sum, r) => sum + r.tavily_credits, 0)
  const exaCredits = searchRows.reduce((sum, r) => sum + r.exa_credits, 0)

  return (
    <div className="flex flex-col gap-10">
      <section>
        <div className="mb-1 flex items-center justify-between">
          <h2 className="font-display text-base font-medium text-ink">
            LLM Token Usage
          </h2>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => llmQuery.refetch()}
          >
            Refresh
          </Button>
        </div>
        <p className="mb-4 text-xs text-muted-foreground">
          Each user has a daily token quota (default 80,000, resets at UTC
          midnight), editable per-user in User Management. This view shows
          all-time totals, not remaining quota.
        </p>

        {llmQuery.isLoading && (
          <p className="text-sm text-muted-foreground">Loading...</p>
        )}
        {llmQuery.isError && (
          <p className="text-sm text-destructive">Failed to load LLM usage.</p>
        )}

        {!llmQuery.isLoading && !llmQuery.isError && llmRows.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No LLM usage recorded yet.
          </p>
        )}

        {llmRows.length > 0 && (
          <>
            <div className="grid grid-cols-3 gap-4">
              <MetricCard
                label="Total Tokens (all users)"
                value={totalTokens.toLocaleString()}
                color="teal"
              />
              <MetricCard label="Total LLM Calls" value={totalCalls} color="ink" />
              <MetricCard
                label="Mistral Fallback Calls"
                value={mistralCalls}
                delta={mistralCalls > 0 ? "Gemini quota was hit" : undefined}
                color="amber"
              />
            </div>

            <div className="mt-4 overflow-x-auto rounded-xl border border-border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50 text-left text-xs text-muted-foreground">
                    <th className="px-3 py-2 font-medium">Username</th>
                    <th className="px-3 py-2 font-medium">Total Calls</th>
                    <th className="px-3 py-2 font-medium">Total Tokens</th>
                    <th className="px-3 py-2 font-medium">Gemini Calls</th>
                    <th className="px-3 py-2 font-medium">Gemini Tokens</th>
                    <th className="px-3 py-2 font-medium">Mistral Calls</th>
                    <th className="px-3 py-2 font-medium">Mistral Tokens</th>
                  </tr>
                </thead>
                <tbody>
                  {llmRows.map((r) => (
                    <tr key={r.user_id} className="border-b border-border last:border-0">
                      <td className="px-3 py-2 text-ink">{r.username}</td>
                      <td className="px-3 py-2 font-mono text-xs">{r.total_calls}</td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {r.total_tokens.toLocaleString()}
                      </td>
                      <td className="px-3 py-2 font-mono text-xs">{r.gemini_calls}</td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {r.gemini_tokens.toLocaleString()}
                      </td>
                      <td className="px-3 py-2 font-mono text-xs">{r.mistral_calls}</td>
                      <td className="px-3 py-2 font-mono text-xs">
                        {r.mistral_tokens.toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div
              className="mt-4 rounded-xl border border-border p-3"
              style={{ height: Math.max(llmRows.length * 56, 140) }}
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={[...llmRows].sort((a, b) => a.total_tokens - b.total_tokens)}
                  layout="vertical"
                  margin={{ left: 24 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis
                    type="category"
                    dataKey="username"
                    width={90}
                    tick={{ fontSize: 12 }}
                    interval={0}
                  />
                  <Tooltip />
                  <Bar dataKey="total_tokens" fill="var(--color-teal)" radius={4} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </section>

      <section>
        <div className="mb-1 flex items-center justify-between">
          <h2 className="font-display text-base font-medium text-ink">
            Search Engine Usage
          </h2>
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => searchQuery.refetch()}
          >
            Refresh
          </Button>
        </div>
        <p className="mb-4 text-xs text-muted-foreground">
          Tracked in credits, not raw call counts — Tavily's "advanced" search
          depth costs 2 credits per call; everything else (Tavily
          basic/fast/ultra-fast, all Exa calls) is 1 credit.
        </p>

        {searchQuery.isLoading && (
          <p className="text-sm text-muted-foreground">Loading...</p>
        )}
        {searchQuery.isError && (
          <p className="text-sm text-destructive">Failed to load search usage.</p>
        )}

        {!searchQuery.isLoading && !searchQuery.isError && searchRows.length === 0 && (
          <p className="text-sm text-muted-foreground">
            No search usage recorded yet.
          </p>
        )}

        {searchRows.length > 0 && (
          <>
            <div className="grid grid-cols-3 gap-4">
              <MetricCard label="Total Credits" value={totalCredits} color="teal" />
              <MetricCard label="Tavily Credits" value={tavilyCredits} color="ink" />
              <MetricCard label="Exa Credits" value={exaCredits} color="amber" />
            </div>

            <div className="mt-4 overflow-x-auto rounded-xl border border-border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border bg-muted/50 text-left text-xs text-muted-foreground">
                    <th className="px-3 py-2 font-medium">Username</th>
                    <th className="px-3 py-2 font-medium">Total Credits</th>
                    <th className="px-3 py-2 font-medium">Total Calls</th>
                    <th className="px-3 py-2 font-medium">Tavily Credits</th>
                    <th className="px-3 py-2 font-medium">Tavily Calls</th>
                    <th className="px-3 py-2 font-medium">Exa Credits</th>
                    <th className="px-3 py-2 font-medium">Exa Calls</th>
                  </tr>
                </thead>
                <tbody>
                  {searchRows.map((r) => (
                    <tr key={r.user_id} className="border-b border-border last:border-0">
                      <td className="px-3 py-2 text-ink">{r.username}</td>
                      <td className="px-3 py-2 font-mono text-xs">{r.total_credits}</td>
                      <td className="px-3 py-2 font-mono text-xs">{r.total_calls}</td>
                      <td className="px-3 py-2 font-mono text-xs">{r.tavily_credits}</td>
                      <td className="px-3 py-2 font-mono text-xs">{r.tavily_calls}</td>
                      <td className="px-3 py-2 font-mono text-xs">{r.exa_credits}</td>
                      <td className="px-3 py-2 font-mono text-xs">{r.exa_calls}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            <div
              className="mt-4 rounded-xl border border-border p-3"
              style={{ height: Math.max(searchRows.length * 56, 140) }}
            >
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={[...searchRows].sort(
                    (a, b) => a.total_credits - b.total_credits
                  )}
                  layout="vertical"
                  margin={{ left: 24 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                  <XAxis type="number" tick={{ fontSize: 12 }} />
                  <YAxis
                    type="category"
                    dataKey="username"
                    width={90}
                    tick={{ fontSize: 12 }}
                    interval={0}
                  />
                  <Tooltip />
                  <Bar dataKey="total_credits" fill="var(--color-teal)" radius={4} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </>
        )}
      </section>
    </div>
  )
}

export default UsageTab