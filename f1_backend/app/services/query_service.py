"""
Servicio de consultas básicas: pilotos, constructores, circuitos y carreras.
Toda la lógica de acceso a datos vive aquí; los routers solo orquestan.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, text
from typing import Optional, List
from app.models.f1_models import (
    Driver, Constructor, Circuit, Race, Result,
    DriverStanding, ConstructorStanding, Status,
)
from app.schemas.f1_schemas import (
    DriverBase, DriverDetail, ConstructorBase, ConstructorDetail,
    CircuitBase, RaceBase, RaceResult, StandingsEntry,
)


# ── Pilotos ───────────────────────────────────────────────────────────────────

async def get_drivers(
    db: AsyncSession,
    nationality: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[int, List[DriverBase]]:
    q = select(Driver)
    if nationality:
        q = q.where(Driver.nationality.ilike(f"%{nationality}%"))
    if search:
        q = q.where(
            (Driver.forename + " " + Driver.surname).ilike(f"%{search}%")
        )
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.order_by(Driver.surname).offset(skip).limit(limit))
    drivers = result.scalars().all()
    return total, [DriverBase.model_validate(d) for d in drivers]


async def get_driver(db: AsyncSession, driver_id: int) -> Optional[DriverDetail]:
    driver = await db.get(Driver, driver_id)
    if not driver:
        return None

    stats = await db.execute(
        text("""
            SELECT
                COUNT(DISTINCT r.resultId)                              AS total_races,
                SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END)        AS total_wins,
                SUM(r.points)                                           AS total_points,
                ARRAY_AGG(DISTINCT c.name)                              AS constructors
            FROM results r
            JOIN constructors c ON c.constructorId = r.constructorId
            WHERE r.driverId = :did
        """),
        {"did": driver_id},
    )
    row = stats.mappings().one()

    champs = await db.scalar(
        text("""
            SELECT COUNT(*) FROM driver_standings ds
            JOIN (
                SELECT year, MAX(raceId) AS last_race
                FROM races GROUP BY year
            ) last ON last.last_race = ds.raceId
            WHERE ds.driverId = :did AND ds.position = 1
        """),
        {"did": driver_id},
    )

    detail = DriverDetail.model_validate(driver)
    detail.total_races = row["total_races"] or 0
    detail.total_wins = row["total_wins"] or 0
    detail.total_points = float(row["total_points"] or 0)
    detail.championships = champs or 0
    detail.constructors = [c for c in (row["constructors"] or []) if c]
    return detail


# ── Constructores ─────────────────────────────────────────────────────────────

async def get_constructors(
    db: AsyncSession,
    nationality: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[int, List[ConstructorBase]]:
    q = select(Constructor)
    if nationality:
        q = q.where(Constructor.nationality.ilike(f"%{nationality}%"))
    if search:
        q = q.where(Constructor.name.ilike(f"%{search}%"))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.order_by(Constructor.name).offset(skip).limit(limit))
    constructors = result.scalars().all()
    return total, [ConstructorBase.model_validate(c) for c in constructors]


async def get_constructor(db: AsyncSession, constructor_id: int) -> Optional[ConstructorDetail]:
    constructor = await db.get(Constructor, constructor_id)
    if not constructor:
        return None

    stats = await db.execute(
        text("""
            SELECT
                COUNT(DISTINCT r.resultId)                          AS total_races,
                SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END)    AS total_wins,
                SUM(r.points)                                       AS total_points,
                ARRAY_AGG(DISTINCT d.forename || ' ' || d.surname)  AS drivers,
                SUM(CASE WHEN s.status NOT IN ('Finished', '+1 Lap', '+2 Laps',
                    '+3 Laps', '+4 Laps', '+5 Laps', '+6 Laps', '+7 Laps',
                    '+8 Laps', '+9 Laps') THEN 1 ELSE 0 END)        AS dnfs
            FROM results r
            JOIN drivers d    ON d.driverId    = r.driverId
            JOIN status  s    ON s.statusId    = r.statusId
            WHERE r.constructorId = :cid
        """),
        {"cid": constructor_id},
    )
    row = stats.mappings().one()

    champs = await db.scalar(
        text("""
            SELECT COUNT(*) FROM constructor_standings cs
            JOIN (
                SELECT year, MAX(raceId) AS last_race
                FROM races GROUP BY year
            ) last ON last.last_race = cs.raceId
            WHERE cs.constructorId = :cid AND cs.position = 1
        """),
        {"cid": constructor_id},
    )

    detail = ConstructorDetail.model_validate(constructor)
    detail.total_races = row["total_races"] or 0
    detail.total_wins = row["total_wins"] or 0
    detail.total_points = float(row["total_points"] or 0)
    detail.championships = champs or 0
    detail.drivers = [d for d in (row["drivers"] or []) if d]
    detail.dnfs = row["dnfs"] or 0
    return detail


# ── Circuitos ─────────────────────────────────────────────────────────────────

async def get_circuits(
    db: AsyncSession,
    country: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
) -> tuple[int, List[CircuitBase]]:
    q = select(Circuit)
    if country:
        q = q.where(Circuit.country.ilike(f"%{country}%"))
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    result = await db.execute(q.order_by(Circuit.name).offset(skip).limit(limit))
    return total, [CircuitBase.model_validate(c) for c in result.scalars().all()]


async def get_circuit(db: AsyncSession, circuit_id: int) -> Optional[CircuitBase]:
    circuit = await db.get(Circuit, circuit_id)
    return CircuitBase.model_validate(circuit) if circuit else None


# ── Carreras ──────────────────────────────────────────────────────────────────

async def get_races(
    db: AsyncSession,
    year: Optional[int] = None,
    circuit_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 50,
) -> tuple[int, List[RaceBase]]:
    stmt = (
        select(
            Race.raceId, Race.year, Race.round, Race.name, Race.date,
            Circuit.name.label("circuit_name"),
            Circuit.country.label("circuit_country"),
        )
        .join(Circuit, Race.circuitId == Circuit.circuitId)
    )
    if year:
        stmt = stmt.where(Race.year == year)
    if circuit_id:
        stmt = stmt.where(Race.circuitId == circuit_id)

    total = await db.scalar(select(func.count()).select_from(stmt.subquery()))
    result = await db.execute(
        stmt.order_by(Race.year.desc(), Race.round).offset(skip).limit(limit)
    )
    return total, [RaceBase.model_validate(row._mapping) for row in result]


async def get_race_results(db: AsyncSession, race_id: int) -> List[RaceResult]:
    stmt = (
        select(
            Result.position,
            Result.positionText,
            Result.points,
            Result.grid,
            Result.laps,
            Result.time,
            Result.fastestLapTime,
            Result.fastestLapSpeed,
            Status.status.label("status"),
            Driver.forename.label("driver_forename"),
            Driver.surname.label("driver_surname"),
            Driver.code.label("driver_code"),
            Constructor.name.label("constructor_name"),
        )
        .join(Driver, Result.driverId == Driver.driverId)
        .join(Constructor, Result.constructorId == Constructor.constructorId)
        .join(Status, Result.statusId == Status.statusId)
        .where(Result.raceId == race_id)
        .order_by(Result.positionOrder)
    )
    result = await db.execute(stmt)
    return [RaceResult.model_validate(row._mapping) for row in result]


# ── Standings ─────────────────────────────────────────────────────────────────

async def get_driver_standings(
    db: AsyncSession,
    year: int,
    after_round: Optional[int] = None,
) -> List[StandingsEntry]:
    """Standings de pilotos tras una ronda concreta (o al final del año)."""
    subq = (
        select(func.max(Race.raceId))
        .where(Race.year == year)
    )
    if after_round:
        subq = subq.where(Race.round <= after_round)
    last_race_id = await db.scalar(subq)
    if not last_race_id:
        return []

    stmt = (
        select(
            DriverStanding.position,
            DriverStanding.points,
            DriverStanding.wins,
            Driver.driverId.label("driver_id"),
            (Driver.forename + " " + Driver.surname).label("driver_name"),
        )
        .join(Driver, DriverStanding.driverId == Driver.driverId)
        .where(DriverStanding.raceId == last_race_id)
        .order_by(DriverStanding.position)
    )
    result = await db.execute(stmt)
    return [StandingsEntry.model_validate(row._mapping) for row in result]


async def get_constructor_standings(
    db: AsyncSession,
    year: int,
    after_round: Optional[int] = None,
) -> List[StandingsEntry]:
    subq = select(func.max(Race.raceId)).where(Race.year == year)
    if after_round:
        subq = subq.where(Race.round <= after_round)
    last_race_id = await db.scalar(subq)
    if not last_race_id:
        return []

    stmt = (
        select(
            ConstructorStanding.position,
            ConstructorStanding.points,
            ConstructorStanding.wins,
            Constructor.constructorId.label("constructor_id"),
            Constructor.name.label("constructor_name"),
        )
        .join(Constructor, ConstructorStanding.constructorId == Constructor.constructorId)
        .where(ConstructorStanding.raceId == last_race_id)
        .order_by(ConstructorStanding.position)
    )
    result = await db.execute(stmt)
    return [StandingsEntry.model_validate(row._mapping) for row in result]
