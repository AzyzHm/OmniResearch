import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, it, expect } from "vitest"

import PasswordInput from "@/shared/components/PasswordInput"

describe("PasswordInput", () => {
  it("starts masked (type=password) with a 'Show password' toggle", () => {
    render(<PasswordInput id="pw" value="" onChange={() => {}} />)

    const input = document.getElementById("pw") as HTMLInputElement
    expect(input.type).toBe("password")
    expect(screen.getByRole("button", { name: "Show password" })).toBeInTheDocument()
  })

  it("reveals the password as plain text when the eye icon is clicked, and re-masks on a second click", async () => {
    const user = userEvent.setup()
    render(<PasswordInput id="pw" value="hunter2" onChange={() => {}} />)

    const input = document.getElementById("pw") as HTMLInputElement
    const toggle = screen.getByRole("button", { name: "Show password" })

    await user.click(toggle)
    expect(input.type).toBe("text")
    expect(screen.getByRole("button", { name: "Hide password" })).toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: "Hide password" }))
    expect(input.type).toBe("password")
  })

  it("does not submit the form when the toggle is clicked (type=button)", () => {
    render(<PasswordInput id="pw" value="" onChange={() => {}} />)
    const toggle = screen.getByRole("button", { name: "Show password" })
    expect(toggle).toHaveAttribute("type", "button")
  })
})
