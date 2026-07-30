import { render, screen } from "@testing-library/react"
import { MemoryRouter } from "react-router-dom"
import { describe, it, expect, vi } from "vitest"

import AdminLayout from "@/features/admin/pages/AdminLayout"

vi.mock("@/features/auth/context/AuthContext", () => ({
  useAuth: vi.fn(() => ({
    user: { user_id: "u1", username: "Azyz", role: "admin" },
    isLoading: false,
    isAuthenticated: true,
    refetchUser: vi.fn(),
    clearUser: vi.fn(),
  })),
}))

vi.mock("@/shared/components/ThemeToggle", () => ({
  default: () => <button data-testid="theme-toggle">Theme</button>,
}))

describe("AdminLayout — leaving admin without logging out", () => {
  it("has a link back to the projects page that doesn't require signing out", () => {
    render(
      <MemoryRouter>
        <AdminLayout />
      </MemoryRouter>
    )

    const backLink = screen.getByRole("link", { name: /Back to projects/ })
    expect(backLink).toHaveAttribute("href", "/app")
  })
})