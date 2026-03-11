"use client"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import { LayoutDashboard, Settings, BarChart2, FileText, Package, Wrench, ShoppingCart } from "lucide-react"

type IconName = "LayoutDashboard" | "Settings" | "BarChart2" | "FileText" | "Package" | "Wrench" | "ShoppingCart"

const ICON_MAP: Record<IconName, React.ElementType> = {
  LayoutDashboard, Settings, BarChart2, FileText, Package, Wrench, ShoppingCart,
}

interface SidebarItem {
  label: string
  href: string
  icon: IconName
  status?: "not_started" | "in_progress" | "completed" | "locked"
}
interface SidebarProps { projectId?: string; projectSteps?: SidebarItem[] }

const STATUS_DOT: Record<string, string> = {
  not_started: "bg-slate-300",
  in_progress: "bg-warning",
  completed: "bg-success",
  locked: "bg-slate-200",
}

export function Sidebar({ projectSteps }: SidebarProps) {
  const pathname = usePathname()
  const topItems: SidebarItem[] = [
    { label: "Проекты", href: "/dashboard", icon: "LayoutDashboard" },
    { label: "Настройки", href: "/settings", icon: "Settings" },
  ]
  const items = projectSteps ?? topItems

  return (
    <aside className="hidden md:flex w-56 shrink-0 border-r border-border bg-surface flex-col">
      <nav className="flex flex-col gap-0.5 p-3 flex-1">
        {items.map(item => {
          const Icon = ICON_MAP[item.icon]
          const isLocked = item.status === "locked"
          const active = item.href === "/dashboard"
            ? pathname === item.href
            : pathname.startsWith(item.href)
          return (
            <Link
              key={item.href}
              href={isLocked ? "#" : item.href}
              aria-disabled={isLocked}
              className={cn(
                "relative flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-all duration-200",
                active
                  ? "bg-primary/10 text-primary font-semibold"
                  : "text-slate-600 hover:bg-slate-50 hover:text-slate-900",
                isLocked && "opacity-40 pointer-events-none cursor-not-allowed"
              )}
            >
              {active && (
                <span className="absolute left-0 top-1/2 -translate-y-1/2 w-0.5 h-4 bg-primary rounded-r-full" />
              )}
              <Icon className={cn("w-4 h-4 shrink-0", active ? "text-primary" : "text-slate-400")} />
              <span className="flex-1 truncate">{item.label}</span>
              {item.status && (
                <span
                  className={cn("w-2 h-2 rounded-full shrink-0", STATUS_DOT[item.status])}
                  title={item.status === "completed" ? "Готово" : item.status === "in_progress" ? "В работе" : item.status === "locked" ? "Заблокировано" : "Не начато"}
                />
              )}
            </Link>
          )
        })}
      </nav>
    </aside>
  )
}
