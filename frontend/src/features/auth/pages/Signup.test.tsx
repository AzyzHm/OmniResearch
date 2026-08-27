import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { describe, it, expect } from "vitest"

import Signup from "@/features/auth/pages/Signup"

describe("Signup — password visibility toggles", () => {
  it("password and confirm-password fields each start masked and toggle independently", async () => {
    const user = userEvent.setup()
    render(
      <MemoryRouter>
        <Signup />
      </MemoryRouter>,
    )

    const password = document.getElementById("password") as HTMLInputElement
    const confirmPassword = document.getElementById("confirmPassword") as HTMLInputElement
    expect(password.type).toBe("password")
    expect(confirmPassword.type).toBe("password")

    const toggles = screen.getAllByRole("button", { name: "Show password" })
    expect(toggles).toHaveLength(2)

    await user.click(toggles[0])
    expect(password.type).toBe("text")
    expect(confirmPassword.type).toBe("password")
  })
})
