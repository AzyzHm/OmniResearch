import { useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import {
  approveUser,
  changeUserRole,
  deleteUser,
  listUsers,
  updateTokenLimit,
} from "@/features/admin/api"
import { ApiError } from "@/shared/lib/apiClient"
import { useAuth } from "@/features/auth/context/AuthContext"
import { Button } from "@/shared/components/ui/button"
import UserRow from "@/features/admin/components/UserRow"

const QUERY_KEY_BASE = ["admin-users"]

function UsersTab() {
  const { user: viewer } = useAuth()
  const queryClient = useQueryClient()
  const [pendingOnly, setPendingOnly] = useState(false)
  const [actionError, setActionError] = useState<string | null>(null)
  const queryKey = [...QUERY_KEY_BASE, pendingOnly]

  const { data, isLoading, isError, refetch } = useQuery({
    queryKey,
    queryFn: () => listUsers(pendingOnly),
  })

  function invalidateAll() {
    setActionError(null)
    queryClient.invalidateQueries({ queryKey: QUERY_KEY_BASE })
  }

  function onMutationError(err: unknown) {
    setActionError(err instanceof ApiError ? err.message : "Something went wrong.")
  }

  const approveMutation = useMutation({
    mutationFn: approveUser,
    onSuccess: invalidateAll,
    onError: onMutationError,
  })
  const roleMutation = useMutation({
    mutationFn: ({ id, role }: { id: string; role: "admin" | "user" }) => changeUserRole(id, role),
    onSuccess: invalidateAll,
    onError: onMutationError,
  })
  const deleteMutation = useMutation({
    mutationFn: deleteUser,
    onSuccess: invalidateAll,
    onError: onMutationError,
  })
  const limitMutation = useMutation({
    mutationFn: ({ id, limit }: { id: string; limit: number }) => updateTokenLimit(id, limit),
    onSuccess: invalidateAll,
    onError: onMutationError,
  })

  const isMutating =
    approveMutation.isPending ||
    roleMutation.isPending ||
    deleteMutation.isPending ||
    limitMutation.isPending

  const isSuperadminViewer = viewer?.role === "superadmin"

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h2 className="font-display text-base font-medium text-ink">Registered Users</h2>
        <div className="flex items-center gap-3">
          <label className="flex items-center gap-1.5 text-sm text-muted-foreground">
            <input
              type="checkbox"
              checked={pendingOnly}
              onChange={(e) => setPendingOnly(e.target.checked)}
              className="size-4 rounded border-input accent-teal"
            />
            Show pending accounts only
          </label>
          <Button type="button" variant="outline" size="sm" onClick={() => refetch()}>
            Refresh
          </Button>
        </div>
      </div>

      {actionError && <p className="mb-3 text-sm text-destructive">{actionError}</p>}

      {isLoading && <p className="text-sm text-muted-foreground">Loading...</p>}
      {isError && <p className="text-sm text-destructive">Failed to load users.</p>}

      {!isLoading && !isError && data && (
        <>
          <p className="mb-2 text-sm text-muted-foreground">{data.total} user(s)</p>
          {data.users.length === 0 ? (
            <p className="text-sm text-muted-foreground">No users found.</p>
          ) : (
            <div className="rounded-xl border border-border px-4">
              {data.users.map((u) => (
                <UserRow
                  key={u.id}
                  user={u}
                  isSelf={u.id === viewer?.user_id}
                  isSuperadminViewer={isSuperadminViewer}
                  isMutating={isMutating}
                  onApprove={() => approveMutation.mutate(u.id)}
                  onChangeRole={(role) => roleMutation.mutate({ id: u.id, role })}
                  onDelete={() => deleteMutation.mutate(u.id)}
                  onUpdateTokenLimit={(limit) => limitMutation.mutate({ id: u.id, limit })}
                />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}

export default UsersTab
