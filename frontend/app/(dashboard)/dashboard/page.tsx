import { cookies } from "next/headers"
import { ProjectCard } from "@/components/projects/ProjectCard"
import { CreateProjectDialog } from "@/components/projects/CreateProjectDialog"
import { FolderOpen } from "lucide-react"

async function getProjects() {
  const cookieStore = await cookies()
  const token = cookieStore.get("access_token")
  const res = await fetch("http://fastapi:8000/api/v1/projects", {
    headers: { Cookie: `access_token=${token?.value}` },
    cache: "no-store",
  })
  if (!res.ok) return []
  return res.json()
}

export default async function DashboardPage() {
  const projects = await getProjects()
  return (
    <div>
      <div className="flex items-center justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Проекты</h1>
          {projects.length > 0 && (
            <p className="text-sm text-muted-foreground mt-0.5">
              {projects.length} {projects.length === 1 ? "проект" : projects.length < 5 ? "проекта" : "проектов"}
            </p>
          )}
        </div>
        <CreateProjectDialog />
      </div>

      {projects.length === 0 ? (
        <div className="flex flex-col items-center justify-center py-20 text-center">
          <div className="w-14 h-14 rounded-2xl bg-primary/10 flex items-center justify-center mb-4">
            <FolderOpen className="w-7 h-7 text-primary" />
          </div>
          <h2 className="text-base font-semibold text-foreground mb-1">Нет проектов</h2>
          <p className="text-sm text-muted-foreground mb-6 max-w-xs">
            Создайте первый проект, чтобы начать расчёт маржи строительного тендера
          </p>
          <CreateProjectDialog />
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {projects.map((p: any) => <ProjectCard key={p.id} project={p} />)}
        </div>
      )}
    </div>
  )
}
