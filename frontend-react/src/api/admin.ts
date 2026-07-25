import { apiClient } from "@/lib/apiClient"

export interface AdminUser {
  id: string
  username: string
  role: string
  is_approved: boolean
  created_at: string
  daily_token_limit: number
}

export interface AdminStats {
  total_users: number
  pending_users: number
  total_logins: number
  recent_logins: { username: string; login_time: string; ip_address: string | null }[]
  admin_users?: number
}

export interface LoginLog {
  id: string
  user_id: string
  username: string
  login_time: string
  ip_address: string | null
}

export interface LlmUsageRow {
  user_id: string
  username: string
  gemini_calls: number
  gemini_tokens: number
  mistral_calls: number
  mistral_tokens: number
  total_calls: number
  total_tokens: number
}

export interface SearchUsageRow {
  user_id: string
  username: string
  tavily_calls: number
  tavily_credits: number
  exa_calls: number
  exa_credits: number
  total_calls: number
  total_credits: number
}

export function getStats() {
  return apiClient.get<AdminStats>("/admin/stats")
}

export function listUsers(pendingOnly = false) {
  return apiClient
    .get<{ users: AdminUser[]; total: number }>(
      `/admin/users${pendingOnly ? "?pending_only=true" : ""}`
    )
}

export function approveUser(userId: string) {
  return apiClient.put<{ message: string }>(`/admin/users/${userId}/approve`)
}

export function changeUserRole(userId: string, newRole: "admin" | "user") {
  return apiClient.put<{ message: string }>(
    `/admin/users/${userId}/role?new_role=${newRole}`
  )
}

export function deleteUser(userId: string) {
  return apiClient.delete<{ message: string }>(`/admin/users/${userId}`)
}

export function updateTokenLimit(userId: string, dailyTokenLimit: number) {
  return apiClient.put<{ message: string }>(`/admin/users/${userId}/token-limit`, {
    daily_token_limit: dailyTokenLimit,
  })
}

export function getLogs(limit = 100, offset = 0, username?: string) {
  const params = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  if (username) params.set("username", username)
  return apiClient.get<{ logs: LoginLog[]; total: number }>(
    `/admin/logs?${params.toString()}`
  )
}

export function getLlmUsage() {
  return apiClient.get<{ users: LlmUsageRow[] }>("/admin/usage/llm")
}

export function getSearchUsage() {
  return apiClient.get<{ users: SearchUsageRow[] }>("/admin/usage/search")
}