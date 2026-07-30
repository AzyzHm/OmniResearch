import { useState } from "react"
import { Link, Outlet, useNavigate } from "react-router-dom"
import { LogOut, Settings } from "lucide-react"

import { logout } from "@/features/auth/api"
import { useAuth } from "@/features/auth/context/AuthContext"
import { Button } from "@/shared/components/ui/button"
import ThemeToggle from "@/shared/components/ThemeToggle"
import appLogo from "@/assets/app-logo.svg"

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
      // Even if the request fails, clear local state and send the user
      // back to the landing page rather than leaving them stuck.
    } finally {
      clearUser()
      navigate("/")
    }
  }

  return (
    <div className="min-h-screen bg-paper">
      <header className="sticky top-0 z-40 flex h-14 items-center justify-between gap-2 border-b border-border bg-paper/90 px-3 backdrop-blur-md sm:px-6">
        <div className="flex min-w-0 items-center gap-2 font-display text-base font-medium text-ink">
          <img src={appLogo} alt="" className="size-5 shrink-0" />
          <span className="truncate">OmniResearch</span>
        </div>

        <div className="flex shrink-0 items-center gap-2 sm:gap-3">
          {isAdmin && (
            <Link
              to="/admin"
              className="admin-glow inline-flex items-center gap-1.5 text-sm font-medium text-teal transition-opacity hover:opacity-80"
            >
              <Settings className="size-3.5" />
              <span>AdminSpace</span>
            </Link>
          )}
          <ThemeToggle />
          {user && (
            <span className="hidden font-mono text-xs text-muted-foreground md:inline">
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
            <span className="hidden sm:inline">
              {loggingOut ? "Logging out..." : "Log out"}
            </span>
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