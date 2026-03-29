import { request, BASE } from "./client"
import type { MarginResult } from "@/types/api"

export const margin = {
  get: (projectId: string) => request<MarginResult>(`/projects/${projectId}/margin`),
  export: (projectId: string) =>
    fetch(`${BASE}/projects/${projectId}/margin/export`, { method: "POST", credentials: "include" }),
}
