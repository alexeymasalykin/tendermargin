"use client"
import { useState, useCallback } from "react"
import { useRouter } from "next/navigation"
import { Upload, FileSpreadsheet, FileText } from "lucide-react"
import { api } from "@/lib/api"
import { cn } from "@/lib/utils"

export const ITEM_TYPE_COLORS: Record<string, string> = {
  work: "border-l-primary",
  material: "border-l-success",
  equipment: "border-l-warning",
  mechanism: "border-l-muted-foreground",
}

export function SmetaUpload({ projectId }: { projectId: string }) {
  const router = useRouter()
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleFile(file: File) {
    const ext = file.name.split(".").pop()?.toLowerCase()
    if (!["xlsx", "xls", "pdf"].includes(ext ?? "")) {
      setError("Поддерживаются: .xlsx, .xls, .pdf")
      return
    }
    setUploading(true)
    setError(null)
    try {
      await api.smeta.upload(projectId, file)
      router.refresh()
    } catch (e: any) {
      setError(e.detail ?? "Ошибка загрузки")
    } finally {
      setUploading(false)
    }
  }

  const onDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }, [projectId])

  return (
    <div>
      <label
        htmlFor="smeta-upload"
        onDragOver={e => { e.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={onDrop}
        className={cn(
          "flex flex-col items-center justify-center border-2 border-dashed rounded-lg p-12 cursor-pointer transition-colors",
          dragging ? "border-primary bg-primary/5" : "border-border hover:border-primary/50"
        )}
      >
        <Upload className="w-8 h-8 text-muted-foreground mb-3" />
        <p className="text-sm font-medium">Перетащите смету или нажмите</p>
        <p className="text-xs text-muted-foreground mt-1">ГРАНД-Смета Excel, PDF до 200 МБ</p>
        <div className="flex gap-2 mt-4">
          <FileSpreadsheet className="w-4 h-4 text-success" />
          <span className="text-xs text-muted-foreground">.xlsx / .xls</span>
          <FileText className="w-4 h-4 text-destructive" />
          <span className="text-xs text-muted-foreground">.pdf</span>
        </div>
      </label>
      <input
        id="smeta-upload"
        type="file"
        accept=".xlsx,.xls,.pdf"
        className="sr-only"
        onChange={e => { const f = e.target.files?.[0]; if (f) handleFile(f) }}
        disabled={uploading}
      />
      {error && <p className="text-sm text-destructive mt-2">{error}</p>}
      {uploading && <p className="text-sm text-muted-foreground mt-2">Парсинг файла...</p>}
    </div>
  )
}
