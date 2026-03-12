import { cookies } from "next/headers"
import { Breadcrumbs } from "@/components/layout/Breadcrumbs"
import { MaterialsTable } from "@/components/materials/MaterialsTable"
import type { Material } from "@/types/api"

async function getMaterials(projectId: string): Promise<Material[]> {
  const cookieStore = await cookies()
  const token = cookieStore.get("access_token")
  const res = await fetch(`http://fastapi:8000/api/v1/projects/${projectId}/materials`, {
    headers: { Cookie: `access_token=${token?.value}` },
    cache: "no-store",
  })
  if (!res.ok) return []
  return res.json()
}

export default async function MaterialsPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const materials = await getMaterials(id)
  const filled = materials.filter(m => m.supplier_price != null).length

  return (
    <div>
      <Breadcrumbs crumbs={[
        { label: "Проекты", href: "/dashboard" },
        { label: "Обзор", href: `/projects/${id}` },
        { label: "Материалы" },
      ]} />
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-semibold">Материалы</h1>
          {materials.length > 0 && (
            <p className="text-sm text-muted-foreground mt-0.5">
              Цены: {filled}/{materials.length} заполнено
            </p>
          )}
        </div>
      </div>

      {materials.length === 0 ? (
        <p className="text-muted-foreground text-sm">Загрузите смету для формирования ведомости материалов</p>
      ) : (
        <MaterialsTable data={materials} projectId={id} />
      )}
    </div>
  )
}
