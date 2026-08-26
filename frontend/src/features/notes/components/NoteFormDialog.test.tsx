import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, it, expect, vi } from "vitest"

import NoteFormDialog from "@/features/notes/components/NoteFormDialog"

describe("NoteFormDialog", () => {
  it("submits only the trimmed name", async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(
      <NoteFormDialog
        open
        onOpenChange={() => {}}
        isSubmitting={false}
        error={null}
        onSubmit={onSubmit}
      />,
    )

    await user.type(screen.getByLabelText("Note name"), "  Key Findings  ")
    await user.click(screen.getByRole("button", { name: "Create note" }))

    expect(onSubmit).toHaveBeenCalledExactlyOnceWith("Key Findings")
  })

  it("disables submit until a name is entered", () => {
    render(
      <NoteFormDialog
        open
        onOpenChange={() => {}}
        isSubmitting={false}
        error={null}
        onSubmit={() => {}}
      />,
    )

    expect(screen.getByRole("button", { name: "Create note" })).toBeDisabled()
  })
})
