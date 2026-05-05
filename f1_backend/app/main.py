from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.db.session import engine
from app.routers import queries, analysis


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verificar conexión a BD
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: c.execute(c.connection.connection.cursor().execute("SELECT 1")))
    print("✅ Conexión a PostgreSQL establecida")
    yield
    # Shutdown: cerrar pool de conexiones
    await engine.dispose()
    print("🔌 Pool de conexiones cerrado")


app = FastAPI(
    title="F1 Analytics API",
    description=(
        "API REST para análisis de datos de Fórmula 1. "
        "Cubre datos históricos desde 1950 hasta 2024."
    ),
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(queries.router)
app.include_router(analysis.router)


@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "version": "1.0.0", "env": settings.APP_ENV}
