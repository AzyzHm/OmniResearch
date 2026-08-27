import { render, screen, act } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, it, expect, beforeEach, vi } from "vitest"

import { ThemeProvider } from "@/shared/context/ThemeContext"
import { useTheme } from "@/shared/context/useTheme"

const STORAGE_KEY = "omniresearch-theme"

function installMatchMediaMock(initialMatches: boolean) {
  let matches = initialMatches
  const listeners: Array<() => void> = []

  const mql = {
    get matches() {
      return matches
    },
    media: "(prefers-color-scheme: dark)",
    addEventListener: (_: string, cb: () => void) => listeners.push(cb),
    removeEventListener: (_: string, cb: () => void) => {
      const i = listeners.indexOf(cb)
      if (i !== -1) listeners.splice(i, 1)
    },
  }

  window.matchMedia = vi.fn().mockReturnValue(mql) as unknown as typeof window.matchMedia

  return {
    setMatches(next: boolean) {
      matches = next
      listeners.forEach((cb) => cb())
    },
  }
}

function ThemeProbe() {
  const { theme, resolvedTheme, setTheme } = useTheme()
  return (
    <div>
      <span data-testid="theme">{theme}</span>
      <span data-testid="resolved">{resolvedTheme}</span>
      <button onClick={() => setTheme("light")}>light</button>
      <button onClick={() => setTheme("dark")}>dark</button>
      <button onClick={() => setTheme("system")}>system</button>
    </div>
  )
}

describe("ThemeContext", () => {
  beforeEach(() => {
    window.localStorage.clear()
    document.documentElement.classList.remove("dark")
  })

  it("defaults to system preference when nothing is stored", () => {
    installMatchMediaMock(true)
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>,
    )
    expect(screen.getByTestId("theme")).toHaveTextContent("system")
    expect(screen.getByTestId("resolved")).toHaveTextContent("dark")
    expect(document.documentElement.classList.contains("dark")).toBe(true)
  })

  it("respects a stored explicit preference over the OS setting", () => {
    installMatchMediaMock(true)
    window.localStorage.setItem(STORAGE_KEY, "light")
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>,
    )
    expect(screen.getByTestId("resolved")).toHaveTextContent("light")
    expect(document.documentElement.classList.contains("dark")).toBe(false)
  })

  it("setTheme persists to localStorage and updates the DOM class", async () => {
    installMatchMediaMock(false)
    const user = userEvent.setup()
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>,
    )

    await user.click(screen.getByRole("button", { name: "dark" }))

    expect(window.localStorage.getItem(STORAGE_KEY)).toBe("dark")
    expect(screen.getByTestId("resolved")).toHaveTextContent("dark")
    expect(document.documentElement.classList.contains("dark")).toBe(true)
  })

  it("live-updates while in system mode when the OS preference changes", async () => {
    const mock = installMatchMediaMock(false)
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>,
    )
    expect(screen.getByTestId("resolved")).toHaveTextContent("light")

    act(() => {
      mock.setMatches(true)
    })

    expect(screen.getByTestId("resolved")).toHaveTextContent("dark")
    expect(document.documentElement.classList.contains("dark")).toBe(true)
  })

  it("does not react to OS changes once an explicit preference is set", async () => {
    const mock = installMatchMediaMock(false)
    const user = userEvent.setup()
    render(
      <ThemeProvider>
        <ThemeProbe />
      </ThemeProvider>,
    )

    await user.click(screen.getByRole("button", { name: "light" }))
    expect(screen.getByTestId("resolved")).toHaveTextContent("light")

    act(() => {
      mock.setMatches(true)
    })
    expect(screen.getByTestId("resolved")).toHaveTextContent("light")
  })
})
