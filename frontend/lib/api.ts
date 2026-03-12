import type {
  User,
  Project,
  ProjectDetail,
  SmetaItem,
  Material,
  ContractorPrice,
  PricelistMatch,
  MarginResult,
} from "@/types/api"

const BASE = "/api/v1"

async function request<T>(path: string, options?: RequestInit): Promise<T> {
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

export const api = {
  auth: {
    register: (data: { email: string; password: string; name: string }) =>
      request<User>("/auth/register", { method: "POST", body: JSON.stringify(data) }),
    login: (data: { email: string; password: string }) =>
      request<User>("/auth/login", { method: "POST", body: JSON.stringify(data) }),
    logout: () => request<void>("/auth/logout", { method: "POST" }),
    me: () => request<User>("/auth/me"),
  },
  projects: {
    list: () => request<Project[]>("/projects"),
    get: (id: string) => request<ProjectDetail>(`/projects/${id}`),
    create: (data: { name: string; description: string }) =>
      request<Project>("/projects", { method: "POST", body: JSON.stringify(data) }),
    update: (id: string, data: { name?: string; description?: string }) =>
      request<Project>(`/projects/${id}`, { method: "PUT", body: JSON.stringify(data) }),
    delete: (id: string) => request<void>(`/projects/${id}`, { method: "DELETE" }),
  },
  smeta: {
    upload: (projectId: string, file: File) => {
      const fd = new FormData()
      fd.append("file", file)
      return request(`/projects/${projectId}/smeta/upload`, { method: "POST", headers: {}, body: fd })
    },
    items: (projectId: string, params?: { page?: number; page_size?: number }) => {
      const q = new URLSearchParams({
        page: String(params?.page ?? 1),
        page_size: String(params?.page_size ?? 50),
      })
      return request<{ items: SmetaItem[]; total: number; page: number; page_size: number; pages: number }>(
        `/projects/${projectId}/smeta/items?${q}`
      )
    },
  },
  materials: {
    list: (projectId: string) => request<Material[]>(`/projects/${projectId}/materials`),
    export: (projectId: string) =>
      fetch(`${BASE}/projects/${projectId}/materials/export`, { method: "POST", credentials: "include" }),
  },
  contractor: {
    list: (projectId: string) => request<ContractorPrice[]>(`/projects/${projectId}/contractor-prices`),
    batchUpdate: (projectId: string, prices: { smeta_item_id: string; price: number | null }[]) =>
      request<ContractorPrice[]>(`/projects/${projectId}/contractor-prices`, {
        method: "PUT",
        body: JSON.stringify({ prices }),
      }),
    updateOne: (projectId: string, smeta_item_id: string, price: number | null) =>
      request<ContractorPrice>(`/projects/${projectId}/contractor-prices/${smeta_item_id}`, {
        method: "PUT",
        body: JSON.stringify({ price }),
      }),
  },
  pricelist: {
    upload: (projectId: string, file: File) => {
      const fd = new FormData()
      fd.append("file", file)
      return request(`/projects/${projectId}/pricelist/upload`, { method: "POST", headers: {}, body: fd })
    },
    detectStructure: (projectId: string) =>
      request(`/projects/${projectId}/pricelist/detect-structure`, { method: "POST" }),
    map: (projectId: string, structure: object) =>
      request<{ task_id: string }>(`/projects/${projectId}/pricelist/map`, {
        method: "POST",
        body: JSON.stringify({ structure }),
      }),
    mapStatus: (projectId: string, task_id: string) =>
      request<{ status: string; progress: number; total: number; matches: unknown[]; error?: string }>(
        `/projects/${projectId}/pricelist/map/status?task_id=${task_id}`
      ),
    matches: (projectId: string) =>
      request<PricelistMatch[]>(`/projects/${projectId}/pricelist/matches`),
    updateMatches: (
      projectId: string,
      updates: { id: string; supplier_price?: number; status?: string }[]
    ) =>
      request<PricelistMatch[]>(`/projects/${projectId}/pricelist/matches`, {
        method: "PUT",
        body: JSON.stringify({ updates }),
      }),
  },
  margin: {
    get: (projectId: string) => request<MarginResult>(`/projects/${projectId}/margin`),
    export: (projectId: string) =>
      fetch(`${BASE}/projects/${projectId}/margin/export`, { method: "POST", credentials: "include" }),
  },
}
