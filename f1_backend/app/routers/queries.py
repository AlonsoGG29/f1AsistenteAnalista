from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.db.session import get_db
from app.schemas.f1_schemas import (
    DriverBase, DriverDetail, ConstructorBase, ConstructorDetail,
    CircuitBase, RaceBase, RaceResult, StandingsEntry, PaginatedResponse,
)
import app.services.query_service as svc

router = APIRouter(prefix="/api", tags=["Consultas básicas"])


# ── Pilotos ───────────────────────────────────────────────────────────────────

@router.get("/drivers", response_model=PaginatedResponse, summary="Lista de pilotos")
async def list_drivers(
    nationality: Optional[str] = Query(None, description="Filtrar por nacionalidad"),
    search: Optional[str] = Query(None, description="Buscar por nombre"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=2000),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    total, items = await svc.get_drivers(db, nationality, search, skip, page_size)
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/drivers/{driver_id}", response_model=DriverDetail, summary="Detalle de piloto")
async def get_driver(driver_id: int, db: AsyncSession = Depends(get_db)):
    driver = await svc.get_driver(db, driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Piloto no encontrado")
    return driver


# ── Constructores ─────────────────────────────────────────────────────────────

@router.get("/constructors", response_model=PaginatedResponse, summary="Lista de constructores")
async def list_constructors(
    nationality: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    total, items = await svc.get_constructors(db, nationality, search, skip, page_size)
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/constructors/{constructor_id}", response_model=ConstructorDetail, summary="Detalle de constructor")
async def get_constructor(constructor_id: int, db: AsyncSession = Depends(get_db)):
    constructor = await svc.get_constructor(db, constructor_id)
    if not constructor:
        raise HTTPException(status_code=404, detail="Constructor no encontrado")
    return constructor


# ── Circuitos ─────────────────────────────────────────────────────────────────

@router.get("/circuits", response_model=PaginatedResponse, summary="Lista de circuitos")
async def list_circuits(
    country: Optional[str] = Query(None, description="Filtrar por país"),
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    total, items = await svc.get_circuits(db, country, skip, page_size)
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/circuits/{circuit_id}", response_model=CircuitBase, summary="Detalle de circuito")
async def get_circuit(circuit_id: int, db: AsyncSession = Depends(get_db)):
    circuit = await svc.get_circuit(db, circuit_id)
    if not circuit:
        raise HTTPException(status_code=404, detail="Circuito no encontrado")
    return circuit


# ── Carreras ──────────────────────────────────────────────────────────────────

@router.get("/races", response_model=PaginatedResponse, summary="Lista de carreras")
async def list_races(
    year: Optional[int] = Query(None, description="Filtrar por temporada"),
    circuit_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    skip = (page - 1) * page_size
    total, items = await svc.get_races(db, year, circuit_id, skip, page_size)
    return PaginatedResponse(total=total, page=page, page_size=page_size, items=items)


@router.get("/races/{race_id}/results", response_model=List[RaceResult], summary="Resultados de una carrera")
async def get_race_results(race_id: int, db: AsyncSession = Depends(get_db)):
    results = await svc.get_race_results(db, race_id)
    if not results:
        raise HTTPException(status_code=404, detail="Carrera no encontrada o sin resultados")
    return results


# ── Standings ─────────────────────────────────────────────────────────────────

@router.get(
    "/standings/drivers/{year}",
    response_model=List[StandingsEntry],
    summary="Clasificación de pilotos de una temporada",
)
async def driver_standings(
    year: int,
    after_round: Optional[int] = Query(None, description="Standings tras la ronda N"),
    db: AsyncSession = Depends(get_db),
):
    standings = await svc.get_driver_standings(db, year, after_round)
    if not standings:
        raise HTTPException(status_code=404, detail=f"Sin datos de standings para {year}")
    return standings


@router.get(
    "/standings/constructors/{year}",
    response_model=List[StandingsEntry],
    summary="Clasificación de constructores de una temporada",
)
async def constructor_standings(
    year: int,
    after_round: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    standings = await svc.get_constructor_standings(db, year, after_round)
    if not standings:
        raise HTTPException(status_code=404, detail=f"Sin datos de standings para {year}")
    return standings
