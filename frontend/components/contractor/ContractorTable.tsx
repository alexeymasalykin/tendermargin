"use client"
import { createColumnHelper } from "@tanstack/react-table"
import { DataTable } from "@/components/tables/DataTable"
import { useContractorPrices, type ContractorPriceRow } from "@/hooks/useContractorPrices"
import { formatMoney, formatPercent, cn } from "@/lib/utils"
import { Progress } from "@/components/ui/progress"
import type { ContractorPrice } from "@/types/api"

const DELTA_COLOR = (pct: number | null) => {
  if (pct === null) return "text-muted-foreground"
  if (pct > 15) return "text-success font-medium"
  if (pct > 5) return "text-warning font-medium"
  if (pct >= 0) return "text-destructive font-medium"
  return "text-destructive font-bold"
}

function PriceCell({
  smeta_item_id, price, onUpdate,
}: {
  smeta_item_id: string
  price: number | null
  onUpdate: (id: string, price: number | null) => void
}) {
  return (
    <input
      type="number"
      min={0}
      step={0.01}
      defaultValue={price ?? ""}
      onBlur={e => {
        const v = e.target.value === "" ? null : parseFloat(e.target.value)
        onUpdate(smeta_item_id, v)
      }}
      onKeyDown={e => { if (e.key === "Enter") (e.target as HTMLInputElement).blur() }}
      placeholder="Введите цену"
      className={cn(
        "w-28 px-2 py-1 text-right font-mono tabular-nums text-sm rounded border",
        "border-border focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary",
        price == null && "border-dashed text-muted-foreground"
      )}
    />
  )
}

export function ContractorTable({ projectId, initial }: { projectId: string; initial: ContractorPrice[] }) {
  const { prices, updatePrice } = useContractorPrices(projectId, initial)

  const col = createColumnHelper<ContractorPriceRow>()
  const columns = [
    col.display({ id: "num", header: "№", cell: i => i.row.index + 1 }),
    col.accessor("name", { header: "Наименование" }),
    col.accessor("unit", { header: "Ед." }),
    col.accessor("quantity", {
      header: "Кол-во",
      cell: i => <span className="font-mono tabular-nums text-right block">{i.getValue()}</span>,
    }),
    col.accessor("ceiling_total", {
      header: "Потолок, ₽",
      cell: i => <span className="font-mono tabular-nums text-right block text-muted-foreground">{formatMoney(i.getValue())}</span>,
    }),
    col.accessor("smeta_item_id", {
      header: "Цена подр., ₽/ед.",
      cell: i => (
        <PriceCell
          smeta_item_id={i.getValue()}
          price={i.row.original.price}
          onUpdate={updatePrice}
        />
      ),
    }),
    col.accessor("contractor_sum", {
      header: "Сумма подр., ₽",
      cell: i => {
        const v = i.getValue()
        return v != null
          ? <span className="font-mono tabular-nums text-right block font-medium">{formatMoney(v)}</span>
          : <span className="text-muted-foreground text-xs">—</span>
      },
    }),
    col.accessor("delta_pct", {
      header: "Δ к смете",
      cell: i => {
        const v = i.getValue()
        return <span className={cn("font-mono tabular-nums text-right block", DELTA_COLOR(v))}>
          {v != null ? formatPercent(v) : "—"}
        </span>
      },
    }),
  ]

  const filled = prices.filter(p => p.price != null).length
  const pct = prices.length > 0 ? Math.round((filled / prices.length) * 100) : 0

  return (
    <div className="space-y-4">
      <DataTable
        data={prices}
        columns={columns}
        searchPlaceholder="Поиск по наименованию..."
        emptyText="Нет позиций для ввода расценок"
        pageSize={20}
      />
      <div className="space-y-1">
        <div className="flex justify-between text-sm text-muted-foreground">
          <span>Заполнено</span>
          <span className="font-mono">{filled}/{prices.length} ({pct}%)</span>
        </div>
        <Progress value={pct} className="h-2" />
      </div>
    </div>
  )
}
