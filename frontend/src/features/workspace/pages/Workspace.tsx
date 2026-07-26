import { useState } from "react"
import { Link, Outlet, useNavigate } from "react-router-dom"
import { LogOut, Settings, Sparkles } from "lucide-react"

import { logout } from "@/features/auth/api"
import { useAuth } from "@/features/auth/context/AuthContext"
import { Button } from "@/shared/components/ui/button"

function Workspace() {
  const navigate = useNavigate()
  const { user, clearUser } = useAuth()
  const [loggingOut, setLoggingOut] = useState(false)
  const isAdmin = user?.role === "admin" || user?.role === "superadmin"

  async function handleLogout() {
    setLoggingOut(true)
    try {
      await logout()
    } catch {
    } finally {
      clearUser()
      navigate("/")
    }
  }

  return (
    <div className="min-h-screen bg-paper">
      <header className="sticky top-0 z-40 flex h-14 items-center justify-between border-b border-border bg-paper/90 px-6 backdrop-blur-md">
        <div className="flex items-center gap-2 font-display text-base font-medium text-ink">
          <Sparkles className="size-4 text-teal" />
          OmniResearch
        </div>

        <div className="flex items-center gap-3">
          {isAdmin && (
            <Link
              to="/admin"
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-ink"
            >
              <Settings className="size-3.5" />
              Admin
            </Link>
          )}
          {user && (
            <span className="font-mono text-xs text-muted-foreground">
              {user.username}
            </span>
          )}
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={handleLogout}
            disabled={loggingOut}
          >
            <LogOut className="size-3.5" data-icon="inline-start" />
            {loggingOut ? "Logging out..." : "Log out"}
          </Button>
        </div>
      </header>

      <main>
        <Outlet />
      </main>
    </div>
  )
}

export default Workspace