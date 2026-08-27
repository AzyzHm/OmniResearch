import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, it, expect, vi } from "vitest"

import CollectionFormDialog from "@/features/collections/components/CollectionFormDialog"

describe("CollectionFormDialog", () => {
  it("has no source-type picker — collections no longer have a type", () => {
    render(
      <CollectionFormDialog
        open
        onOpenChange={() => {}}
        isSubmitting={false}
        error={null}
        onSubmit={() => {}}
      />,
    )

    expect(screen.queryByText("Documents")).not.toBeInTheDocument()
    expect(screen.queryByText("URLs")).not.toBeInTheDocument()
    expect(screen.queryByText("Source type")).not.toBeInTheDocument()
  })

  it("submits only the trimmed name", async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()

    render(
      <CollectionFormDialog
        open
        onOpenChange={() => {}}
        isSubmitting={false}
        error={null}
        onSubmit={onSubmit}
      />,
    )

    await user.type(screen.getByLabelText("Collection name"), "  Background Reading  ")
    await user.click(screen.getByRole("button", { name: "Create collection" }))

    expect(onSubmit).toHaveBeenCalledExactlyOnceWith("Background Reading")
  })

  it("disables submit until a name is entered", () => {
    render(
      <CollectionFormDialog
        open
        onOpenChange={() => {}}
        isSubmitting={false}
        error={null}
        onSubmit={() => {}}
      />,
    )

    expect(screen.getByRole("button", { name: "Create collection" })).toBeDisabled()
  })
})
