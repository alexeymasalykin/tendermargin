# TenderMargin — CLAUDE.md

## Project Overview

TenderMargin — SaaS-калькулятор маржинальности строительных тендеров.
Парсит сметы (ГРАНД-Смета Excel/PDF), сопоставляет с ценами подрядчиков и поставщиков (AI-маппинг через OpenRouter), рассчитывает маржу по каждой позиции.

**Stack:** Next.js 16 (App Router) + FastAPI + PostgreSQL 16
**Deploy:** Docker Compose на Ubuntu 24.04, системный nginx на порту 80

## Quick Start

```bash
# Запуск (всё через Docker)
docker compose up --build -d

# Frontend: http://localhost:3001
# Backend API: http://localhost:8000/api/v1
# Swagger: http://localhost:8000/docs
```

## Project Structure

```
backend/
  app/
    main.py           # FastAPI app entry point
    config.py          # Pydantic Settings (.env)
    database.py        # AsyncSession, Base model
    deps.py            # get_current_user (JWT from cookie)
    models/            # SQLAlchemy models
    schemas/           # Pydantic request/response
    routers/           # HTTP endpoints
    services/          # Business logic
  alembic/             # DB migrations
  entrypoint.sh        # alembic upgrade head → uvicorn
  tests/               # pytest (async, in-memory SQLite)

frontend/
  app/
    page.tsx           # Landing page
    (public)/          # /login, /register
    (dashboard)/       # Protected routes
      dashboard/       # Projects list
      projects/[id]/   # Project detail (smeta, materials, contractor, pricelist, result)
      settings/        # User settings
  components/
    ui/                # shadcn/ui (Button, Card, Dialog, Table, etc.)
    auth/              # LoginForm, RegisterForm
    projects/          # ProjectCard, CreateProjectDialog, ProgressStep, MetricCard
    contractor/        # ContractorTable
    pricelist/         # PricelistWizard, MappingTable
    result/            # ResultTable, MarginChart
    layout/            # TopBar, Sidebar, Breadcrumbs, MobileNav
    tables/            # DataTable (generic TanStack Table wrapper)
    smeta/             # SmetaTable, SmetaUpload
  hooks/
    useContractorPrices.ts  # Debounced auto-save + local calculations
  lib/
    api.ts             # Centralized API client (fetch + credentials: include)
    utils.ts           # formatCurrency, formatPercent, cn()
  types/
    api.ts             # TypeScript interfaces
  middleware.ts        # Auth redirect (cookie check)

core/                  # Legacy Python parsers (used by backend services)
docker-compose.yml
```

## Key Commands

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m pytest tests/              # 51 test
uvicorn app.main:app --reload        # Dev server :8000

# Frontend
cd frontend
npm install
npm run dev                          # Dev server :3000
npm run build                        # Production build
npm test                             # Vitest (7 tests)

