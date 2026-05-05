"""
app/services/ml_service.py
━━━━━━━━━━━━━━━━━━━━━━━━━━
Servicio de inferencia. Carga los modelos entrenados al arrancar
la aplicación y expone métodos de predicción para cada caso de uso.

Los modelos se cargan una sola vez (singleton) usando lru_cache.
Si un modelo no está disponible, los endpoints devuelven 503.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Optional

import numpy as np

logger = logging.getLogger(__name__)

# Ruta base donde están los .joblib — ajusta si es necesario
MODELS_DIR = Path(__file__).parent.parent.parent / "models_trained"


@dataclass
class ModelBundle:
    pipeline: object
    features: list[str]
    metrics:  dict
    name:     str
    loaded:   bool = False


@dataclass
class SafetyCarInput:
    """Features para predecir Safety Car en una carrera."""
    year:                   int
    round:                  int
    season_progress:        float   # round / total_rounds (0-1)
    lat:                    float   # latitud del circuito
    lng:                    float   # longitud del circuito
    alt:                    float   # altitud (metros)
    country_sc_rate:        float   # tasa histórica de SC en ese país
    circuit_sc_rate_3y:     float   # tasa SC últimas 3 temporadas en el circuito
    circuit_sc_rate_all:    float   # tasa SC histórica en el circuito
    n_finishers:            float   # pilotos que terminaron últimas ediciones (media)
    n_pit_stops:            float   # pit stops medios en el circuito
    is_modern_era:          int     # 1 si year >= 2011


@dataclass
class MechanicalFailureInput:
    """Features para predecir fallo mecánico de un piloto en una carrera."""
    year:                       int
    round:                      int
    season_progress:            float
    is_modern_era:              int     # 1 si year >= 2014
    grid_position:              int
    laps_completed:             int     # vueltas completadas hasta el momento
    driver_dnf_rate_5r:         float   # tasa DNF mec. últimas 5 carreras del piloto
    driver_dnf_rate_all:        float   # tasa DNF mec. histórica del piloto
    driver_races_count:         int     # total de carreras del piloto
    constructor_dnf_rate_5r:    float   # tasa DNF mec. del equipo últimas 5 carreras


@dataclass
class PodiumInput:
    """Features para predecir probabilidad de podio."""
    year:                       int
    round:                      int
    season_progress:            float
    is_modern_era:              int
    quali_pos:                  int     # posición de clasificación
    driver_podium_rate_5r:      float   # tasa podio últimas 5 carreras
    driver_win_rate_all:        float   # tasa victorias histórica
    driver_avg_pos_5r:          float   # posición media últimas 5 carreras
    constr_podium_rate_5r:      float   # tasa podio del equipo últimas 5
    driver_circuit_podium_rate: float   # tasa podio del piloto en este circuito


@dataclass
class PredictionResult:
    probability: float
    label:       bool
    threshold:   float
    confidence:  str   # "alta" | "media" | "baja"
    model_auc:   Optional[float] = None
    features_used: list[str] = field(default_factory=list)


def _confidence_label(prob: float, threshold: float) -> str:
    distance = abs(prob - threshold)
    if distance > 0.25:
        return "alta"
    if distance > 0.10:
        return "media"
    return "baja"


def _load_bundle(filename: str, name: str) -> ModelBundle:
    path = MODELS_DIR / filename
    if not path.exists():
        logger.warning(f"Modelo '{name}' no encontrado en {path}")
        return ModelBundle(pipeline=None, features=[], metrics={}, name=name, loaded=False)
    try:
        import joblib
        data = joblib.load(path)
        logger.info(f"Modelo '{name}' cargado — AUC CV: {data['metrics'].get('cv_auc_mean', '?'):.4f}")
        return ModelBundle(
            pipeline=data["pipeline"],
            features=data["features"],
            metrics=data["metrics"],
            name=name,
            loaded=True,
        )
    except Exception as e:
        logger.error(f"Error cargando '{name}': {e}")
        return ModelBundle(pipeline=None, features=[], metrics={}, name=name, loaded=False)


@lru_cache(maxsize=1)
def _get_models() -> dict[str, ModelBundle]:
    return {
        "safety_car":          _load_bundle("safety_car_model.joblib",      "Safety Car"),
        "mechanical_failure":  _load_bundle("mechanical_failure_model.joblib", "Fallo Mecánico"),
        "position":            _load_bundle("position_model.joblib",          "Podio"),
    }


def get_model_status() -> dict:
    """Devuelve el estado de carga de todos los modelos."""
    models = _get_models()
    return {
        key: {
            "loaded":    m.loaded,
            "cv_auc":    m.metrics.get("cv_auc_mean"),
            "n_samples": m.metrics.get("n_samples"),
            "backend":   m.metrics.get("backend"),
        }
        for key, m in models.items()
    }


def _predict(bundle: ModelBundle, values: list, threshold: float = 0.5) -> PredictionResult:
    if not bundle.loaded:
        raise RuntimeError(f"Modelo '{bundle.name}' no disponible")
    X = np.array(values, dtype=float).reshape(1, -1)
    prob = float(bundle.pipeline.predict_proba(X)[0, 1])
    return PredictionResult(
        probability=round(prob, 4),
        label=prob >= threshold,
        threshold=threshold,
        confidence=_confidence_label(prob, threshold),
        model_auc=bundle.metrics.get("cv_auc_mean"),
        features_used=bundle.features,
    )


# ── API pública ───────────────────────────────────────────────────────────────

def predict_safety_car(inp: SafetyCarInput, threshold: float = 0.5) -> PredictionResult:
    bundle = _get_models()["safety_car"]
    values = [
        inp.year, inp.round, inp.season_progress,
        inp.lat, inp.lng, inp.alt,
        inp.country_sc_rate, inp.circuit_sc_rate_3y, inp.circuit_sc_rate_all,
        inp.n_finishers, inp.n_pit_stops, inp.is_modern_era,
    ]
    return _predict(bundle, values, threshold)


def predict_mechanical_failure(inp: MechanicalFailureInput, threshold: float = 0.3) -> PredictionResult:
    """Threshold más bajo (0.3) porque el coste de un falso negativo es alto."""
    bundle = _get_models()["mechanical_failure"]
    values = [
        inp.year, inp.round, inp.season_progress, inp.is_modern_era,
        inp.grid_position, inp.laps_completed,
        inp.driver_dnf_rate_5r, inp.driver_dnf_rate_all, inp.driver_races_count,
        inp.constructor_dnf_rate_5r,
    ]
    return _predict(bundle, values, threshold)


def predict_podium(inp: PodiumInput, threshold: float = 0.5) -> PredictionResult:
    bundle = _get_models()["position"]
    values = [
        inp.year, inp.round, inp.season_progress, inp.is_modern_era,
        inp.quali_pos,
        inp.driver_podium_rate_5r, inp.driver_win_rate_all,
        inp.driver_avg_pos_5r, inp.constr_podium_rate_5r,
        inp.driver_circuit_podium_rate,
    ]
    return _predict(bundle, values, threshold)


def get_feature_importance(model_key: str) -> dict:
    bundle = _get_models().get(model_key)
    if not bundle or not bundle.loaded:
        return {}
    return bundle.metrics.get("feature_importance", {})
