import { useState } from "react"

import type { AdminUser } from "@/features/admin/api"
import { Button } from "@/shared/components/ui/button"
import { Input } from "@/shared/components/ui/input"
import Badge from "@/features/admin/components/Badge"

interface UserRowProps {
  user: AdminUser
  isSelf: boolean
  isSuperadminViewer: boolean
  onApprove: () => void
  onChangeRole: (newRole: "admin" | "user") => void
  onDelete: () => void
  onUpdateTokenLimit: (limit: number) => void
  isMutating: boolean
}

function UserRow({
  user,
  isSelf,
  isSuperadminViewer,
  onApprove,
  onChangeRole,
  onDelete,
  onUpdateTokenLimit,
  isMutating,
}: UserRowProps) {
  const [confirmingDelete, setConfirmingDelete] = useState(false)
  const [limitValue, setLimitValue] = useState(String(user.daily_token_limit))

  const canChangeRole = isSuperadminViewer && user.role !== "superadmin"
  const limitDirty = limitValue !== String(user.daily_token_limit)

  return (
    <div className="border-b border-border py-3 last:border-0">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="font-medium text-ink">{user.username}</span>
            <Badge color={user.role === "superadmin" ? "amber" : "teal"}>
              {user.role.toUpperCase()}
            </Badge>
            {isSelf && <Badge color="muted">YOU</Badge>}
          </div>
          <p className="mt-0.5 text-xs text-muted-foreground">
            Joined{" "}
            {new Date(user.created_at).toLocaleDateString(undefined, {
              day: "2-digit",
              month: "short",
              year: "numeric",
            })}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Badge color={user.is_approved ? "teal" : "amber"}>
            {user.is_approved ? "✓ Approved" : "⏳ Pending"}
          </Badge>

          {!isSelf &&
            (confirmingDelete ? (
              <div className="flex items-center gap-1">
                <Button
                  type="button"
                  size="xs"
                  variant="destructive"
                  disabled={isMutating}
                  onClick={onDelete}
                >
                  Confirm
                </Button>
                <Button
                  type="button"
                  size="xs"
                  variant="ghost"
                  disabled={isMutating}
                  onClick={() => setConfirmingDelete(false)}
                >
                  Cancel
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-1">
                {!user.is_approved && (
                  <Button type="button" size="xs" disabled={isMutating} onClick={onApprove}>
                    Approve
                  </Button>
                )}
                {canChangeRole && (
                  <Button
                    type="button"
                    size="xs"
                    variant="outline"
                    disabled={isMutating}
                    onClick={() => onChangeRole(user.role === "user" ? "admin" : "user")}
                  >
                    {user.role === "user" ? "Promote" : "Demote"}
                  </Button>
                )}
                <Button
                  type="button"
                  size="xs"
                  variant="outline"
                  disabled={isMutating}
                  onClick={() => setConfirmingDelete(true)}
                >
                  Delete
                </Button>
              </div>
            ))}
        </div>
      </div>

      {user.role === "user" && (
        <div className="mt-2 flex items-center gap-2">
          <span className="text-xs text-muted-foreground">Daily token limit</span>
          <Input
            type="number"
            min={0}
            max={100_000_000}
            step={5000}
            value={limitValue}
            onChange={(e) => setLimitValue(e.target.value)}
            className="h-7 w-32 text-xs"
          />
          <Button
            type="button"
            size="xs"
            variant="outline"
            disabled={!limitDirty || isMutating}
            onClick={() => onUpdateTokenLimit(Number(limitValue))}
          >
            Save
          </Button>
        </div>
      )}
    </div>
  )
}

export default UserRow
