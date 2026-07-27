import { NavLink, Outlet, useNavigate } from "react-router-dom"
import { LogOut } from "lucide-react"

import { logout } from "@/features/auth/api"
import { useAuth } from "@/features/auth/context/AuthContext"
import { cn } from "@/shared/lib/utils"
import appLogo from "@/assets/app-logo.svg"

const TABS = [
  { to: "/admin", label: "Overview", end: true },
  { to: "/admin/users", label: "User Management", end: false },
  { to: "/admin/logs", label: "Login Logs", end: false },
  { to: "/admin/usage", label: "Usage", end: false },
]

function AdminLayout() {
  const navigate = useNavigate()
  const { user, clearUser } = useAuth()

  async function handleLogout() {
    try {
      await logout()
    } catch {
      // Fall through and clear local state regardless.
    } finally {
      clearUser()
      navigate("/")
    }
  }

  return (
    <div className="min-h-screen bg-paper">
      <header className="border-b border-border bg-surface px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <img src={appLogo} alt="" className="size-6" />
            <h1 className="font-display text-xl font-medium text-ink">
              Admin Dashboard
            </h1>
          </div>
          <div className="flex items-center gap-3">
            {user && (
              <span className="text-sm text-muted-foreground">
                Signed in as <span className="font-medium text-ink">{user.username}</span>
              </span>
            )}
            <button
              type="button"
              onClick={handleLogout}
              className="inline-flex items-center gap-1.5 text-sm text-muted-foreground transition-colors hover:text-ink"
            >
              <LogOut className="size-3.5" />
              Sign out
            </button>
          </div>
        </div>

        <nav className="mt-4 flex gap-1">
          {TABS.map((tab) => (
            <NavLink
              key={tab.to}
              to={tab.to}
              end={tab.end}
              className={({ isActive }) =>
                cn(
                  "rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-teal/10 text-teal"
                    : "text-muted-foreground hover:bg-muted hover:text-ink"
                )
              }
            >
              {tab.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-5xl px-6 py-6">
        <Outlet />
      </main>
    </div>
  )
}

export default AdminLayout