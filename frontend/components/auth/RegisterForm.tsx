"use client"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import { z } from "zod"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { api } from "@/lib/api"
import { useState } from "react"

const schema = z.object({
  name: z.string().min(2, "Минимум 2 символа"),
  email: z.string().min(1, "Введите email").email("Некорректный email"),
  password: z.string().min(8, "Минимум 8 символов"),
  confirm: z.string(),
}).refine(d => d.password === d.confirm, {
  message: "Пароли не совпадают", path: ["confirm"],
})
type FormValues = z.infer<typeof schema>

export function RegisterForm() {
  const router = useRouter()
  const [serverError, setServerError] = useState<string | null>(null)
  const { register, handleSubmit, formState: { errors, isSubmitting } } = useForm<FormValues>({
    resolver: zodResolver(schema),
  })
  async function onSubmit(data: FormValues) {
    try {
      setServerError(null)
      await api.auth.register({ email: data.email, password: data.password, name: data.name })
      router.push("/dashboard")
    } catch (e: unknown) {
      const err = e as { detail?: string }
      setServerError(err.detail ?? "Ошибка регистрации")
    }
  }
  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-4 w-full max-w-sm">
      <div className="space-y-1">
        <Label htmlFor="name">Имя</Label>
        <Input id="name" type="text" autoComplete="name" {...register("name")} />
        {errors.name && <p className="text-xs text-destructive">{errors.name.message}</p>}
      </div>
      <div className="space-y-1">
        <Label htmlFor="email">Email</Label>
        <Input id="email" type="email" autoComplete="email" {...register("email")} />
        {errors.email && <p className="text-xs text-destructive">{errors.email.message}</p>}
      </div>
      <div className="space-y-1">
        <Label htmlFor="password">Пароль</Label>
        <Input id="password" type="password" autoComplete="new-password" {...register("password")} />
        {errors.password && <p className="text-xs text-destructive">{errors.password.message}</p>}
      </div>
      <div className="space-y-1">
        <Label htmlFor="confirm">Подтвердите пароль</Label>
        <Input id="confirm" type="password" autoComplete="new-password" {...register("confirm")} />
        {errors.confirm && <p className="text-xs text-destructive">{errors.confirm.message}</p>}
      </div>
      {serverError && <p className="text-sm text-destructive">{serverError}</p>}
      <Button type="submit" className="w-full" disabled={isSubmitting}>
        {isSubmitting ? "Регистрация..." : "Создать аккаунт"}
      </Button>
    </form>
  )
}
