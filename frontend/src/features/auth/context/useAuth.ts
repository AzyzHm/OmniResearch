import { useContext } from "react"
import { AuthContext } from "@/features/auth/context/auth-context"

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return ctx
}
