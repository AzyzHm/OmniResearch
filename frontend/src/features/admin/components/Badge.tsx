import { cn } from "@/shared/lib/utils"

interface BadgeProps {
  children: React.ReactNode
  color?: "teal" | "amber" | "muted" | "destructive"
}

const COLOR_CLASSES: Record<NonNullable<BadgeProps["color"]>, string> = {
  teal: "bg-teal/15 text-teal border-teal/30",
  amber: "bg-amber/15 text-amber border-amber/30",
  muted: "bg-muted text-muted-foreground border-border",
  destructive: "bg-destructive/10 text-destructive border-destructive/30",
}

function Badge({ children, color = "muted" }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full border px-2.5 py-0.5 font-mono text-[0.7rem] font-medium",
        COLOR_CLASSES[color]
      )}
    >
      {children}
    </span>
  )
}

export default Badge