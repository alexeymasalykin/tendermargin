"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"

interface Step {
  label: string
  href: string
  status?: string
}

const STATUS_DOT: Record<string, string> = {
  not_started: "bg-slate-300",
  in_progress: "bg-warning",
  completed: "bg-success",
  locked: "bg-slate-200",
}

export function ProjectMobileNav({ steps }: { steps: Step[] }) {
  const pathname = usePathname()

  return (
    <nav className="md:hidden border-b border-border bg-surface overflow-x-auto">
      <div className="flex gap-0 min-w-max">
        {steps.map(step => {
          const isLocked = step.status === "locked"
          const active = step.href === pathname ||
            (step.href !== steps[0]?.href && pathname.startsWith(step.href))

          return (
            <Link
              key={step.href}
              href={isLocked ? "#" : step.href}
              className={cn(
                "flex items-center gap-1.5 px-3 py-2.5 text-xs font-medium whitespace-nowrap border-b-2 transition-colors",
                active
                  ? "border-primary text-primary"
                  : "border-transparent text-muted-foreground hover:text-foreground",
                isLocked && "opacity-40 pointer-events-none"
              )}
            >
              {step.status && (
                <span className={cn("w-1.5 h-1.5 rounded-full", STATUS_DOT[step.status] ?? "bg-slate-300")} />
              )}
              {step.label}
            </Link>
          )
        })}
      </div>
    </nav>
  )
}
