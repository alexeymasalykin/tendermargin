"use client"

import { useState } from "react"
import { createColumnHelper } from "@tanstack/react-table"
import { DataTable } from "@/components/tables/DataTable"
import { Button } from "@/components/ui/button"
import { Download, Loader2 } from "lucide-react"
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

function ExportButton({ projectId }: { projectId: string }) {
  const [loading, setLoading] = useState(false)

  async function handleExport() {
    setLoading(true)
    try {
      const res = await fetch(`/api/v1/projects/${projectId}/materials/export`, {
        method: "POST",
        credentials: "include",
      })
      if (!res.ok) throw new Error("Export failed")
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `materials-${projectId}.xlsx`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      console.error("Export failed")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Button variant="outline" size="sm" onClick={handleExport} disabled={loading}>
      {loading ? <Loader2 className="w-4 h-4 mr-2 animate-spin" /> : <Download className="w-4 h-4 mr-2" />}
      Экспорт Excel
    </Button>
  )
}

export function MaterialsTable({ data, projectId }: { data: Material[]; projectId: string }) {
  return (
    <div>
      <div className="flex justify-end mb-4">
        <ExportButton projectId={projectId} />
      </div>
      <DataTable
        data={data}
        columns={columns}
        emptyText="Нет материалов"
        searchPlaceholder="Поиск по названию..."
      />
    </div>
  )
}
