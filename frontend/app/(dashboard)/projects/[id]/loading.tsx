import { Skeleton } from "@/components/ui/skeleton"
import { TableSkeleton } from "@/components/skeletons/TableSkeleton"

export default function Loading() {
  return (
    <div className="space-y-6">
      <Skeleton className="h-8 w-64" />
      <div className="grid gap-4 sm:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Skeleton key={i} className="h-24 rounded-xl" />
        ))}
      </div>
      <TableSkeleton rows={8} cols={6} />
    </div>
  )
}
