import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, it, expect, vi } from "vitest"

import Workspace from "@/features/workspace/pages/Workspace"

vi.mock("@/features/auth/context/AuthContext", () => ({
  useAuth: vi.fn(),
}))

vi.mock("@/shared/components/ThemeToggle", () => ({
  default: () => <button data-testid="theme-toggle">Theme</button>,
}))

import { useAuth } from "@/features/auth/context/AuthContext"

function renderWorkspace(role: string | undefined) {
  vi.mocked(useAuth).mockReturnValue({
    user: role ? { user_id: "u1", username: "Azyz", role } : null,
    isLoading: false,
    isAuthenticated: !!role,
    refetchUser: vi.fn(),
    clearUser: vi.fn(),
  } as any)

  return render(
    <MemoryRouter>
      <Workspace />
    </MemoryRouter>
  )
}

describe("Workspace header — AdminSpace link", () => {
  it("shows 'AdminSpace' (not the old 'Admin' label) for admin users, always visible (no hidden-on-mobile class)", () => {
    renderWorkspace("admin")

    const link = screen.getByRole("link", { name: /AdminSpace/ })
    expect(link).toHaveAttribute("href", "/admin")

    const label = screen.getByText("AdminSpace")
    expect(label.className).not.toContain("hidden")
  })

  it("shows for superadmin too", () => {
    renderWorkspace("superadmin")
    expect(screen.getByRole("link", { name: /AdminSpace/ })).toBeInTheDocument()
  })

  it("does not show for a regular user", () => {
    renderWorkspace("user")
    expect(screen.queryByText("AdminSpace")).not.toBeInTheDocument()
  })

  it("renders before the theme toggle in the header (left of it)", () => {
    renderWorkspace("admin")

    const header = screen.getByRole("banner")
    const adminLink = screen.getByRole("link", { name: /AdminSpace/ })
    const themeToggle = screen.getByTestId("theme-toggle")

    const position = adminLink.compareDocumentPosition(themeToggle)
    // DOCUMENT_POSITION_FOLLOWING (4) means themeToggle comes after adminLink
    expect(position & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy()
    expect(header).toContainElement(adminLink)
  })
})