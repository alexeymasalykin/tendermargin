"use client"
import { useState } from "react"
import { CheckCircle2, AlertCircle, HelpCircle } from "lucide-react"
import { api } from "@/lib/api"
import { cn, formatMoney } from "@/lib/utils"
import { toast } from "sonner"
import type { PricelistMatch } from "@/types/api"

const CONF_COLOR = (c: number | null) =>
  c == null ? "text-muted-foreground" : c >= 0.85 ? "text-success" : c >= 0.5 ? "text-warning" : "text-destructive"
const CONF_ICON = (c: number | null) =>
  c != null && c >= 0.85 ? CheckCircle2 : c != null && c >= 0.5 ? HelpCircle : AlertCircle

export function MappingTable({ projectId, initial }: { projectId: string; initial: PricelistMatch[] }) {
  const [matches, setMatches] = useState(initial)

  async function handlePriceChange(id: string, supplier_price: number) {
    try {
      await api.pricelist.updateMatches(projectId, [{ id, supplier_price, status: "manual" }])
      setMatches(prev => prev.map(m => m.id === id ? { ...m, supplier_price, status: "manual" as any } : m))
      toast.success("Сохранено", { duration: 1500 })
    } catch {
      toast.error("Ошибка сохранения")
    }
  }

  return (
    <div className="border border-border rounded-lg overflow-hidden">
      <table className="w-full text-sm">
        <thead className="bg-muted/50">
          <tr>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">ID материала</th>
            <th className="px-4 py-3 text-left font-medium text-muted-foreground">Найдено в прайсе</th>
            <th className="px-4 py-3 text-center font-medium text-muted-foreground">Совпадение</th>
            <th className="px-4 py-3 text-right font-medium text-muted-foreground">Цена, ₽</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {matches.map(m => {
            const Icon = CONF_ICON(m.confidence)
            return (
              <tr key={m.id} className="hover:bg-muted/20">
                <td className="px-4 py-3 font-medium font-mono text-xs text-muted-foreground">{m.material_id.slice(0, 8)}…</td>
                <td className="px-4 py-3 text-muted-foreground">{m.supplier_name ?? "—"}</td>
                <td className="px-4 py-3">
                  <span className={cn("flex items-center justify-center gap-1 font-mono text-xs", CONF_COLOR(m.confidence))}>
                    <Icon className="w-3.5 h-3.5" />
                    {m.confidence != null ? (m.confidence * 100).toFixed(0) + "%" : "—"}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  {m.confidence != null && m.confidence >= 0.85 && m.supplier_price != null ? (
                    <span className="font-mono tabular-nums">{formatMoney(m.supplier_price)}</span>
                  ) : (
                    <input
                      type="number"
                      min={0}
                      defaultValue={m.supplier_price ?? ""}
                      placeholder="Введите цену"
                      onBlur={e => {
                        const v = parseFloat(e.target.value)
                        if (!isNaN(v)) handlePriceChange(m.id, v)
                      }}
                      className="w-28 px-2 py-1 text-right font-mono text-sm rounded border border-dashed border-border focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
                    />
                  )}
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
