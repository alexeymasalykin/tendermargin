import Link from "next/link"
import { ChevronRight } from "lucide-react"

interface Crumb { label: string; href?: string }

export function Breadcrumbs({ crumbs }: { crumbs: Crumb[] }) {
  return (
    <nav aria-label="Breadcrumb" className="flex items-center gap-1 text-sm text-muted-foreground mb-6">
      {crumbs.map((crumb, i) => (
        <span key={i} className="flex items-center gap-1">
          {i > 0 && <ChevronRight className="w-3 h-3" />}
          {crumb.href
            ? <Link href={crumb.href} className="hover:text-foreground transition-colors">{crumb.label}</Link>
            : <span className="text-foreground font-medium">{crumb.label}</span>}
        </span>
      ))}
    </nav>
  )
}
