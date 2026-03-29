# TenderMargin

SaaS-калькулятор маржинальности строительных тендеров. Парсит сметы (ГРАНД-Смета Excel/PDF), сопоставляет с ценами подрядчиков и поставщиков через AI-маппинг, рассчитывает маржу по каждой позиции.

## Возможности

- **Парсинг смет** — загрузка файлов ГРАНД-Сметы (Excel/PDF), автоматическое извлечение позиций
- **Расценки подрядчика** — ручной ввод или массовая загрузка прайс-листа
- **AI-сопоставление** — маппинг позиций поставщика к позициям сметы через OpenRouter LLM
- **Расчёт маржи** — анализ «потолок vs себестоимость» по каждой позиции с цветовой индикацией
- **Экспорт в Excel** — детальный отчёт по маржинальности

## Стек

| Слой | Технологии |
|------|-----------|
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, SQLAlchemy (async), Pydantic |
| БД | PostgreSQL 16 |
| AI | OpenRouter API (GPT-4o / Claude) |
| Деплой | Docker Compose, Nginx |

## Архитектура

```
┌─────────────┐     ┌──────────────┐     ┌──────────────┐
│   Браузер    │────▶│   Nginx :80  │     │              │
│             │◀────│  (reverse    │     │  PostgreSQL  │
└─────────────┘     │   proxy)     │     │    :5432     │
                    └──────┬───────┘     └──────▲───────┘
                           │                    │
                    ┌──────▼───────┐     ┌──────┴───────┐
                    │  Next.js     │     │   FastAPI    │
                    │  :3001       │────▶│   :8000      │
                    │              │     │              │
                    │  App Router  │     │  SQLAlchemy  │
                    │  shadcn/ui   │     │  Pydantic    │
                    │  TypeScript  │     │  JWT Auth    │
                    └──────────────┘     └──────────────┘
                                              │
                                        ┌─────▼──────┐
                                        │ OpenRouter  │
                                        │  (AI API)   │
                                        └────────────┘
```

### Поток данных

1. **Загрузка** — пользователь загружает файл ГРАНД-Сметы (Excel/PDF)
2. **Парсинг** — backend извлекает позиции, материалы, коды работ
3. **Расценки** — подрядчик заполняет цены; загружается прайс поставщика
4. **Сопоставление** — AI маппит позиции поставщика к материалам сметы (OpenRouter)
5. **Расчёт** — маржа = потолок тендера − себестоимость подрядчика по каждой позиции
6. **Экспорт** — Excel-отчёт с цветовой индикацией маржинальности

## Быстрый старт

```bash
# 1. Клонировать
git clone https://github.com/alex2061/tendermargin.git
cd tendermargin

# 2. Настроить
cp .env.example .env
# Отредактировать .env — задать DB_PASSWORD, JWT_SECRET, OPENROUTER_API_KEY

# 3. Запустить
docker compose up --build -d

# Frontend: http://localhost:3001
# API docs: http://localhost:8000/api/docs
```

## Структура проекта

```
backend/         FastAPI-приложение
  app/
    routers/     HTTP-эндпоинты
    services/    Бизнес-логика
    models/      SQLAlchemy-модели (async)
    schemas/     Pydantic request/response DTO
  alembic/       Миграции БД
  tests/         pytest (async, in-memory SQLite)

frontend/        Next.js 16 приложение
  app/           App Router — страницы
  components/    React-компоненты (shadcn/ui)
  lib/api/       API-клиент по модулям
  types/         TypeScript-интерфейсы

core/            Python-парсеры (Excel/PDF)
```

## Разработка

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v        # Тесты (48 тестов, 72% coverage)
uvicorn app.main:app --reload     # Dev-сервер :8000

# Frontend
cd frontend
npm install
npm run dev                       # Dev-сервер :3000
npm run build                     # Production-сборка
npm test                          # Vitest
```

## API

Интерактивная документация доступна по адресу `/api/docs` (Swagger UI) при запущенном backend.

## Лицензия

MIT
