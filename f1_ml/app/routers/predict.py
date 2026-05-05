"""
app/routers/predict.py
━━━━━━━━━━━━━━━━━━━━━━
Endpoints de predicción ML. Todos son POST para aceptar el
objeto de features en el body.

Añadir al main.py existente:
    from app.routers import predict
    app.include_router(predict.router)
"""
from fastapi import APIRouter, HTTPException
from app.schemas.ml_schemas import (
    SafetyCarRequest, MechanicalFailureRequest, PodiumRequest,
    PredictionResponse, ModelStatusResponse, FeatureImportanceResponse,
)
from app.services.ml_service import (
    SafetyCarInput, MechanicalFailureInput, PodiumInput,
    predict_safety_car, predict_mechanical_failure, predict_podium,
    get_model_status, get_feature_importance,
    PredictionResult,
)

router = APIRouter(prefix="/api/predict", tags=["Predicciones ML"])


def _to_response(result: PredictionResult) -> PredictionResponse:
    return PredictionResponse(
        probability=result.probability,
        label=result.label,
        threshold=result.threshold,
        confidence=result.confidence,
        model_auc=result.model_auc,
        features_used=result.features_used,
    )


# ── Estado de los modelos ─────────────────────────────────────────────────────

@router.get(
    "/status",
    response_model=ModelStatusResponse,
    summary="Estado de carga de los modelos ML",
    description=(
        "Comprueba si los modelos están cargados y disponibles. "
        "Si un modelo muestra `loaded: false`, hay que entrenar primero "
        "con `python scripts/train_models.py`."
    ),
)
async def model_status():
    return get_model_status()


@router.get(
    "/feature-importance/{model}",
    response_model=FeatureImportanceResponse,
    summary="Importancia de features de un modelo",
)
async def feature_importance(model: str):
    valid = {"safety_car", "mechanical_failure", "position"}
    if model not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Modelo inválido. Opciones: {', '.join(valid)}",
        )
    importance = get_feature_importance(model)
    if not importance:
        raise HTTPException(
            status_code=503,
            detail=f"Modelo '{model}' no disponible o sin datos de importancia",
        )
    return FeatureImportanceResponse(model=model, importance=importance)


# ── Safety Car ────────────────────────────────────────────────────────────────

@router.post(
    "/safety-car",
    response_model=PredictionResponse,
    summary="Probabilidad de Safety Car en una carrera",
    description=(
        "Predice la probabilidad de que aparezca un Safety Car (o VSC) "
        "en una carrera dados los parámetros del circuito e historial. "
        "Los valores de `country_sc_rate`, `circuit_sc_rate_*` y `n_pit_stops` "
        "puedes obtenerlos del endpoint `/api/analysis/circuits/{id}/stats`."
    ),
)
async def predict_sc(body: SafetyCarRequest):
    try:
        inp = SafetyCarInput(**body.model_dump())
        result = predict_safety_car(inp)
        return _to_response(result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ── Fallo mecánico ────────────────────────────────────────────────────────────

@router.post(
    "/mechanical-failure",
    response_model=PredictionResponse,
    summary="Probabilidad de fallo mecánico de un piloto",
    description=(
        "Predice la probabilidad de que un piloto sufra un DNF por avería mecánica. "
        "Puedes consultar `driver_dnf_rate_*` y `constructor_dnf_rate_5r` "
        "desde el endpoint `/api/analysis/drivers/{id}/season-stats`. "
        "El threshold por defecto es 0.3 (más conservador que 0.5)."
    ),
)
async def predict_dnf(body: MechanicalFailureRequest):
    try:
        inp = MechanicalFailureInput(**body.model_dump())
        result = predict_mechanical_failure(inp)
        return _to_response(result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))


# ── Podio ─────────────────────────────────────────────────────────────────────

@router.post(
    "/podium",
    response_model=PredictionResponse,
    summary="Probabilidad de podio de un piloto",
    description=(
        "Predice la probabilidad de que un piloto termine en el top 3. "
        "Los valores de historial de podio se pueden calcular con "
        "`/api/analysis/drivers/{id}/season-stats` y "
        "`/api/analysis/head-to-head`."
    ),
)
async def predict_pos(body: PodiumRequest):
    try:
        inp = PodiumInput(**body.model_dump())
        result = predict_podium(inp)
        return _to_response(result)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
