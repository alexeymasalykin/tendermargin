import { request } from "./client"
import type { PricelistMatch } from "@/types/api"

export const pricelist = {
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
}
