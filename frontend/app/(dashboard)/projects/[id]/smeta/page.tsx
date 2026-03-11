import { cookies } from "next/headers"
import { SmetaUpload } from "@/components/smeta/SmetaUpload"
import { SmetaTable } from "@/components/smeta/SmetaTable"
import { Breadcrumbs } from "@/components/layout/Breadcrumbs"

async function getSmetaItems(projectId: string) {
  const cookieStore = await cookies()
  const token = cookieStore.get("access_token")
  const res = await fetch(
    `http://fastapi:8000/api/v1/projects/${projectId}/smeta/items?size=200`,
    { headers: { Cookie: `access_token=${token?.value}` }, cache: "no-store" }
  )
  if (!res.ok) return { items: [], total: 0 }
  return res.json()
}

export default async function SmetaPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params
  const { items, total } = await getSmetaItems(id)

  return (
    <div>
      <Breadcrumbs crumbs={[
        { label: "Проекты", href: "/dashboard" },
        { label: "Обзор", href: `/projects/${id}` },
        { label: "Смета" },
      ]} />
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Смета</h1>
        {total > 0 && <span className="text-sm text-muted-foreground">{total} позиций</span>}
      </div>

      {total === 0 ? (
        <SmetaUpload projectId={id} />
      ) : (
        <div className="space-y-4">
          <SmetaTable items={items} />
          <details className="text-sm">
            <summary className="cursor-pointer text-muted-foreground hover:text-foreground">
              Загрузить новую смету
            </summary>
            <div className="mt-3 p-4 border border-warning/50 rounded-lg bg-warning/5">
              <p className="text-sm text-warning mb-3">
                Загрузка новой сметы удалит все текущие данные: расценки, прайсы, результат.
              </p>
              <SmetaUpload projectId={id} />
            </div>
          </details>
        </div>
      )}
    </div>
  )
}
