import { Breadcrumbs } from "@/components/layout/Breadcrumbs"

export default function SettingsPage() {
  return (
    <div>
      <Breadcrumbs crumbs={[{ label: "Настройки" }]} />
      <h1 className="text-xl font-semibold mb-6">Настройки профиля</h1>
      <p className="text-sm text-muted-foreground">В разработке</p>
    </div>
  )
}
