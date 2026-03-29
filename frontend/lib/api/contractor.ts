import { request } from "./client"
import type { ContractorPrice } from "@/types/api"

export const contractor = {
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
  uploadPricelist: (projectId: string, file: File) => {
    const fd = new FormData()
    fd.append("file", file)
    return request(`/projects/${projectId}/contractor-pricelist/upload`, { method: "POST", headers: {}, body: fd })
  },
  detectStructure: (projectId: string) =>
    request(`/projects/${projectId}/contractor-pricelist/detect`, { method: "POST" }),
  mapPricelist: (projectId: string, structure: object) =>
    request<{ task_id: string }>(`/projects/${projectId}/contractor-pricelist/map`, {
      method: "POST",
      body: JSON.stringify({ structure }),
    }),
  mapStatus: (projectId: string, task_id: string) =>
    request<{ status: string; progress: number; total: number; matches: unknown[]; error?: string }>(
      `/projects/${projectId}/contractor-pricelist/map/status?task_id=${task_id}`
    ),
}
