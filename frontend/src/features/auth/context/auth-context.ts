import { createContext } from "react"
import type { QueryKey } from "@tanstack/react-query"
import type { CurrentUser } from "@/features/auth/api"

export const AUTH_QUERY_KEY: QueryKey = ["currentUser"]

export interface AuthContextValue {
  user: CurrentUser | null
  isLoading: boolean
  isAuthenticated: boolean
  refetchUser: () => Promise<unknown>
  clearUser: () => void
}

export const AuthContext = createContext<AuthContextValue | undefined>(undefined)
