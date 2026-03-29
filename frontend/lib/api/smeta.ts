import { request } from "./client"
import type { SmetaItem } from "@/types/api"

export const smeta = {
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
}
