from pydantic import BaseModel, Field, model_validator
from typing import Optional


# ── Respuesta común ───────────────────────────────────────────────────────────

class PredictionResponse(BaseModel):
    probability: float = Field(..., ge=0, le=1, description="Probabilidad entre 0 y 1")
    label:       bool  = Field(..., description="True si supera el threshold")
    threshold:   float = Field(..., description="Threshold usado para la decisión")
    confidence:  str   = Field(..., description="alta | media | baja")
    model_auc:   Optional[float] = Field(None, description="AUC CV del modelo entrenado")
    features_used: list[str] = []


class ModelStatusResponse(BaseModel):
    safety_car:         dict
    mechanical_failure: dict
    position:           dict


class FeatureImportanceResponse(BaseModel):
    model: str
    importance: dict  # {feature_name: importance_value}


# ── Safety Car ────────────────────────────────────────────────────────────────

class SafetyCarRequest(BaseModel):
    year:                int   = Field(..., ge=1950, le=2030)
    round:               int   = Field(..., ge=1,    le=30)
    season_progress:     float = Field(..., ge=0,    le=1,
                                       description="round / total_rounds de la temporada")
    lat:                 float = Field(..., description="Latitud del circuito")
    lng:                 float = Field(..., description="Longitud del circuito")
    alt:                 float = Field(0,   description="Altitud del circuito en metros")
    country_sc_rate:     float = Field(0.5, ge=0, le=1,
                                       description="Tasa histórica de SC en el país del circuito")
    circuit_sc_rate_3y:  float = Field(0.5, ge=0, le=1,
                                       description="Tasa SC últimas 3 temporadas en el circuito")
    circuit_sc_rate_all: float = Field(0.5, ge=0, le=1,
                                       description="Tasa SC histórica en el circuito")
    n_finishers:         float = Field(18,  ge=0,  le=26,
                                       description="Media de pilotos que terminan en este circuito")
    n_pit_stops:         float = Field(40,  ge=0,
                                       description="Media de pit stops totales en el circuito")
    is_modern_era:       int   = Field(1,   ge=0, le=1,
                                       description="1 si year >= 2011")

    @model_validator(mode="after")
    def set_modern_era(self):
        self.is_modern_era = 1 if self.year >= 2011 else 0
        return self

    model_config = {"json_schema_extra": {"example": {
        "year": 2024, "round": 8, "season_progress": 0.38,
        "lat": 43.7347, "lng": 7.4205, "alt": 7,
        "country_sc_rate": 0.72, "circuit_sc_rate_3y": 0.67,
        "circuit_sc_rate_all": 0.65, "n_finishers": 17, "n_pit_stops": 52,
    }}}


# ── Fallo mecánico ────────────────────────────────────────────────────────────

class MechanicalFailureRequest(BaseModel):
    year:                    int   = Field(..., ge=1950, le=2030)
    round:                   int   = Field(..., ge=1,    le=30)
    season_progress:         float = Field(..., ge=0,    le=1)
    grid_position:           int   = Field(..., ge=1,    le=26)
    laps_completed:          int   = Field(0,   ge=0,
                                           description="Vueltas completadas hasta ahora (0 = antes de la carrera)")
    driver_dnf_rate_5r:      float = Field(0.1, ge=0, le=1,
                                           description="Tasa DNF mecánico del piloto en las últimas 5 carreras")
    driver_dnf_rate_all:     float = Field(0.1, ge=0, le=1,
                                           description="Tasa DNF mecánico histórica del piloto")
    driver_races_count:      int   = Field(50,  ge=0,
                                           description="Número total de carreras del piloto")
    constructor_dnf_rate_5r: float = Field(0.1, ge=0, le=1,
                                           description="Tasa DNF mecánico del constructor en las últimas 5 carreras")

    @model_validator(mode="after")
    def set_derived(self):
        self.is_modern_era = 1 if self.year >= 2014 else 0
        return self

    is_modern_era: int = 1

    model_config = {"json_schema_extra": {"example": {
        "year": 2024, "round": 5, "season_progress": 0.24,
        "grid_position": 3, "laps_completed": 0,
        "driver_dnf_rate_5r": 0.0, "driver_dnf_rate_all": 0.05,
        "driver_races_count": 180, "constructor_dnf_rate_5r": 0.08,
    }}}


# ── Podio ─────────────────────────────────────────────────────────────────────

class PodiumRequest(BaseModel):
    year:                       int   = Field(..., ge=1950, le=2030)
    round:                      int   = Field(..., ge=1,    le=30)
    season_progress:            float = Field(..., ge=0,    le=1)
    quali_pos:                  int   = Field(..., ge=1,    le=26,
                                              description="Posición de clasificación")
    driver_podium_rate_5r:      float = Field(0.3, ge=0, le=1)
    driver_win_rate_all:        float = Field(0.2, ge=0, le=1)
    driver_avg_pos_5r:          float = Field(5.0, ge=1, le=26)
    constr_podium_rate_5r:      float = Field(0.3, ge=0, le=1)
    driver_circuit_podium_rate: float = Field(0.3, ge=0, le=1)

    @model_validator(mode="after")
    def set_derived(self):
        self.is_modern_era = 1 if self.year >= 2014 else 0
        return self

    is_modern_era: int = 1

    model_config = {"json_schema_extra": {"example": {
        "year": 2024, "round": 5, "season_progress": 0.24,
        "quali_pos": 2,
        "driver_podium_rate_5r": 0.8, "driver_win_rate_all": 0.45,
        "driver_avg_pos_5r": 1.8, "constr_podium_rate_5r": 0.75,
        "driver_circuit_podium_rate": 0.6,
    }}}
