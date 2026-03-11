import { cookies } from "next/headers"
import { MetricCard } from "@/components/projects/MetricCard"
import { MarginChart } from "@/components/result/MarginChart"
import { ResultTable } from "@/components/result/ResultTable"
import { Breadcrumbs } from "@/components/layout/Breadcrumbs"
import { Button } from "@/components/ui/button"
import { Download } from "lucide-react"
import { formatMoney, formatPercent } from "@/lib/utils"
import type { MarginResult } from "@/types/api"

async function getMargin(projectId: string): Promise<MarginResult | null> {
  const cookieStore = await cookies()
  const token = cookieStore.get("access_token")
  const res = await fetch(`http://fastapi:8000/api/v1/projects/${projectId}/margin`, {
    headers: { Cookie: `access_token=${token?.value}` },
    cache: "no-store",
  })
  if (!res.ok) return null
  return res.json()
}

export default async function ResultPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const margin = await getMargin(id)

  return (
    <div>
      <Breadcrumbs crumbs={[
        { label: "Проекты", href: "/dashboard" },
        { label: "Обзор", href: `/projects/${id}` },
        { label: "Результат" },
      ]} />
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Результат расчёта</h1>
        {margin && (
          <a href={`/api/v1/projects/${id}/margin/export`} download>
            <Button variant="outline" size="sm">
              <Download className="w-4 h-4 mr-2" />Экспорт Excel
            </Button>
          </a>
        )}
      </div>

      {!margin ? (
        <p className="text-muted-foreground text-sm">
          Заполните расценки подрядчика или загрузите прайс поставщика для расчёта маржи
        </p>
      ) : (
        <div className="space-y-8">
          <div className="grid grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
            <MetricCard label="НМЦК" value={formatMoney(margin.total_ceiling) + " ₽"} />
            <MetricCard label="Себестоимость" value={formatMoney(margin.total_cost) + " ₽"} />
            <MetricCard label="Маржа" value={formatMoney(margin.total_margin) + " ₽"} />
            <MetricCard label="Маржа %" value={formatPercent(margin.margin_pct)} highlight />
            <MetricCard label="Макс. снижение" value={formatPercent(margin.max_discount_pct)} />
            <MetricCard label="Цена пол" value={formatMoney(margin.floor_price) + " ₽"} />
          </div>

          <MarginChart items={margin.items} />

          <div>
            <h2 className="font-semibold mb-3">Детализация по позициям</h2>
            <ResultTable items={margin.items} />
          </div>
        </div>
      )}
    </div>
  )
}
