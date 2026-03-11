"use client"
import { LogOut, User, BarChart2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { api } from "@/lib/api"
import { useRouter } from "next/navigation"
import { MobileNav } from "./MobileNav"

interface TopBarProps {
  userName: string
  mobileNavItems?: { label: string; href: string; icon: "LayoutDashboard" | "Settings" | "BarChart2" | "FileText" | "Package" | "Wrench" | "ShoppingCart"; status?: string }[]
}

export function TopBar({ userName, mobileNavItems }: TopBarProps) {
  const router = useRouter()
  async function handleLogout() {
    await api.auth.logout()
    router.push("/login")
  }
  return (
    <header className="h-14 border-b border-border bg-surface/95 backdrop-blur-sm flex items-center px-4 sm:px-6 gap-3 sm:gap-4 sticky top-0 z-40 shadow-card">
      <MobileNav items={mobileNavItems} />
      <a href="/dashboard" className="flex items-center gap-2 mr-auto group">
        <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center shadow-sm">
          <BarChart2 className="w-4 h-4 text-white" />
        </div>
        <span className="font-semibold text-foreground text-[15px] tracking-tight">TenderMargin</span>
      </a>
      <span className="text-sm text-muted-foreground items-center gap-1.5 hidden sm:flex">
        <span className="w-6 h-6 rounded-full bg-primary/10 flex items-center justify-center">
          <User className="w-3.5 h-3.5 text-primary" />
        </span>
        {userName}
      </span>
      <Button variant="ghost" size="sm" onClick={handleLogout} className="text-muted-foreground hover:text-foreground">
        <LogOut className="w-4 h-4 sm:mr-1.5" />
        <span className="hidden sm:inline">Выход</span>
      </Button>
    </header>
  )
}