# Docker
docker compose up --build -d         # Build & run all
docker compose build nextjs          # Rebuild frontend only
docker compose logs -f nextjs        # Watch logs
```

## Environment Variables

File: `.env` (root). Copy from `.env.example`.

```
DB_USER=tendermargin
DB_PASSWORD=          # Set a strong password
DB_NAME=tendermargin
DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@postgres:5432/${DB_NAME}
JWT_SECRET=           # Generate: openssl rand -hex 32
OPENROUTER_API_KEY=   # Get from https://openrouter.ai/keys
```

**Never commit `.env`** — only `.env.example` with placeholder values.

## API Endpoints

Base: `/api/v1`

| Group | Method | Path | Notes |
|-------|--------|------|-------|
| Auth | POST | `/auth/register` | → UserResponse + httponly cookies |
| Auth | POST | `/auth/login` | → UserResponse + httponly cookies |
| Auth | POST | `/auth/refresh` | Rotate refresh token |
| Auth | POST | `/auth/logout` | 204, `response_model=None` |
| Auth | GET | `/auth/me` | Current user |
| Projects | GET/POST | `/projects` | List / Create |
| Projects | GET/PUT/DELETE | `/projects/{id}` | Detail / Update / Delete (204) |
| Smeta | POST | `/projects/{id}/smeta/upload` | Excel/PDF upload |
| Smeta | GET | `/projects/{id}/smeta/items` | Paginated, filterable |
| Materials | GET | `/projects/{id}/materials` | Aggregated list |
| Materials | POST | `/projects/{id}/materials/export` | Excel download |
| Contractor | GET | `/projects/{id}/contractor-prices` | Price list |
| Contractor | PUT | `/projects/{id}/contractor-prices` | Batch update |
| Pricelist | POST | `/projects/{id}/pricelist/upload` | Supplier file |
| Pricelist | POST | `/projects/{id}/pricelist/map` | → `{task_id}` (async AI) |
| Pricelist | GET | `/projects/{id}/pricelist/map/status` | `?task_id=...` |
| Margin | GET | `/projects/{id}/margin` | Full calculation |
| Margin | POST | `/projects/{id}/margin/export` | Excel with colors |
| Health | GET | `/health` | `{status: "ok"}` |

## Architecture Patterns

### Auth
- JWT в httponly cookies (access 15 min + refresh 7 days)
- `middleware.ts` редиректит неавторизованных с dashboard → /login
- `deps.py:get_current_user` — dependency для всех защищённых роутов
- `api.ts` всегда передаёт `credentials: "include"`

### Backend
- **Routers** → HTTP layer only, делегируют в **Services**
- **Services** → Business logic, работают с ORM
- **Models** → SQLAlchemy async, `Mapped[]` type hints
- 204 endpoints require explicit `response_model=None` (FastAPI 0.115.5)
- Decimal types for money (no float)
- Cascade deletes: re-upload smeta → deletes old items, materials, matches

### Frontend
- Server Components by default (async data fetching)
- `"use client"` only for interactive components (forms, hover, state)
- `params` is `Promise` in Next.js 15+ — always `await params`
- `cookies()` must be awaited in server components
- UI library: `@base-ui/react/dialog` (NOT Radix) — use `render={<Button />}`, not `asChild`
- Toasts: Sonner
- Tables: TanStack Table v8 via `DataTable` generic component

### Margin Calculation
- `ceiling` = SmetaItem.total_price (тендерная цена)
- `cost` = ContractorPrice.price × quantity
- `margin` = ceiling − cost
- `margin_pct` = (margin / ceiling) × 100
- Status: `green` (≥15%), `yellow` (5–15%), `red` (0–5%), `loss` (<0%)

### Field Names (backend ↔ frontend)
- `ceiling_total` (NOT `ceiling_price`)
- `supplier_total` (NOT `supplier_sum`)
- Status `"loss"` (NOT `"darkred"`)
- `PricelistMatch` has no `material_name` field
- `api.pricelist.map()` requires `structure` arg
- `api.pricelist.mapStatus()` requires `task_id` arg

## Deployment

- System nginx on port 80 → proxy to `localhost:3001` (Next.js) and `localhost:8000` (FastAPI)
- Nginx config: `/etc/nginx/sites-enabled/tendermargin`
- Docker containers: `nextjs` (3001→3000), `fastapi` (8000→8000), `postgres` (5432)
- Alembic migrations run automatically on container start (`entrypoint.sh`)
- Production: `http://YOUR_SERVER_IP`

## Testing

```bash
# Backend (51 tests, async, in-memory SQLite)
cd backend && python -m pytest tests/ -v

# Frontend (7 tests, Vitest + jsdom)
cd frontend && npm test
```

Backend fixtures: `db_engine`, `db_session`, `client`, `auth_client` (conftest.py).

## Design System

- **Style:** Soft UI with clean data focus
- **Font:** Fira Sans (body) + Fira Code (monospace/data)
- **Colors:** Primary `#2563EB`, Text `#1E293B`, Background `#F8FAFC`
- **Icons:** Lucide React (no emoji as icons)
- **Shadows:** CSS custom properties (`--shadow-sm`, `--shadow-md`, `--shadow-lg`)
- **Border radius:** `0.625rem` (10px)
- **Responsive breakpoints:** 375 / 768 / 1024 / 1440

## Common Gotchas

1. **Port 80 occupied** — system nginx runs on 80, Docker nginx removed from compose
2. **FastAPI 204 error** — `AssertionError: Status code 204 must not have a response body` → add `response_model=None`
3. **Next.js 15 params** — `params: Promise<{id: string}>`, must `await`
4. **Dialog component** — `@base-ui/react`, NOT Radix. Pattern: `<DialogTrigger render={<Button />}>`
5. **Docker build OOM** — VPS has limited RAM, rebuild one service at a time: `docker compose build nextjs`
6. **Font import** — Google Fonts `@import` in `globals.css`, `font-display: swap`
