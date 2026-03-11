"use client"
import { createColumnHelper } from "@tanstack/react-table"
import { DataTable } from "@/components/tables/DataTable"
import { Badge } from "@/components/ui/badge"
import { ITEM_TYPE_COLORS } from "./SmetaUpload"
import { formatMoney, cn } from "@/lib/utils"
import type { SmetaItem } from "@/types/api"

const TYPE_LABELS: Record<string, string> = {
  work: "Работа", material: "Материал",
  equipment: "Оборудование", mechanism: "Механизм", unknown: "—",
}
const TYPE_VARIANTS: Record<string, "default" | "secondary" | "outline"> = {
  work: "default", material: "secondary", equipment: "outline", mechanism: "outline", unknown: "outline",
}

const col = createColumnHelper<SmetaItem>()

const columns = [
  col.accessor("number", { header: "№", cell: i => <span className="font-mono text-xs">{i.getValue()}</span> }),
  col.accessor("code", { header: "Код", cell: i => <span className="font-mono text-xs text-muted-foreground">{i.getValue()}</span> }),
  col.accessor("name", {
    header: "Наименование",
    cell: i => (
      <div className={cn("border-l-4 pl-3 py-0.5", ITEM_TYPE_COLORS[i.row.original.item_type] ?? "border-l-border")}>
        {i.getValue()}
      </div>
    ),
  }),
  col.accessor("unit", { header: "Ед." }),
  col.accessor("quantity", {
    header: "Кол-во",
    cell: i => <span className="font-mono tabular-nums text-right block">{i.getValue()}</span>,
  }),
  col.accessor("total_price", {
    header: "Потолок, ₽",
    cell: i => <span className="font-mono tabular-nums text-right block">{formatMoney(i.getValue())}</span>,
  }),
  col.accessor("item_type", {
    header: "Тип",
    cell: i => (
      <Badge variant={TYPE_VARIANTS[i.getValue()] ?? "outline"} className="text-xs">
        {TYPE_LABELS[i.getValue()] ?? i.getValue()}
      </Badge>
    ),
  }),
]

export function SmetaTable({ items }: { items: SmetaItem[] }) {
  return (
    <DataTable
      data={items}
      columns={columns}
      searchPlaceholder="Поиск по названию или коду..."
      emptyText="Нет позиций в смете"
      pageSize={20}
    />
  )
}
