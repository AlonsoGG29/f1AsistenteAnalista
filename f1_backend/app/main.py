from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from sqlalchemy import text
from app.config import settings
from app.db.session import engine
from app.routers import queries, analysis
from app.services.ml_service import ml_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: verificar conexión a BD
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: c.execute(text("SELECT 1")))
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


# ── ML Predictions ───────────────────────────────────────────────────────────
@app.get("/api/predict/status", tags=["Predicciones ML"])
async def model_status():
    """Estado de carga de los modelos ML"""
    return {
        "safety_car": {"loaded": 'sc' in ml_service.models},
        "pit_stop": {"loaded": 'pit' in ml_service.models},
        "tyre_strategy": {"loaded": 'tyre' in ml_service.models},
    }


@app.post("/api/predict/safety-car", tags=["Predicciones ML"])
async def predict_safety_car(payload: dict):
    """Predicción de Safety Car"""
    return ml_service.predict_safety_car(payload)


@app.post("/api/predict/pit-stop", tags=["Predicciones ML"])
async def predict_pit_stop(payload: dict):
    """Predicción de Parada en Boxes"""
    return ml_service.predict_pit_stop(payload)


@app.post("/api/predict/tyre-strategy", tags=["Predicciones ML"])
async def predict_tyre_strategy(payload: dict):
    """Recomendación de Neumáticos"""
    return ml_service.predict_tyre_strategy(payload)


@app.post("/api/predict/mechanical-failure", tags=["Predicciones ML"])
async def predict_mechanical_failure(payload: dict):
    """Predicción de falla mecánica (Mock por ahora)"""
    return {"probability": 0.05, "label": False, "confidence": "baja"}


@app.post("/api/predict/podium", tags=["Predicciones ML"])
async def predict_podium(payload: dict):
    """Predicción de podium (Mock por ahora)"""
    return {"probability": 0.15, "label": False, "confidence": "media"}


@app.get("/health", tags=["Sistema"])
async def health_check():
    return {"status": "ok", "version": "1.0.0", "env": settings.APP_ENV}
