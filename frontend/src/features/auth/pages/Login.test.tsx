import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { describe, it, expect, vi } from "vitest"

import Login from "@/features/auth/pages/Login"

vi.mock("@/features/auth/context/AuthContext", () => ({
  useAuth: () => ({ refetchUser: vi.fn() }),
}))

function renderLogin() {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  })
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <Login />
      </MemoryRouter>
    </QueryClientProvider>,
  )
}

describe("Login — password visibility toggle", () => {
  it("password field starts masked and can be revealed via the eye icon", async () => {
    const user = userEvent.setup()
    renderLogin()

    const passwordInput = document.getElementById("password") as HTMLInputElement
    expect(passwordInput.type).toBe("password")

    await user.click(screen.getByRole("button", { name: "Show password" }))
    expect(passwordInput.type).toBe("text")
  })
})
