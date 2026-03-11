from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth
from app.routers import projects as projects_router
from app.routers import smeta as smeta_router
from app.routers import materials as materials_router
from app.routers import contractor as contractor_router
from app.routers import pricelist as pricelist_router
from app.routers import margin as margin_router

app = FastAPI(
    title="TenderMargin API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(projects_router.router, prefix="/api/v1")
app.include_router(smeta_router.router, prefix="/api/v1")
app.include_router(materials_router.router, prefix="/api/v1")
app.include_router(contractor_router.router, prefix="/api/v1")
app.include_router(pricelist_router.router, prefix="/api/v1")
app.include_router(margin_router.router, prefix="/api/v1")


@app.get("/api/v1/health")
async def health() -> dict:
    return {"status": "ok"}
