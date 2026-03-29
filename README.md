# TenderMargin

A SaaS margin calculator for construction tenders. Parses cost estimates (GRAND-Smeta Excel/PDF), matches them against contractor and supplier prices using AI mapping, and calculates per-item margins.

## Features

- **Estimate parsing** — Upload GRAND-Smeta files (Excel/PDF), auto-extract line items
- **Contractor pricing** — Manual entry or bulk upload of contractor price lists
- **AI-powered matching** — Map supplier prices to estimate items via OpenRouter LLM
- **Margin calculation** — Per-item ceiling vs. cost analysis with color-coded status
- **Excel export** — Download detailed margin reports

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 16 (App Router), TypeScript, Tailwind CSS, shadcn/ui |
| Backend | FastAPI, SQLAlchemy (async), Pydantic |
| Database | PostgreSQL 16 |
| AI | OpenRouter API (GPT-4o / Claude) |
| Deploy | Docker Compose, Nginx |

## Quick Start

```bash
# 1. Clone
git clone https://github.com/alex2061/tendermargin.git
cd tendermargin

# 2. Configure
cp .env.example .env
# Edit .env — set DB_PASSWORD, JWT_SECRET, OPENROUTER_API_KEY

# 3. Run
docker compose up --build -d

# Frontend: http://localhost:3001
# API docs: http://localhost:8000/api/docs
```

## Project Structure

```
backend/         FastAPI application
  app/
    routers/     HTTP endpoints
    services/    Business logic
    models/      SQLAlchemy models (async)
    schemas/     Pydantic request/response DTOs
  alembic/       Database migrations
  tests/         pytest (async, in-memory SQLite)

frontend/        Next.js 16 application
  app/           App Router pages
  components/    React components (shadcn/ui)
  lib/api/       API client modules
  types/         TypeScript interfaces

core/            Python parsers (Excel/PDF)
```

## Development

```bash
# Backend
cd backend
pip install -r requirements.txt
python -m pytest tests/ -v        # Run tests
uvicorn app.main:app --reload     # Dev server :8000

# Frontend
cd frontend
npm install
npm run dev                       # Dev server :3000
npm run build                     # Production build
npm test                          # Vitest
```

## API Documentation

Interactive API docs available at `/api/docs` (Swagger UI) when the backend is running.

## License

MIT
