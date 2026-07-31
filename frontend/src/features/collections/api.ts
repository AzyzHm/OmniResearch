import { API_BASE_URL, apiClient, ApiError } from "@/shared/lib/apiClient"

export interface Collection {
  id: string
  project_id: string
  name: string
  created_at: string
}

export interface CollectionItem {
  id: string
  collection_id: string
  name: string
  source_type: string
  is_active: boolean
  status: "processing" | "ready" | "error" | string
  chunk_count: number
  page_count: number | null
  word_count: number | null
  storage_path: string | null
  error_message: string | null
  created_at: string
}

export function listCollections(projectId: string) {
  return apiClient.get<Collection[]>(`/projects/${projectId}/collections`)
}

export function createCollection(projectId: string, payload: { name: string }) {
  return apiClient.post<Collection>(`/projects/${projectId}/collections`, payload)
}

export function deleteCollection(collectionId: string) {
  return apiClient.delete<void>(`/collections/${collectionId}`)
}

export function listCollectionItems(collectionId: string) {
  return apiClient.get<CollectionItem[]>(`/collections/${collectionId}/items`)
}

export function uploadCollectionFiles(collectionId: string, files: File[]) {
  const formData = new FormData()
  files.forEach((file) => formData.append("files", file))
  return apiClient.upload<CollectionItem[]>(
    `/collections/${collectionId}/items`,
    formData
  )
}

export function addCollectionUrl(collectionId: string, url: string) {
  return apiClient.post<CollectionItem>(`/collections/${collectionId}/items/url`, {
    url,
  })
}

export function updateCollectionItem(
  collectionId: string,
  itemId: string,
  isActive: boolean
) {
  return apiClient.patch<CollectionItem>(
    `/collections/${collectionId}/items/${itemId}`,
    { is_active: isActive }
  )
}

export function bulkUpdateCollectionItems(
  collectionId: string,
  updates: { item_id: string; is_active: boolean }[]
) {
  return apiClient.patch<CollectionItem[]>(
    `/collections/${collectionId}/items/bulk`,
    { updates }
  )
}

export function deleteCollectionItem(collectionId: string, itemId: string) {
  return apiClient.delete<void>(`/collections/${collectionId}/items/${itemId}`)
}

export function getCollectionItemContentUrl(collectionId: string, itemId: string) {
  return `${API_BASE_URL}/collections/${collectionId}/items/${itemId}/content`
}

export async function getCollectionItemContentText(
  collectionId: string,
  itemId: string
): Promise<string> {
  const response = await fetch(getCollectionItemContentUrl(collectionId, itemId), {
    credentials: "include",
    cache: "no-store",
  })
  if (!response.ok) {
    let detail = "Couldn't load this file's content."
    try {
      const body = await response.json()
      if (typeof body?.detail === "string") detail = body.detail
    } catch {
      // response wasn't JSON; fall back to the default message
    }
    throw new ApiError(response.status, detail)
  }
  return response.text()
}