"use client"
import { useState, useCallback, useRef } from "react"
import { api } from "@/lib/api"
import { toast } from "sonner"
import type { ContractorPrice } from "@/types/api"

// Extended type with computed fields
export interface ContractorPriceRow extends ContractorPrice {
  contractor_sum: number | null
  delta_pct: number | null
}

export function useContractorPrices(projectId: string, initial: ContractorPrice[]) {
  const [prices, setPrices] = useState<ContractorPriceRow[]>(
    initial.map(p => ({
      ...p,
      contractor_sum: p.price != null ? p.price * p.quantity : null,
      delta_pct: p.price != null && p.ceiling_total > 0
        ? ((p.ceiling_total - p.price * p.quantity) / p.ceiling_total) * 100
        : null,
    }))
  )
  const pending = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())

  const updatePrice = useCallback((smeta_item_id: string, price: number | null) => {
    setPrices(prev =>
      prev.map(p => p.smeta_item_id === smeta_item_id
        ? {
            ...p,
            price,
            contractor_sum: price != null ? price * p.quantity : null,
            delta_pct: price != null && p.ceiling_total > 0
              ? ((p.ceiling_total - price * p.quantity) / p.ceiling_total) * 100
              : null,
          }
        : p
      )
    )

    const existing = pending.current.get(smeta_item_id)
    if (existing) clearTimeout(existing)
    const t = setTimeout(async () => {
      pending.current.delete(smeta_item_id)
      if (price == null) return
      try {
        await api.contractor.batchUpdate(projectId, [{ smeta_item_id, price }])
        toast.success("Сохранено", { duration: 1500 })
      } catch {
        toast.error("Ошибка сохранения")
      }
    }, 500)
    pending.current.set(smeta_item_id, t)
  }, [projectId])

  return { prices, updatePrice }
}
