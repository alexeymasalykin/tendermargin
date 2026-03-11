"use client"
import Link from "next/link"
import { Card, CardHeader, CardTitle, CardDescription, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { formatMoney, formatPercent } from "@/lib/utils"
import { TrendingUp, Calendar } from "lucide-react"
import type { ProjectDetail } from "@/types/api"

export function ProjectCard({ project }: { project: ProjectDetail }) {
  const margin = project.progress?.margin
  const smetaDone = project.progress?.smeta?.status !== "not_started"

  return (
    <Link href={`/projects/${project.id}`}>
      <Card className="group hover:border-primary/30 transition-all duration-200 cursor-pointer h-full hover:-translate-y-0.5 shadow-card hover:shadow-card-hover">
        <CardHeader className="pb-3">
          <CardTitle className="text-[15px] font-semibold leading-snug group-hover:text-primary transition-colors duration-200">
            {project.name}
          </CardTitle>
          {project.description && (
            <CardDescription className="line-clamp-2 text-xs mt-1">{project.description}</CardDescription>
          )}
        </CardHeader>
        <CardFooter className="pt-0 flex items-center justify-between gap-2">
          <div className="flex items-center gap-1.5">
            {margin?.available && margin.margin_pct !== undefined ? (
              <Badge
                variant={margin.margin_pct > 15 ? "default" : margin.margin_pct > 5 ? "secondary" : "destructive"}
                className="font-mono text-xs gap-1"
              >
                <TrendingUp className="w-3 h-3" />
                {formatPercent(margin.margin_pct)}
              </Badge>
            ) : smetaDone ? (
              <span className="text-xs text-muted-foreground">Данные не заполнены</span>
            ) : (
              <span className="text-xs text-muted-foreground">Новый проект</span>
            )}
          </div>
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {new Date(project.created_at).toLocaleDateString("ru-RU")}
          </span>
        </CardFooter>
      </Card>
    </Link>
  )
}
