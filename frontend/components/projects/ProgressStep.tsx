import Link from "next/link"
import { CheckCircle2, Circle, Clock, Lock, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import type { StepStatus } from "@/types/api"

interface ProgressStepProps {
  label: string
  href: string
  status: StepStatus | "locked"
  detail?: string
  cta?: string
}

const ICON = {
  completed: CheckCircle2,
  in_progress: Clock,
  not_started: Circle,
  locked: Lock,
}
const BG = {
  completed: "bg-success/10",
  in_progress: "bg-warning/10",
  not_started: "bg-muted",
  locked: "bg-muted/50",
}
const ICON_COLOR = {
  completed: "text-success",
  in_progress: "text-warning",
  not_started: "text-muted-foreground",
  locked: "text-muted-foreground/40",
}

export function ProgressStep({ label, href, status, detail, cta }: ProgressStepProps) {
  const Icon = ICON[status]
  const locked = status === "locked"
  const completed = status === "completed"

  const content = (
    <div className={cn(
      "flex items-center gap-4 p-4 rounded-xl border transition-colors duration-200",
      locked
        ? "border-border/50 bg-muted/30 opacity-60"
        : "border-border bg-surface hover:border-primary/30 shadow-card hover:shadow-card-hover",
      completed && "border-success/20 bg-success/5",
    )}>
      <div className={cn("w-9 h-9 rounded-lg flex items-center justify-center flex-shrink-0", BG[status])}>
        <Icon className={cn("w-5 h-5", ICON_COLOR[status])} />
      </div>
      <div className="flex-1 min-w-0">
        <p className={cn("font-medium text-sm", locked ? "text-muted-foreground" : "text-foreground")}>
          {label}
        </p>
        {detail && <p className="text-xs text-muted-foreground mt-0.5">{detail}</p>}
      </div>
      {!locked && (
        <span className="flex items-center gap-0.5 text-sm text-primary font-medium shrink-0">
          {cta ?? "Открыть"}
          <ChevronRight className="w-4 h-4" />
        </span>
      )}
      {locked && (
        <Lock className="w-4 h-4 text-muted-foreground/40 shrink-0" />
      )}
    </div>
  )

  if (locked) return content

  return <Link href={href}>{content}</Link>
}
