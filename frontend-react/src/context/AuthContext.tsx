import { createContext, useContext, type ReactNode } from "react"
import { useQuery, useQueryClient, type QueryKey } from "@tanstack/react-query"
import { getCurrentUser, type CurrentUser } from "@/api/auth"
import { ApiError } from "@/lib/apiClient"

export const AUTH_QUERY_KEY: QueryKey = ["currentUser"]

interface AuthContextValue {
  user: CurrentUser | null
  isLoading: boolean
  isAuthenticated: boolean
  refetchUser: () => Promise<unknown>
  clearUser: () => void
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const queryClient = useQueryClient()

  const { data, isLoading, refetch } = useQuery({
    queryKey: AUTH_QUERY_KEY,
    queryFn: async (): Promise<CurrentUser | null> => {
      try {
        return await getCurrentUser()
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          return null
        }
        throw err
      }
    },
    retry: false,
    staleTime: 5 * 60 * 1000,
    refetchOnWindowFocus: false,
  })

  const value: AuthContextValue = {
    user: data ?? null,
    isLoading,
    isAuthenticated: !!data,
    refetchUser: refetch,
    clearUser: () => queryClient.setQueryData(AUTH_QUERY_KEY, null),
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return ctx
}