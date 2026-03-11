import { Card, CardContent } from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface MetricCardProps {
  label: string
  value: string
  sub?: string
  highlight?: boolean
}

export function MetricCard({ label, value, sub, highlight }: MetricCardProps) {
  return (
    <Card
      className={cn(
        "transition-colors duration-200 shadow-card",
        highlight
          ? "border-primary/30 bg-gradient-to-br from-primary/5 to-primary/10"
          : "border-border/60"
      )}
    >
      <CardContent className="pt-4 pb-4">
        <p className="text-[11px] font-medium text-muted-foreground uppercase tracking-widest">{label}</p>
        <p className={cn(
          "text-2xl font-bold font-mono mt-1.5 tracking-tight",
          highlight ? "text-primary" : "text-foreground"
        )}>
          {value}
        </p>
        {sub && <p className="text-xs text-muted-foreground mt-0.5">{sub}</p>}
      </CardContent>
    </Card>
  )
}
