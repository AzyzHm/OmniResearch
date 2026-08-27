import { apiClient } from "@/shared/lib/apiClient"

export interface Project {
  id: string
  user_id: string
  name: string
  created_at: string
  updated_at: string
}

export interface ProjectPayload {
  name: string
}

export function listProjects() {
  return apiClient.get<Project[]>("/projects")
}

export function createProject(payload: ProjectPayload) {
  return apiClient.post<Project>("/projects", payload)
}

export function renameProject(projectId: string, payload: ProjectPayload) {
  return apiClient.put<Project>(`/projects/${projectId}`, payload)
}

export function deleteProject(projectId: string) {
  return apiClient.delete<void>(`/projects/${projectId}`)
}
