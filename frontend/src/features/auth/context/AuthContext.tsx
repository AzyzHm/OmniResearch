import { type ReactNode } from "react"
import { useQuery, useQueryClient } from "@tanstack/react-query"
import { getCurrentUser, type CurrentUser } from "@/features/auth/api"
import { ApiError } from "@/shared/lib/apiClient"
import {
  AUTH_QUERY_KEY,
  AuthContext,
  type AuthContextValue,
} from "@/features/auth/context/auth-context"

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
