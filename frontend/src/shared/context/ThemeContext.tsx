import {
  createContext,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react"

export type ThemePreference = "light" | "dark" | "system"
type ResolvedTheme = "light" | "dark"

const STORAGE_KEY = "omniresearch-theme"

function systemPrefersDark(): boolean {
  return window.matchMedia("(prefers-color-scheme: dark)").matches
}

function applyTheme(resolved: ResolvedTheme) {
  document.documentElement.classList.toggle("dark", resolved === "dark")
}

function readStoredPreference(): ThemePreference {
  const stored = window.localStorage.getItem(STORAGE_KEY)
  return stored === "light" || stored === "dark" || stored === "system"
    ? stored
    : "system"
}

interface ThemeContextValue {
  /** The user's stored preference — light, dark, or "follow the OS". */
  theme: ThemePreference
  /** What's actually applied right now (system resolves to light or dark). */
  resolvedTheme: ResolvedTheme
  setTheme: (theme: ThemePreference) => void
}

const ThemeContext = createContext<ThemeContextValue | undefined>(undefined)

export function ThemeProvider({ children }: { children: ReactNode }) {
  const [theme, setThemeState] = useState<ThemePreference>(readStoredPreference)
  // Tracks the live OS preference, updated only via the matchMedia
  // listener below. resolvedTheme itself is derived below, not stored —
  // storing it separately and syncing it in an effect would just be
  // redundant state-mirroring.
  const [systemIsDark, setSystemIsDark] = useState<boolean>(systemPrefersDark)

  const resolvedTheme: ResolvedTheme =
    theme === "system" ? (systemIsDark ? "dark" : "light") : theme

  function setTheme(next: ThemePreference) {
    setThemeState(next)
    window.localStorage.setItem(STORAGE_KEY, next)
  }

  // Sync the resolved theme to the DOM — a legitimate "update an external
  // system from React state" effect, not state-mirroring.
  useEffect(() => {
    applyTheme(resolvedTheme)
  }, [resolvedTheme])

  // Subscribe to OS-level preference changes so "system" mode stays live
  // without needing a page reload.
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

export function useTheme() {
  const ctx = useContext(ThemeContext)
  if (!ctx) {
    throw new Error("useTheme must be used within a ThemeProvider")
  }
  return ctx
}