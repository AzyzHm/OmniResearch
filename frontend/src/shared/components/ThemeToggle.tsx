import { Moon, Sun, Monitor } from "lucide-react"

import { useTheme, type ThemePreference } from "@/shared/context/ThemeContext"
import { Button } from "@/shared/components/ui/button"

const CYCLE: ThemePreference[] = ["system", "light", "dark"]

const ICONS: Record<ThemePreference, typeof Sun> = {
  system: Monitor,
  light: Sun,
  dark: Moon,
}

const LABELS: Record<ThemePreference, string> = {
  system: "Matching your system theme",
  light: "Light theme",
  dark: "Dark theme",
}

function ThemeToggle() {
  const { theme, setTheme } = useTheme()
  const Icon = ICONS[theme]

  function cycle() {
    const nextIndex = (CYCLE.indexOf(theme) + 1) % CYCLE.length
    setTheme(CYCLE[nextIndex])
  }

  return (
    <Button
      type="button"
      variant="ghost"
      size="icon-xs"
      onClick={cycle}
      title={`${LABELS[theme]} — click to change`}
      aria-label={`Theme: ${LABELS[theme]}. Click to change.`}
    >
      <Icon className="size-3.5" />
    </Button>
  )
}

export default ThemeToggle
