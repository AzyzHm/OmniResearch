import { apiClient } from "@/shared/lib/apiClient"

export const COLLECTION_TYPES = ["documents", "urls", "text"] as const
export type CollectionType = (typeof COLLECTION_TYPES)[number]

export interface Collection {
  id: string
  project_id: string
  name: string
  type: CollectionType
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
  error_message: string | null
  created_at: string
}

export function listCollections(projectId: string) {
  return apiClient.get<Collection[]>(`/projects/${projectId}/collections`)
}

export function createCollection(
  projectId: string,
  payload: { name: string; type: CollectionType }
) {
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