import { cookies } from "next/headers"
import { createColumnHelper } from "@tanstack/react-table"
import { DataTable } from "@/components/tables/DataTable"
import { Breadcrumbs } from "@/components/layout/Breadcrumbs"
import { Button } from "@/components/ui/button"
import { Download } from "lucide-react"
import { formatMoney } from "@/lib/utils"
import type { Material } from "@/types/api"

const col = createColumnHelper<Material>()

const columns = [
  col.display({ id: "num", header: "№", cell: i => i.row.index + 1 }),
  col.accessor("name", { header: "Наименование" }),
  col.accessor("unit", { header: "Ед." }),
  col.accessor("quantity", {
    header: "Объём",
    cell: i => <span className="font-mono tabular-nums text-right block">{i.getValue()}</span>,
  }),
  col.accessor("supplier_price", {
    header: "Цена поставщика, ₽",
    cell: i => {
      const v = i.getValue()
      return v != null
        ? <span className="font-mono tabular-nums text-right block">{formatMoney(v)}</span>
        : <span className="text-muted-foreground text-xs">—</span>
    },
  }),
  col.accessor("supplier_total", {
    header: "Сумма, ₽",
    cell: i => {
      const v = i.getValue()
      return v != null
        ? <span className="font-mono tabular-nums text-right block font-medium">{formatMoney(v)}</span>
        : <span className="text-muted-foreground text-xs">—</span>
    },
  }),
]

async function getMaterials(projectId: string): Promise<Material[]> {
  const cookieStore = await cookies()
  const token = cookieStore.get("access_token")
  const res = await fetch(`http://fastapi:8000/api/v1/projects/${projectId}/materials`, {
    headers: { Cookie: `access_token=${token?.value}` },
    cache: "no-store",
  })
  if (!res.ok) return []
  return res.json()
}

function ExportButton({ projectId }: { projectId: string }) {
  return (
    <a href={`/api/v1/projects/${projectId}/materials/export`} download>
      <Button variant="outline" size="sm">
        <Download className="w-4 h-4 mr-2" />
        Экспорт Excel
      </Button>
    </a>
  )
}

export default async function MaterialsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const materials = await getMaterials(id)
  const filled = materials.filter(m => m.supplier_price != null).length

  return (
    <div>
      <Breadcrumbs crumbs={[
        { label: "Проекты", href: "/dashboard" },
        { label: "Обзор", href: `/projects/${id}` },
        { label: "Материалы" },
      ]} />
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Материалы</h1>
          {materials.length > 0 && (
            <p className="text-sm text-muted-foreground mt-0.5">
              Цены: {filled}/{materials.length} заполнено
            </p>
          )}
        </div>
        {materials.length > 0 && <ExportButton projectId={id} />}
      </div>

      {materials.length === 0 ? (
        <p className="text-muted-foreground text-sm">Загрузите смету для формирования ведомости материалов</p>
      ) : (
        <DataTable
          data={materials}
          columns={columns}
          emptyText="Нет материалов"
          searchPlaceholder="Поиск по названию..."
        />
      )}
    </div>
  )
}
