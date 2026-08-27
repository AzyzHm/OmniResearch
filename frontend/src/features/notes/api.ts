import { apiClient } from "@/shared/lib/apiClient"
import type { Source } from "@/features/chat/api"

export interface Note {
  id: string
  project_id: string
  name: string
  created_at: string
}

export interface NoteItem {
  id: string
  note_id: string
  message_id: string
  chat_id: string
  role: "user" | "assistant" | string
  content: string
  sources?: Source[] | null
  created_at: string
}

export function listNotes(projectId: string) {
  return apiClient.get<Note[]>(`/projects/${projectId}/notes`)
}

export function createNote(projectId: string, name: string) {
  return apiClient.post<Note>(`/projects/${projectId}/notes`, { name })
}

export function renameNote(noteId: string, name: string) {
  return apiClient.put<Note>(`/notes/${noteId}`, { name })
}

export function deleteNote(noteId: string) {
  return apiClient.delete<void>(`/notes/${noteId}`)
}

export function listNoteItems(noteId: string) {
  return apiClient.get<NoteItem[]>(`/notes/${noteId}/items`)
}

export function saveMessageToNote(noteId: string, messageId: string) {
  return apiClient.post<NoteItem>(`/notes/${noteId}/items`, { message_id: messageId })
}

export function removeNoteItem(noteId: string, itemId: string) {
  return apiClient.delete<void>(`/notes/${noteId}/items/${itemId}`)
}
