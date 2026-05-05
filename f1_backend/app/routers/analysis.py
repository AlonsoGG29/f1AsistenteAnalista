from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.db.session import get_db
from app.schemas.f1_schemas import (
    DriverLapTimes, PitStopItem, PitStopStats,
    DriverSeasonStats, ConstructorSeasonStats,
    HeadToHeadStats, CircuitStats,
)
import app.services.analysis_service as svc

router = APIRouter(prefix="/api/analysis", tags=["Análisis"])


# ── Tiempos de vuelta ─────────────────────────────────────────────────────────

@router.get(
    "/races/{race_id}/lap-times",
    response_model=List[DriverLapTimes],
    summary="Tiempos de vuelta de una carrera",
    description="Devuelve los tiempos de vuelta agrupados por piloto. "
                "Pasar driver_ids para comparar solo pilotos concretos.",
)
async def race_lap_times(
    race_id: int,
    driver_ids: Optional[str] = Query(
        None,
        description="IDs de pilotos separados por coma, ej: 1,3,8",
    ),
    db: AsyncSession = Depends(get_db),
):
    ids = [int(x) for x in driver_ids.split(",")] if driver_ids else None
    data = await svc.get_race_lap_times(db, race_id, ids)
    if not data:
        raise HTTPException(status_code=404, detail="Sin datos de vuelta para esta carrera")
    return data


@router.get(
    "/drivers/{driver_id}/lap-progression/{year}",
    summary="Progresión de tiempos del piloto en una temporada",
    description="Tiempo medio y mejor tiempo por carrera a lo largo de la temporada.",
)
async def driver_lap_progression(
    driver_id: int,
    year: int,
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_driver_lap_progression(db, driver_id, year)
    if not data:
        raise HTTPException(status_code=404, detail="Sin datos para este piloto y temporada")
    return data


# ── Pit Stops ─────────────────────────────────────────────────────────────────

@router.get(
    "/races/{race_id}/pit-stops",
    response_model=List[PitStopItem],
    summary="Pit stops de una carrera",
)
async def race_pit_stops(race_id: int, db: AsyncSession = Depends(get_db)):
    data = await svc.get_race_pit_stops(db, race_id)
    if not data:
        raise HTTPException(status_code=404, detail="Sin pit stops para esta carrera")
    return data


@router.get(
    "/drivers/{driver_id}/pit-stops",
    response_model=List[PitStopStats],
    summary="Estadísticas de pit stops de un piloto",
)
async def driver_pit_stops(
    driver_id: int,
    year: Optional[int] = Query(None, description="Filtrar por temporada"),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_driver_pit_stop_stats(db, driver_id, year)
    if not data:
        raise HTTPException(status_code=404, detail="Sin datos de pit stops para este piloto")
    return data


# ── Estadísticas de temporada ─────────────────────────────────────────────────

@router.get(
    "/drivers/{driver_id}/season-stats",
    response_model=List[DriverSeasonStats],
    summary="Estadísticas por temporada de un piloto",
)
async def driver_season_stats(
    driver_id: int,
    year: Optional[int] = Query(None, description="Filtrar por año concreto"),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_driver_season_stats(db, driver_id, year)
    if not data:
        raise HTTPException(status_code=404, detail="Sin estadísticas para este piloto")
    return data


@router.get(
    "/constructors/{constructor_id}/season-stats",
    response_model=List[ConstructorSeasonStats],
    summary="Estadísticas por temporada de un constructor",
)
async def constructor_season_stats(
    constructor_id: int,
    year: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    data = await svc.get_constructor_season_stats(db, constructor_id, year)
    if not data:
        raise HTTPException(status_code=404, detail="Sin estadísticas para este constructor")
    return data


# ── Head-to-Head ──────────────────────────────────────────────────────────────

@router.get(
    "/head-to-head",
    response_model=HeadToHeadStats,
    summary="Comparativa directa entre dos pilotos",
    description="Estadísticas de las carreras en que ambos pilotos participaron juntos.",
)
async def head_to_head(
    driver_a: int = Query(..., description="ID del primer piloto"),
    driver_b: int = Query(..., description="ID del segundo piloto"),
    year: Optional[int] = Query(None, description="Limitar a una temporada"),
    db: AsyncSession = Depends(get_db),
):
    if driver_a == driver_b:
        raise HTTPException(status_code=400, detail="Los dos pilotos deben ser distintos")
    data = await svc.get_head_to_head(db, driver_a, driver_b, year)
    if not data:
        raise HTTPException(
            status_code=404,
            detail="No se encontraron carreras compartidas entre estos pilotos",
        )
    return data


# ── Circuitos ─────────────────────────────────────────────────────────────────

@router.get(
    "/circuits/{circuit_id}/stats",
    response_model=CircuitStats,
    summary="Estadísticas históricas de un circuito",
)
async def circuit_stats(circuit_id: int, db: AsyncSession = Depends(get_db)):
    data = await svc.get_circuit_stats(db, circuit_id)
    if not data:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")
    return data
