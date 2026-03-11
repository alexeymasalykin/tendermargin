"use client"
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, Cell,
} from "recharts"
import { formatMoney } from "@/lib/utils"
import type { MarginItem } from "@/types/api"

const STATUS_COLOR: Record<string, string> = {
  green: "#16A34A",
  yellow: "#EAB308",
  red: "#EA580C",
  loss: "#DC2626",
}

export function MarginChart({ items }: { items: MarginItem[] }) {
  const data = items.slice(0, 20).map(item => ({
    name: item.name.length > 30 ? item.name.slice(0, 30) + "…" : item.name,
    ceiling: item.ceiling_price,
    cost: item.cost_price,
    status: item.status,
  }))

  return (
    <div className="bg-surface border border-border rounded-lg p-4">
      <h3 className="text-sm font-medium mb-4 text-muted-foreground">Потолок vs Себестоимость (топ 20 позиций)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data} layout="vertical" margin={{ left: 20, right: 20 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#E2E8F0" horizontal={false} />
          <XAxis type="number" tickFormatter={v => formatMoney(v)} tick={{ fontSize: 11 }} />
          <YAxis type="category" dataKey="name" width={180} tick={{ fontSize: 11 }} />
          <Tooltip
            formatter={(value, name) => [formatMoney(Number(value)) + " ₽", name === "ceiling" ? "Потолок" : "Себестоимость"]}
            contentStyle={{ fontSize: 12, border: "1px solid #E2E8F0" }}
          />
          <Legend formatter={v => v === "ceiling" ? "Потолок" : "Себестоимость"} />
          <Bar dataKey="ceiling" fill="#93C5FD" radius={[0, 2, 2, 0]} />
          <Bar dataKey="cost" radius={[0, 2, 2, 0]}>
            {data.map((entry, i) => (
              <Cell key={i} fill={STATUS_COLOR[entry.status] ?? "#64748B"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  )
}
