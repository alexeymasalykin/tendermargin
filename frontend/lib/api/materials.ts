import { request, BASE } from "./client"
import type { Material } from "@/types/api"

export const materials = {
  list: (projectId: string) => request<Material[]>(`/projects/${projectId}/materials`),
  export: (projectId: string) =>
    fetch(`${BASE}/projects/${projectId}/materials/export`, { method: "POST", credentials: "include" }),
}
