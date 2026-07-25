import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AuthProvider } from "@/context/AuthContext"
import ProtectedRoute from "@/components/ProtectedRoute"
import AdminRoute from "@/components/AdminRoute"
import Landing from "@/pages/Landing"
import Login from "@/pages/Login"
import Signup from "@/pages/Signup"
import Workspace from "@/pages/Workspace"
import ProjectsList from "@/pages/ProjectsList"
import ProjectDetail from "@/pages/ProjectDetail"
import Terms from "@/pages/Terms"
import Privacy from "@/pages/Privacy"
import Cookies from "@/pages/Cookies"
import AdminLayout from "@/components/admin/AdminLayout"
import OverviewTab from "@/components/admin/OverviewTab"
import UsersTab from "@/components/admin/UsersTab"
import LogsTab from "@/components/admin/LogsTab"
import UsageTab from "@/components/admin/UsageTab"

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
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
      </AuthProvider>
    </BrowserRouter>
  )
}

export default App