import { cookies } from "next/headers"
import { ContractorTable } from "@/components/contractor/ContractorTable"
import { Breadcrumbs } from "@/components/layout/Breadcrumbs"

async function getContractorPrices(projectId: string) {
  const cookieStore = await cookies()
  const token = cookieStore.get("access_token")
  const res = await fetch(`http://fastapi:8000/api/v1/projects/${projectId}/contractor-prices`, {
    headers: { Cookie: `access_token=${token?.value}` },
    cache: "no-store",
  })
  if (!res.ok) return []
  return res.json()
}

export default async function ContractorPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const prices = await getContractorPrices(id)

  return (
    <div>
      <Breadcrumbs crumbs={[
        { label: "Проекты", href: "/dashboard" },
        { label: "Обзор", href: `/projects/${id}` },
        { label: "Расценки подрядчика" },
      ]} />
      <div className="mb-6">
        <h1 className="text-xl font-semibold">Расценки подрядчика</h1>
        <p className="text-sm text-muted-foreground mt-1">
          Введите цену за единицу — сохранение автоматическое
        </p>
      </div>

      {prices.length === 0 ? (
        <p className="text-muted-foreground text-sm">Загрузите смету для заполнения расценок</p>
      ) : (
        <ContractorTable projectId={id} initial={prices} />
      )}
    </div>
  )
}
