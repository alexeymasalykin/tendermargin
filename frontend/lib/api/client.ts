const BASE = "/api/v1"

export async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...options?.headers },
    credentials: "include",
    ...options,
  })

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Network error" }))
    throw { status: res.status, ...err }
  }

  if (res.status === 204) return undefined as T
  return res.json()
}

export { BASE }
