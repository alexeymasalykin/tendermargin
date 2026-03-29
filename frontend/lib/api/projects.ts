import { request } from "./client"
import type { Project, ProjectDetail } from "@/types/api"

export const projects = {
  list: () => request<Project[]>("/projects"),
  get: (id: string) => request<ProjectDetail>(`/projects/${id}`),
  create: (data: { name: string; description: string }) =>
    request<Project>("/projects", { method: "POST", body: JSON.stringify(data) }),
  update: (id: string, data: { name?: string; description?: string }) =>
    request<Project>(`/projects/${id}`, { method: "PUT", body: JSON.stringify(data) }),
  delete: (id: string) => request<void>(`/projects/${id}`, { method: "DELETE" }),
}
