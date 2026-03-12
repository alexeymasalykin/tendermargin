"use client"

import { createColumnHelper } from "@tanstack/react-table"
import { DataTable } from "@/components/tables/DataTable"
import { Badge } from "@/components/ui/badge"
import { formatMoney, formatPercent, cn } from "@/lib/utils"
import type { MarginItem, MarginStatus } from "@/types/api"

const STATUS_LABELS: Record<MarginStatus, string> = {
  green: "Норма", yellow: "Внимание", red: "Риск", loss: "Убыток",
}
const STATUS_VARIANT: Record<MarginStatus, "default" | "secondary" | "outline" | "destructive"> = {
  green: "default", yellow: "secondary", red: "outline", loss: "destructive",
}

const col = createColumnHelper<MarginItem>()

const columns = [
  col.display({ id: "num", header: "№", cell: i => i.row.index + 1 }),
  col.accessor("name", { header: "Наименование" }),
  col.accessor("unit", { header: "Ед." }),
  col.accessor("ceiling_price", {
    header: "Потолок, ₽",
    cell: i => <span className="font-mono tabular-nums text-right block text-muted-foreground">{formatMoney(i.getValue())}</span>,
  }),
  col.accessor("cost_price", {
    header: "Себестоимость, ₽",
    cell: i => <span className="font-mono tabular-nums text-right block">{formatMoney(i.getValue())}</span>,
  }),
  col.accessor("margin_pct", {
    header: "Маржа, %",
    cell: i => (
      <span className={cn("font-mono tabular-nums text-right block font-semibold",
        i.getValue() > 15 ? "text-success" : i.getValue() > 5 ? "text-warning" : "text-destructive"
      )}>
        {formatPercent(i.getValue())}
      </span>
    ),
  }),
  col.accessor("status", {
    header: "Статус",
    cell: i => (
      <Badge variant={STATUS_VARIANT[i.getValue() as MarginStatus] ?? "outline"}>
        {STATUS_LABELS[i.getValue() as MarginStatus] ?? i.getValue()}
      </Badge>
    ),
  }),
]

export function ResultTable({ items }: { items: MarginItem[] }) {
  return (
    <DataTable
      data={items}
      columns={columns}
      searchPlaceholder="Поиск по позиции..."
      emptyText="Нет данных для расчёта"
      pageSize={20}
    />
  )
}
