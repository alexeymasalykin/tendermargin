"use client"
import { useState } from "react"
import { useRouter } from "next/navigation"
import { Upload, Search, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { api } from "@/lib/api"
import { cn } from "@/lib/utils"

type Step = "upload" | "detect" | "map"

const STEPS: { id: Step; label: string; icon: React.ElementType }[] = [
  { id: "upload", label: "Загрузка", icon: Upload },
  { id: "detect", label: "Структура", icon: Search },
  { id: "map", label: "Маппинг", icon: CheckCircle2 },
]

export function PricelistWizard({ projectId }: { projectId: string }) {
  const router = useRouter()
  const [step, setStep] = useState<Step>("upload")
  const [uploading, setUploading] = useState(false)
  const [detecting, setDetecting] = useState(false)
  const [mapping, setMapping] = useState(false)
  const [progress, setProgress] = useState<{ done: number; total: number } | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [structure, setStructure] = useState<any>(null)
  const [taskId, setTaskId] = useState<string | null>(null)

  async function handleFile(file: File) {
    setUploading(true)
    setError(null)
    try {
      await api.pricelist.upload(projectId, file)
      setStep("detect")
      setUploading(false)
      setDetecting(true)
      const s = await api.pricelist.detectStructure(projectId)
      setStructure(s)
      setDetecting(false)
    } catch (e: any) {
      setError(e.detail ?? "Ошибка загрузки")
      setUploading(false)
      setDetecting(false)
    }
  }

  async function handleMap() {
    setMapping(true)
    setError(null)
    try {
      const result = await api.pricelist.map(projectId, structure ?? {})
      const tid = result.task_id
      setTaskId(tid)
      const poll = setInterval(async () => {
        try {
          const s = await api.pricelist.mapStatus(projectId, tid)
          setProgress({ done: s.progress, total: s.total })
          if (s.status === "completed") {
            clearInterval(poll)
            setMapping(false)
            setStep("map")
            router.refresh()
          }
        } catch {
          clearInterval(poll)
          setMapping(false)
          setError("Ошибка получения статуса")
        }
      }, 2000)
    } catch (e: any) {
      setError(e.detail ?? "Ошибка маппинга")
      setMapping(false)
    }
  }

  const stepIdx = STEPS.findIndex(s => s.id === step)

  return (
    <div className="max-w-2xl space-y-6">
      <div className="flex items-center gap-2">
        {STEPS.map((s, i) => {
          const done = i < stepIdx
          const active = i === stepIdx
          const Icon = s.icon
          return (
            <div key={s.id} className="flex items-center gap-2">
              <div className={cn(
                "flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium",
                active ? "bg-primary text-primary-foreground"
                : done ? "bg-success/10 text-success"
                : "bg-muted text-muted-foreground"
              )}>
                <Icon className="w-4 h-4" />
                {s.label}
              </div>
              {i < STEPS.length - 1 && <span className="text-muted-foreground">→</span>}
            </div>
          )
        })}
      </div>

      {step === "upload" && (
        <label className={cn(
          "flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-12 cursor-pointer transition-colors",
          "border-border hover:border-primary/50"
        )}>
          <Upload className="w-8 h-8 text-muted-foreground mb-3" />
          <p className="text-sm font-medium">Загрузите прайс поставщика (.xlsx)</p>
          <input
            type="file" accept=".xlsx,.xls" className="sr-only"
            onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
            disabled={uploading}
          />
          {uploading && <p className="text-xs text-muted-foreground mt-2">Загрузка...</p>}
        </label>
      )}

      {step === "detect" && (
        <div className="space-y-4">
          {detecting && <p className="text-sm text-muted-foreground">Анализ структуры...</p>}
          {structure && !detecting && (
            <>
              <p className="text-sm font-medium">Определена структура прайса:</p>
              <pre className="text-xs bg-muted p-4 rounded-lg overflow-auto">
                {JSON.stringify(structure, null, 2)}
              </pre>
              <Button onClick={handleMap} disabled={mapping}>
                {mapping ? "Запуск маппинга..." : "Запустить маппинг"}
              </Button>
            </>
          )}
          {mapping && progress && (
            <div className="space-y-1">
              <p className="text-sm text-muted-foreground">Анализ: {progress.done}/{progress.total}</p>
              <Progress value={(progress.done / progress.total) * 100} className="h-2" />
            </div>
          )}
        </div>
      )}

      {step === "map" && (
        <p className="text-sm text-success">✓ Маппинг завершён. Проверьте результаты ниже.</p>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}
    </div>
  )
}
