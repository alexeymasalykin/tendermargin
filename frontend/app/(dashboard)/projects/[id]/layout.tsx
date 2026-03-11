import { cookies } from "next/headers"
import { Sidebar } from "@/components/layout/Sidebar"
import { ProjectMobileNav } from "@/components/layout/ProjectMobileNav"
import type { ProjectDetail } from "@/types/api"

async function getProject(id: string): Promise<ProjectDetail | null> {
  const cookieStore = await cookies()
  const token = cookieStore.get("access_token")
  const res = await fetch(`http://fastapi:8000/api/v1/projects/${id}`, {
    headers: { Cookie: `access_token=${token?.value}` },
    cache: "no-store",
  })
  if (!res.ok) return null
  return res.json()
}

export default async function ProjectLayout({
  children,
  params,
}: {
  children: React.ReactNode
  params: Promise<{ id: string }>
}) {
  const { id } = await params
  const project = await getProject(id)
  if (!project) return <div className="p-6 text-destructive">Проект не найден</div>

  const p = project.progress
  const marginAvailable = p.pricelist.status !== "not_started" || p.contractor.status !== "not_started"

  const steps = [
    { label: "Обзор", href: `/projects/${id}`, icon: "BarChart2" as const, status: "completed" as const },
    { label: "Смета", href: `/projects/${id}/smeta`, icon: "FileText" as const, status: p.smeta.status },
    { label: "Материалы", href: `/projects/${id}/materials`, icon: "Package" as const, status: p.materials.status },
    { label: "Расценки", href: `/projects/${id}/contractor`, icon: "Wrench" as const, status: p.contractor.status },
    { label: "Прайсы", href: `/projects/${id}/pricelist`, icon: "ShoppingCart" as const, status: p.pricelist.status },
    {
      label: "Результат",
      href: `/projects/${id}/result`,
      icon: "BarChart2" as const,
      status: marginAvailable ? (p.margin.available ? "completed" as const : "in_progress" as const) : "locked" as "locked",
    },
  ]

  return (
    <div className="flex flex-col md:flex-row flex-1 -m-4 sm:-m-6">
      {/* Mobile horizontal tabs */}
      <ProjectMobileNav steps={steps} />
      {/* Desktop sidebar */}
      <Sidebar projectId={id} projectSteps={steps} />
      <main id="main-content" className="flex-1 p-4 sm:p-6 overflow-auto">
        {children}
      </main>
    </div>
  )
}
