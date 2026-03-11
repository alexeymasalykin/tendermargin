"use client"
import { useState } from "react"
import Link from "next/link"
import { usePathname } from "next/navigation"
import { Menu, X, LayoutDashboard, Settings, BarChart2, FileText, Package, Wrench, ShoppingCart } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

type IconName = "LayoutDashboard" | "Settings" | "BarChart2" | "FileText" | "Package" | "Wrench" | "ShoppingCart"

const ICON_MAP: Record<IconName, React.ElementType> = {
  LayoutDashboard, Settings, BarChart2, FileText, Package, Wrench, ShoppingCart,
}

interface NavItem {
  label: string
  href: string
  icon: IconName
  status?: string
}

const STATUS_DOT: Record<string, string> = {
  not_started: "bg-slate-300",
  in_progress: "bg-warning",
  completed: "bg-success",
  locked: "bg-slate-200",
}

export function MobileNav({ items }: { items?: NavItem[] }) {
  const [open, setOpen] = useState(false)
  const pathname = usePathname()

  const navItems: NavItem[] = items ?? [
    { label: "Проекты", href: "/dashboard", icon: "LayoutDashboard" },
    { label: "Настройки", href: "/settings", icon: "Settings" },
  ]

  return (
    <>
      <Button
        variant="ghost"
        size="sm"
        className="md:hidden"
        onClick={() => setOpen(true)}
        aria-label="Открыть меню"
      >
        <Menu className="w-5 h-5" />
      </Button>

      {open && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-50 md:hidden"
            onClick={() => setOpen(false)}
          />
          {/* Drawer */}
          <nav className="fixed top-0 left-0 bottom-0 w-64 bg-surface border-r border-border z-50 p-4 flex flex-col gap-1 md:hidden shadow-elevated">
            <div className="flex items-center justify-between mb-4">
              <span className="font-semibold text-sm text-foreground">Меню</span>
              <Button variant="ghost" size="sm" onClick={() => setOpen(false)} aria-label="Закрыть меню">
                <X className="w-4 h-4" />
              </Button>
            </div>
            {navItems.map(item => {
              const Icon = ICON_MAP[item.icon]
              const isLocked = item.status === "locked"
              const active = item.href === "/dashboard"
                ? pathname === item.href
                : pathname.startsWith(item.href)
              return (
                <Link
                  key={item.href}
                  href={isLocked ? "#" : item.href}
                  onClick={() => setOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors",
                    active
                      ? "bg-primary/10 text-primary font-semibold"
                      : "text-slate-600 hover:bg-slate-50",
                    isLocked && "opacity-40 pointer-events-none"
                  )}
                >
                  <Icon className={cn("w-4 h-4", active ? "text-primary" : "text-slate-400")} />
                  <span className="flex-1">{item.label}</span>
                  {item.status && (
                    <span className={cn("w-2 h-2 rounded-full", STATUS_DOT[item.status] ?? "bg-slate-300")} />
                  )}
                </Link>
              )
            })}
          </nav>
        </>
      )}
    </>
  )
}
