import { cookies } from "next/headers"
import { MetricCard } from "@/components/projects/MetricCard"
import { ProgressStep } from "@/components/projects/ProgressStep"
import { Breadcrumbs } from "@/components/layout/Breadcrumbs"
import { formatMoney, formatPercent } from "@/lib/utils"
import type { ProjectDetail } from "@/types/api"

async function getProject(id: string): Promise<ProjectDetail> {
  const cookieStore = await cookies()
  const token = cookieStore.get("access_token")
  const res = await fetch(`http://fastapi:8000/api/v1/projects/${id}`, {
    headers: { Cookie: `access_token=${token?.value}` },
    cache: "no-store",
  })
  return res.json()
}

export default async function ProjectPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const project = await getProject(id)
  const p = project.progress
  const m = p.margin

  return (
    <div>
      <Breadcrumbs crumbs={[{ label: "Проекты", href: "/dashboard" }, { label: project.name }]} />
      <h1 className="text-xl font-semibold mb-6">{project.name}</h1>

      {m.available && (
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
          <MetricCard label="Смета (НМЦК)" value={formatMoney(p.smeta.total_sum ?? 0) + " ₽"} />
          <MetricCard label="Маржа" value={formatPercent(m.margin_pct ?? 0)} highlight />
        </div>
      )}

      <div className="space-y-2 max-w-2xl">
        <ProgressStep label="Смета" href={`/projects/${id}/smeta`} status={p.smeta.status}
          detail={p.smeta.item_count ? `${p.smeta.item_count} позиций` : "Не загружена"}
          cta={p.smeta.status === "not_started" ? "Загрузить" : "Открыть →"} />
        <ProgressStep label="Материалы" href={`/projects/${id}/materials`} status={p.materials.status}
          detail={p.materials.filled != null ? `${p.materials.filled}/${p.materials.total} с ценами` : undefined} />
        <ProgressStep label="Расценки подрядчика" href={`/projects/${id}/contractor`} status={p.contractor.status}
          detail={p.contractor.filled != null ? `${p.contractor.filled}/${p.contractor.total} заполнено` : undefined} />
        <ProgressStep label="Прайсы поставщиков" href={`/projects/${id}/pricelist`} status={p.pricelist.status} />
        <ProgressStep label="Результат" href={`/projects/${id}/result`}
          status={m.available ? "completed" : "locked"} />
      </div>
    </div>
  )
}
