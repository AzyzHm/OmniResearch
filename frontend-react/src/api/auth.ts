import { apiClient } from "@/lib/apiClient"

export interface RegisterPayload {
  username: string
  password: string
}

export interface LoginPayload {
  username: string
  password: string
}

export interface MessageResponse {
  message: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
  user_id: string
  username: string
  role: string
}

export function register(payload: RegisterPayload) {
  return apiClient.post<MessageResponse>("/auth/register", payload)
}

export function login(payload: LoginPayload) {
  return apiClient.post<TokenResponse>("/auth/login", payload)
}

export function logout() {
  return apiClient.post<MessageResponse>("/auth/logout")
}