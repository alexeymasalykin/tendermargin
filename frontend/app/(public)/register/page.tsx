import { RegisterForm } from "@/components/auth/RegisterForm"
import Link from "next/link"

export default function RegisterPage() {
  return (
    <div className="w-full max-w-sm space-y-6 p-6 bg-surface rounded-xl shadow-card border border-border">
      <div>
        <h1 className="text-2xl font-semibold">Регистрация</h1>
        <p className="text-sm text-muted-foreground mt-1">TenderMargin</p>
      </div>
      <RegisterForm />
      <p className="text-sm text-center text-muted-foreground">
        Уже есть аккаунт?{" "}
        <Link href="/login" className="text-primary hover:underline">Войти</Link>
      </p>
    </div>
  )
}
