import Link from "next/link"
import { Button } from "@/components/ui/button"
import { BarChart2, FileSpreadsheet, Zap, ArrowRight, CheckCircle2 } from "lucide-react"

export default function LandingPage() {
  return (
    <div className="min-h-dvh bg-background">
      {/* Header */}
      <header className="border-b border-border/60 bg-surface/95 backdrop-blur-sm sticky top-0 z-40 px-4 sm:px-6 py-3 flex items-center justify-between shadow-card">
        <div className="flex items-center gap-2">
          <div className="w-7 h-7 rounded-lg bg-primary flex items-center justify-center">
            <BarChart2 className="w-4 h-4 text-white" />
          </div>
          <span className="font-bold text-[15px] tracking-tight text-foreground">TenderMargin</span>
        </div>
        <div className="flex gap-2">
          <Link href="/login"><Button variant="ghost" size="sm" className="text-slate-600">Войти</Button></Link>
          <Link href="/register"><Button size="sm" className="bg-accent text-accent-foreground hover:bg-accent/90 shadow-sm hidden sm:inline-flex">Попробовать</Button></Link>
        </div>
      </header>

      {/* Hero */}
      <main>
        <section className="relative overflow-hidden">
          <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-blue-50/30 pointer-events-none" />
          <div className="relative max-w-4xl mx-auto px-4 sm:px-6 py-16 sm:py-24 text-center">
            <div className="inline-flex items-center gap-2 px-3 py-1 bg-primary/10 text-primary rounded-full text-xs sm:text-sm font-medium mb-6 border border-primary/20">
              <Zap className="w-3.5 h-3.5" />
              AI-маппинг прайсов поставщиков
            </div>
            <h1 className="text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight text-foreground mb-5 leading-tight">
              Расчёт маржи<br />
              <span className="text-primary">строительного тендера</span>
            </h1>
            <p className="text-base sm:text-lg text-muted-foreground mb-8 max-w-2xl mx-auto leading-relaxed">
              Загрузите смету ГРАНД-Смета, внесите расценки подрядчика и прайсы поставщиков — получите точный расчёт маржи за секунды.
            </p>
            <div className="flex flex-col sm:flex-row gap-3 justify-center">
              <Link href="/register">
                <Button size="lg" className="gap-2 bg-accent text-accent-foreground hover:bg-accent/90 shadow-md px-6 w-full sm:w-auto">
                  Начать бесплатно
                  <ArrowRight className="w-4 h-4" />
                </Button>
              </Link>
              <Link href="/login">
                <Button variant="outline" size="lg" className="px-6 w-full sm:w-auto">
                  Войти в аккаунт
                </Button>
              </Link>
            </div>
          </div>
        </section>

        {/* Features */}
        <section className="max-w-4xl mx-auto px-4 sm:px-6 pb-16 sm:pb-20">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5">
            {[
              {
                icon: FileSpreadsheet,
                title: "Парсинг сметы",
                desc: "ГРАНД-Смета Excel и PDF автоматически — позиции, типы, разделы",
                color: "bg-blue-50 text-blue-600",
              },
              {
                icon: Zap,
                title: "AI-маппинг прайсов",
                desc: "LLM сопоставляет материалы из сметы с позициями прайса поставщика",
                color: "bg-orange-50 text-orange-600",
              },
              {
                icon: BarChart2,
                title: "Расчёт маржи",
                desc: "Маржа по каждой позиции, себестоимость, цена пол — с визуализацией",
                color: "bg-green-50 text-green-600",
              },
            ].map(({ icon: Icon, title, desc, color }) => (
              <div key={title}
                className="p-5 sm:p-6 rounded-xl border border-border/60 bg-surface transition-colors duration-200 hover:border-primary/30 shadow-card">
                <div className={`w-10 h-10 rounded-xl ${color} flex items-center justify-center mb-4`}>
                  <Icon className="w-5 h-5" />
                </div>
                <h3 className="font-semibold text-foreground mb-2">{title}</h3>
                <p className="text-sm text-muted-foreground leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>

          {/* Trust bullets */}
          <div className="flex flex-col sm:flex-row flex-wrap justify-center gap-x-8 gap-y-2 mt-10 sm:mt-12">
            {["Бесплатно", "Без ограничений проектов", "Данные не передаются третьим лицам"].map(item => (
              <span key={item} className="flex items-center gap-1.5 text-sm text-muted-foreground">
                <CheckCircle2 className="w-4 h-4 text-success shrink-0" />
                {item}
              </span>
            ))}
          </div>
        </section>
      </main>
    </div>
  )
}
