import { lazy, Suspense } from "react"
import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AuthProvider } from "@/features/auth/context/AuthContext"
import ProtectedRoute from "@/features/auth/routes/ProtectedRoute"
import AdminRoute from "@/features/auth/routes/AdminRoute"
import Landing from "@/features/landing/pages/Landing"

const Login = lazy(() => import("@/features/auth/pages/Login"))
const Signup = lazy(() => import("@/features/auth/pages/Signup"))
const Workspace = lazy(() => import("@/features/workspace/pages/Workspace"))
const ProjectsList = lazy(() => import("@/features/projects/pages/ProjectsList"))
const ProjectDetail = lazy(() => import("@/features/workspace/pages/ProjectDetail"))
const Terms = lazy(() => import("@/features/legal/pages/Terms"))
const Privacy = lazy(() => import("@/features/legal/pages/Privacy"))
const Cookies = lazy(() => import("@/features/legal/pages/Cookies"))
const AdminLayout = lazy(() => import("@/features/admin/pages/AdminLayout"))
const OverviewTab = lazy(() => import("@/features/admin/pages/OverviewTab"))
const UsersTab = lazy(() => import("@/features/admin/pages/UsersTab"))
const LogsTab = lazy(() => import("@/features/admin/pages/LogsTab"))
const UsageTab = lazy(() => import("@/features/admin/pages/UsageTab"))

function RouteFallback() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-paper">
      <p className="text-sm text-muted-foreground">Loading...</p>
    </div>
  )
}

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Suspense fallback={<RouteFallback />}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/signup" element={<Signup />} />
            <Route
              path="/app"
              element={
                <ProtectedRoute>
                  <Workspace />
                </ProtectedRoute>
              }
            >
              <Route index element={<ProjectsList />} />
              <Route path="projects/:projectId" element={<ProjectDetail />} />
            </Route>
            <Route
              path="/admin"
              element={
                <AdminRoute>
                  <AdminLayout />
                </AdminRoute>
              }
            >
              <Route index element={<OverviewTab />} />
              <Route path="users" element={<UsersTab />} />
              <Route path="logs" element={<LogsTab />} />
              <Route path="usage" element={<UsageTab />} />
            </Route>
            <Route path="/terms" element={<Terms />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/cookies" element={<Cookies />} />
          </Routes>
        </Suspense>
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App
