const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000"

export class ApiError extends Error {
  status: number
  detail: unknown

  constructor(status: number, detail: unknown) {
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail) && detail[0]?.msg
          ? detail[0].msg
          : "Something went wrong."
    super(message)
    this.status = status
    this.detail = detail
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...options.headers,
    },
  })

  const isJson = response.headers
    .get("content-type")
    ?.includes("application/json")
  const body = isJson ? await response.json() : undefined

  if (!response.ok) {
    throw new ApiError(response.status, body?.detail)
  }

  return body as T
}

export const apiClient = {
  get: <T>(path: string) => request<T>(path, { method: "GET" }),
  post: <T>(path: string, data?: unknown) =>
    request<T>(path, {
      method: "POST",
      body: data !== undefined ? JSON.stringify(data) : undefined,
    }),
}