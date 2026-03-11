import { LoginForm } from "@/components/auth/LoginForm"
import Link from "next/link"

export default function LoginPage() {
  return (
    <div className="w-full max-w-sm space-y-6 p-6 bg-surface rounded-xl shadow-card border border-border">
      <div>
        <h1 className="text-2xl font-semibold">Войти</h1>
        <p className="text-sm text-muted-foreground mt-1">TenderMargin</p>
      </div>
      <LoginForm />
      <p className="text-sm text-center text-muted-foreground">
        Нет аккаунта?{" "}
        <Link href="/register" className="text-primary hover:underline">Зарегистрироваться</Link>
      </p>
    </div>
  )
}
