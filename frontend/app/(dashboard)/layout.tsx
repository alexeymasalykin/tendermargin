import { cookies } from "next/headers"
import { redirect } from "next/navigation"
import { TopBar } from "@/components/layout/TopBar"
import { Sidebar } from "@/components/layout/Sidebar"
import { ErrorBoundary } from "@/components/ErrorBoundary"

async function getUser() {
  const cookieStore = await cookies()
  const token = cookieStore.get("access_token")
  if (!token) return null
  try {
    const res = await fetch("http://fastapi:8000/api/v1/auth/me", {
      headers: { Cookie: `access_token=${token.value}` },
      cache: "no-store",
    })
    if (!res.ok) return null
    return res.json()
  } catch { return null }
}

export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const user = await getUser()
  if (!user) redirect("/login")
  return (
    <div className="min-h-dvh flex flex-col">
      <TopBar userName={user.name} />
      <div className="flex flex-1">
        <Sidebar />
        <main id="main-content" className="flex-1 p-4 sm:p-6 overflow-auto">
          <ErrorBoundary>{children}</ErrorBoundary>
        </main>
      </div>
    </div>
  )
}
