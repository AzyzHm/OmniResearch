import { cn } from "@/shared/lib/utils"

interface MetricCardProps {
  label: string
  value: string | number
  delta?: string
  color?: "teal" | "amber" | "ink"
}

const COLOR_CLASSES: Record<NonNullable<MetricCardProps["color"]>, string> = {
  teal: "border-l-teal text-teal",
  amber: "border-l-amber text-amber",
  ink: "border-l-ink text-ink",
}

function MetricCard({ label, value, delta, color = "teal" }: MetricCardProps) {
  return (
    <div
      className={cn(
        "rounded-lg border-l-4 bg-surface p-4 shadow-sm",
        COLOR_CLASSES[color].split(" ")[0],
      )}
    >
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="mt-0.5 font-display text-2xl font-semibold text-ink">{value}</p>
      {delta && <p className={cn("mt-0.5 text-xs", COLOR_CLASSES[color].split(" ")[1])}>{delta}</p>}
    </div>
  )
}

export default MetricCard
