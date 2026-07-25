import type { ReactNode } from "react"
import { Navigate } from "react-router-dom"

import { useAuth } from "@/context/AuthContext"

function AdminRoute({ children }: { children: ReactNode }) {
  const { user, isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-paper">
        <p className="text-sm text-muted-foreground">Loading...</p>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />
  }

  if (user?.role !== "admin" && user?.role !== "superadmin") {
    return <Navigate to="/app" replace />
  }

  return <>{children}</>
}

export default AdminRoute