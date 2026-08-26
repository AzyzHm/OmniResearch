import { useEffect, useState, type ReactNode } from "react"
import {
  ThemeContext,
  type ThemePreference,
  type ResolvedTheme,
} from "@/shared/context/theme-context"

const STORAGE_KEY = "omniresearch-theme"

function systemPrefersDark(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
}

function applyTheme(resolved: ResolvedTheme) {
  document.documentElement.classList.toggle("dark", resolved === "dark")
}

function readStoredPreference(): ThemePreference {
  const stored = window.localStorage.getItem(STORAGE_KEY)
  return stored === "light" || stored === "dark" || stored === "system" ? stored : "system"
}

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemePreference>(readStoredPreference)
  const [systemIsDark, setSystemIsDark] = useState<boolean>(systemPrefersDark)

  const resolvedTheme: ResolvedTheme =
    theme === "system" ? (systemIsDark ? "dark" : "light") : theme

  function setTheme(next: ThemePreference) {
    setThemeState(next)
    window.localStorage.setItem(STORAGE_KEY, next)
  }

  useEffect(() => {
    applyTheme(resolvedTheme)
  }, [resolvedTheme])

  useEffect(() => {
    const media = window.matchMedia("(prefers-color-scheme: dark)")
    function handleChange() {
      setSystemIsDark(media.matches)
    }
    media.addEventListener("change", handleChange)
    return () => media.removeEventListener("change", handleChange)
  }, [])

  return (
    <ThemeContext.Provider value={{ theme, resolvedTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  )
}
