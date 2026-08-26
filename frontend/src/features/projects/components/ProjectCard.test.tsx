import { render, screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { MemoryRouter } from "react-router-dom"
import { describe, it, expect, vi } from "vitest"

import ProjectCard from "@/features/projects/components/ProjectCard"
import type { Project } from "@/features/projects/api"

const project: Project = {
  id: "p1",
  user_id: "u1",
  name: "Test Project",
  created_at: "2026-01-01T00:00:00Z",
  updated_at: "2026-01-01T00:00:00Z",
}

function renderCard(overrides: Partial<Parameters<typeof ProjectCard>[0]> = {}) {
  const onRename = vi.fn()
  const onDelete = vi.fn()
  render(
    <MemoryRouter>
      <ProjectCard
        project={project}
        onRename={onRename}
        onDelete={onDelete}
        isDeleting={false}
        {...overrides}
      />
    </MemoryRouter>,
  )
  return { onRename, onDelete }
}

describe("ProjectCard mobile visibility", () => {
  it("does not hide rename/delete (or their confirm/cancel state) behind hover-only opacity", () => {
    renderCard()

    const renameButton = screen.getByRole("button", { name: "Rename project" })
    const wrapper = renameButton.parentElement!
    const classes = wrapper.className.split(/\s+/)

    expect(classes).toContain("opacity-100")
    expect(classes).toContain("md:opacity-0")
    expect(classes).toContain("md:group-hover:opacity-100")
    expect(classes).not.toContain("opacity-0")
  })
})

describe("ProjectCard interactions", () => {
  it("asks for confirmation before deleting, and does not navigate when clicking the action area", async () => {
    const user = userEvent.setup()
    const { onDelete } = renderCard()

    await user.click(screen.getByRole("button", { name: "Delete project" }))
    const confirmButton = await screen.findByRole("button", { name: "Confirm" })
    await user.click(confirmButton)

    expect(onDelete).toHaveBeenCalledExactlyOnceWith(project)
  })

  it("calls onRename with the project when the rename button is clicked", async () => {
    const user = userEvent.setup()
    const { onRename } = renderCard()

    await user.click(screen.getByRole("button", { name: "Rename project" }))

    expect(onRename).toHaveBeenCalledExactlyOnceWith(project)
  })
})
