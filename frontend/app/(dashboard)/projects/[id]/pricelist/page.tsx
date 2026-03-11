import { cookies } from "next/headers"
import { PricelistWizard } from "@/components/pricelist/PricelistWizard"
import { MappingTable } from "@/components/pricelist/MappingTable"
import { Breadcrumbs } from "@/components/layout/Breadcrumbs"

async function getMatches(projectId: string) {
  const cookieStore = await cookies()
  const token = cookieStore.get("access_token")
  const res = await fetch(`http://fastapi:8000/api/v1/projects/${projectId}/pricelist/matches`, {
    headers: { Cookie: `access_token=${token?.value}` },
    cache: "no-store",
  })
  if (!res.ok) return []
  return res.json()
}

export default async function PricelistPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const matches = await getMatches(id)

  return (
    <div>
      <Breadcrumbs crumbs={[
        { label: "Проекты", href: "/dashboard" },
        { label: "Обзор", href: `/projects/${id}` },
        { label: "Прайсы поставщиков" },
      ]} />
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Прайсы поставщиков</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Загрузите прайс — LLM автоматически сопоставит позиции со сметой
        </p>
      </div>

      <PricelistWizard projectId={id} />

      {matches.length > 0 && (
        <div className="mt-8 space-y-3">
          <h2 className="font-semibold">Результаты маппинга</h2>
          <MappingTable projectId={id} initial={matches} />
        </div>
      )}
    </div>
  )
}
