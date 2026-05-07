"""
Servicio de análisis: tiempos de vuelta, pit stops,
estadísticas de temporada y comparativas entre pilotos/equipos.
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional, List
from app.models.f1_models import (
    Driver, Constructor, Race, Result, PitStop, LapTime, Status,
)
from app.schemas.f1_schemas import (
    DriverLapTimes, LapTimeItem, PitStopItem, PitStopStats,
    DriverSeasonStats, ConstructorSeasonStats, HeadToHeadStats, CircuitStats,
)


# ── Tiempos de vuelta ─────────────────────────────────────────────────────────

async def get_race_lap_times(
    db: AsyncSession,
    race_id: int,
    driver_ids: Optional[List[int]] = None,
) -> List[DriverLapTimes]:
    """
    Devuelve los tiempos de vuelta de todos los pilotos de una carrera.
    Se pueden filtrar por lista de driver_ids para comparativas.
    """
    stmt = (
        select(
            LapTime.driverId,
            LapTime.lap,
            LapTime.position,
            LapTime.time,
            LapTime.milliseconds,
            Driver.forename,
            Driver.surname,
            Constructor.name.label("constructor_name"),
        )
        .join(Driver, LapTime.driverId == Driver.driverId)
        .join(
            Result,
            (Result.raceId == LapTime.raceId) & (Result.driverId == LapTime.driverId),
        )
        .join(Constructor, Result.constructorId == Constructor.constructorId)
        .where(LapTime.raceId == race_id)
        .order_by(LapTime.driverId, LapTime.lap)
    )
    if driver_ids:
        stmt = stmt.where(LapTime.driverId.in_(driver_ids))

    result = await db.execute(stmt)
    rows = result.mappings().all()

    # Agrupar por piloto
    drivers: dict[int, DriverLapTimes] = {}
    for row in rows:
        did = row["driverId"]
        if did not in drivers:
            drivers[did] = DriverLapTimes(
                driver_id=did,
                driver_name=f"{row['forename']} {row['surname']}",
                constructor_name=row["constructor_name"],
                laps=[],
            )
        drivers[did].laps.append(
            LapTimeItem(
                lap=row["lap"],
                position=row["position"],
                time=row["time"],
                milliseconds=row["milliseconds"],
            )
        )
    return list(drivers.values())


async def get_driver_lap_progression(
    db: AsyncSession,
    driver_id: int,
    year: int,
) -> List[dict]:
    """
    Progresión de tiempos medios de vuelta del piloto a lo largo de una temporada.
    Útil para visualizar evolución de rendimiento carrera a carrera.
    """
    stmt = text("""
        SELECT
            ra.round,
            ra.name  AS race_name,
            ra.date,
            AVG(lt.milliseconds)            AS avg_lap_ms,
            MIN(lt.milliseconds)            AS best_lap_ms,
            COUNT(lt.lap)                   AS laps_completed
        FROM lap_times lt
        JOIN races ra ON ra.raceId = lt.raceId
        WHERE lt.driverId = :did
          AND ra.year = :year
        GROUP BY ra.round, ra.name, ra.date
        ORDER BY ra.round
    """)
    result = await db.execute(stmt, {"did": driver_id, "year": year})
    return [dict(row) for row in result.mappings()]


# ── Pit Stops ─────────────────────────────────────────────────────────────────

async def get_race_pit_stops(
    db: AsyncSession,
    race_id: int,
) -> List[PitStopItem]:
    stmt = (
        select(
            PitStop.stop,
            PitStop.lap,
            PitStop.duration,
            PitStop.milliseconds,
            (Driver.forename + " " + Driver.surname).label("driver_name"),
            Constructor.name.label("constructor_name"),
        )
        .join(Driver, PitStop.driverId == Driver.driverId)
        .join(
            Result,
            (Result.raceId == PitStop.raceId) & (Result.driverId == PitStop.driverId),
        )
        .join(Constructor, Result.constructorId == Constructor.constructorId)
        .where(PitStop.raceId == race_id)
        .order_by(PitStop.lap, PitStop.stop)
    )
    result = await db.execute(stmt)
    return [PitStopItem.model_validate(row._mapping) for row in result]


async def get_driver_pit_stop_stats(
    db: AsyncSession,
    driver_id: int,
    year: Optional[int] = None,
) -> List[PitStopStats]:
    """Estadísticas agregadas de pit stops por carrera para un piloto."""
    year_filter = "AND ra.year = :year" if year else ""
    sql = f"""
        SELECT
            ra.raceId   AS race_id,
            ra.name     AS race_name,
            ra.year,
            d.forename || ' ' || d.surname  AS driver_name,
            c.name                          AS constructor_name,
            COUNT(ps.stop)                  AS total_stops,
            AVG(ps.milliseconds)            AS avg_duration_ms,
            MIN(ps.milliseconds)            AS fastest_stop_ms,
            MIN(CASE WHEN ps.milliseconds = MIN(ps.milliseconds) OVER (
                    PARTITION BY ps.raceId, ps.driverId)
                THEN ps.lap END)            AS fastest_stop_lap
        FROM pit_stops ps
        JOIN races       ra ON ra.raceId       = ps.raceId
        JOIN drivers     d  ON d.driverId      = ps.driverId
        JOIN results     r  ON r.raceId        = ps.raceId
                            AND r.driverId     = ps.driverId
        JOIN constructors c ON c.constructorId = r.constructorId
        WHERE ps.driverId = :did
          {year_filter}
        GROUP BY ra.raceId, ra.name, ra.year, d.forename, d.surname, c.name
        ORDER BY ra.year, ra.raceId
    """
    params = {"did": driver_id}
    if year:
        params["year"] = year
    result = await db.execute(text(sql), params)
    out = []
    for row in result.mappings():
        d = dict(row)
        d["driver_id"] = driver_id
        out.append(PitStopStats.model_validate(d))
    return out


# ── Estadísticas de temporada ─────────────────────────────────────────────────

async def get_driver_season_stats(
    db: AsyncSession,
    driver_id: int,
    year: Optional[int] = None,
) -> List[DriverSeasonStats]:
    year_filter = "AND ra.year = :year" if year else ""
    sql = f"""
        SELECT
            ra.year,
            d.forename || ' ' || d.surname                             AS driver_name,
            c.name                                                      AS constructor_name,
            COUNT(r.resultId)                                           AS races,
            SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END)            AS wins,
            SUM(CASE WHEN r.position <= 3 THEN 1 ELSE 0 END)           AS podiums,
            SUM(r.points)                                               AS points,
            AVG(r.grid)                                                 AS avg_grid,
            AVG(CASE WHEN r.position IS NOT NULL THEN r.position END)   AS avg_finish,
            SUM(CASE WHEN s.status NOT ILIKE '%Finished%'
                          AND s.status NOT ILIKE '%Lap%'
                     THEN 1 ELSE 0 END)                                 AS dnfs,
            SUM(CASE WHEN r.rank = 1 THEN 1 ELSE 0 END)                AS fastest_laps
        FROM results r
        JOIN races        ra ON ra.raceId        = r.raceId
        JOIN drivers      d  ON d.driverId       = r.driverId
        JOIN constructors c  ON c.constructorId  = r.constructorId
        JOIN status       s  ON s.statusId       = r.statusId
        WHERE r.driverId = :did
          {year_filter}
        GROUP BY ra.year, d.forename, d.surname, c.name
        ORDER BY ra.year DESC
    """
    params = {"did": driver_id}
    if year:
        params["year"] = year
    result = await db.execute(text(sql), params)
    out = []
    for row in result.mappings():
        d = dict(row)
        d["driver_id"] = driver_id
        out.append(DriverSeasonStats.model_validate(d))
    return out


async def get_constructor_season_stats(
    db: AsyncSession,
    constructor_id: int,
    year: Optional[int] = None,
) -> List[ConstructorSeasonStats]:
    year_filter = "AND ra.year = :year" if year else ""
    sql = f"""
        SELECT
            ra.year,
            c.name                                                  AS constructor_name,
            COUNT(DISTINCT ra.raceId)                               AS races,
            SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END)        AS wins,
            SUM(CASE WHEN r.position <= 3 THEN 1 ELSE 0 END)       AS podiums,
            SUM(r.points)                                           AS points,
            ARRAY_AGG(DISTINCT d.forename || ' ' || d.surname)      AS drivers,
            SUM(CASE WHEN s.status NOT ILIKE '%Finished%'
                          AND s.status NOT ILIKE '%Lap%'
                     THEN 1 ELSE 0 END)                             AS dnfs
        FROM results r
        JOIN races        ra ON ra.raceId       = r.raceId
        JOIN constructors c  ON c.constructorId = r.constructorId
        JOIN drivers      d  ON d.driverId      = r.driverId
        JOIN status       s  ON s.statusId      = r.statusId
        WHERE r.constructorId = :cid
          {year_filter}
        GROUP BY ra.year, c.name
        ORDER BY ra.year DESC
    """
    params = {"cid": constructor_id}
    if year:
        params["year"] = year
    result = await db.execute(text(sql), params)
    out = []
    for row in result.mappings():
        d = dict(row)
        d["constructor_id"] = constructor_id
        d["drivers"] = [x for x in (d.get("drivers") or []) if x]
        out.append(ConstructorSeasonStats.model_validate(d))
    return out


# ── Head-to-Head ──────────────────────────────────────────────────────────────

async def get_head_to_head(
    db: AsyncSession,
    driver_a_id: int,
    driver_b_id: int,
    year: Optional[int] = None,
) -> Optional[HeadToHeadStats]:
    """
    Comparativa directa entre dos pilotos en las carreras que coincidieron.
    """
    year_filter = "AND ra.year = :year" if year else ""
    sql = f"""
        WITH shared_races AS (
            SELECT ra.raceId
            FROM races ra
            JOIN results ra_a ON ra_a.raceId = ra.raceId AND ra_a.driverId = :aid
            JOIN results ra_b ON ra_b.raceId = ra.raceId AND ra_b.driverId = :bid
            WHERE 1=1 {year_filter}
        ),
        stats AS (
            SELECT
                r.driverId,
                COUNT(*)                            AS races,
                SUM(CASE WHEN r.position = 1 THEN 1 ELSE 0 END) AS wins,
                SUM(CASE WHEN r.position <= 3 THEN 1 ELSE 0 END) AS podiums,
                SUM(CASE WHEN r.grid = 1 THEN 1 ELSE 0 END)      AS poles,
                AVG(r.positionOrder)                AS avg_position,
                AVG(r.grid)                         AS avg_grid,
                SUM(r.points)                       AS total_points,
                SUM(CASE WHEN s.status NOT ILIKE '%Finished%'
                              AND s.status NOT ILIKE '%Lap%'
                         THEN 1 ELSE 0 END)         AS dnfs
            FROM results r
            JOIN status s ON s.statusId = r.statusId
            WHERE r.raceId IN (SELECT raceId FROM shared_races)
              AND r.driverId IN (:aid, :bid)
            GROUP BY r.driverId
        )
        SELECT
            da.driverId  AS driver_a_id,
            da.forename || ' ' || da.surname AS driver_a_name,
            db.driverId  AS driver_b_id,
            db.forename || ' ' || db.surname AS driver_b_name,
            sa.races     AS races_together,
            sa.wins      AS driver_a_wins,
            sb.wins      AS driver_b_wins,
            sa.podiums   AS driver_a_podiums,
            sb.podiums   AS driver_b_podiums,
            sa.poles     AS driver_a_poles,
            sb.poles     AS driver_b_poles,
            sa.avg_position AS driver_a_avg_position,
            sb.avg_position AS driver_b_avg_position,
            sa.avg_grid  AS driver_a_avg_grid,
            sb.avg_grid  AS driver_b_avg_grid,
            sa.total_points AS driver_a_total_points,
            sb.total_points AS driver_b_total_points,
            sa.dnfs      AS driver_a_dnfs,
            sb.dnfs      AS driver_b_dnfs
        FROM stats sa
        JOIN stats sb        ON sb.driverId = :bid
        JOIN drivers da ON da.driverId = :aid
        JOIN drivers db ON db.driverId = :bid
        WHERE sa.driverId = :aid
    """
    params = {"aid": driver_a_id, "bid": driver_b_id}
    if year:
        params["year"] = year
    result = await db.execute(text(sql), params)
    row = result.mappings().one_or_none()
    if not row:
        return None

    data = dict(row)

    # Enrich with teammate advantage if year is specified
    if year:
        for prefix, did in [("driver_a", driver_a_id), ("driver_b", driver_b_id)]:
            tm = await _get_teammate_advantage(db, did, year)
            if tm:
                data[f"{prefix}_teammate_name"] = tm["teammate_name"]
                data[f"{prefix}_teammate_diff"] = tm["points_diff"]

    return HeadToHeadStats.model_validate(data)


async def _get_teammate_advantage(
    db: AsyncSession, driver_id: int, year: int
) -> Optional[dict]:
    """
    Finds the driver's main teammate (same constructor, most shared races)
    in a given season and returns the points difference.
    """
    sql = """
        WITH driver_team AS (
            SELECT r.constructorId, COUNT(*) AS cnt
            FROM results r
            JOIN races ra ON ra.raceId = r.raceId
            WHERE r.driverId = :did AND ra.year = :year
            GROUP BY r.constructorId
            ORDER BY cnt DESC
            LIMIT 1
        ),
        teammate AS (
            SELECT r.driverId, d.forename || ' ' || d.surname AS name,
                   SUM(r.points) AS pts
            FROM results r
            JOIN races ra ON ra.raceId = r.raceId
            JOIN drivers d ON d.driverId = r.driverId
            WHERE r.constructorId = (SELECT constructorId FROM driver_team)
              AND ra.year = :year
              AND r.driverId != :did
            GROUP BY r.driverId, d.forename, d.surname
            ORDER BY pts DESC
            LIMIT 1
        ),
        driver_pts AS (
            SELECT SUM(r.points) AS pts
            FROM results r
            JOIN races ra ON ra.raceId = r.raceId
            WHERE r.driverId = :did AND ra.year = :year
        )
        SELECT t.name AS teammate_name, dp.pts - t.pts AS points_diff
        FROM teammate t, driver_pts dp
    """
    result = await db.execute(text(sql), {"did": driver_id, "year": year})
    row = result.mappings().one_or_none()
    if row and row["teammate_name"]:
        return {"teammate_name": row["teammate_name"], "points_diff": row["points_diff"]}
    return None


# ── Estadísticas de circuito ──────────────────────────────────────────────────

async def get_circuit_stats(
    db: AsyncSession,
    circuit_id: int,
) -> Optional[CircuitStats]:
    stmt = text("""
        WITH base AS (
            SELECT
                ci.circuitId, ci.name AS circuit_name,
                COALESCE(ci.country, '') AS country,
                COUNT(DISTINCT ra.raceId) AS total_races
            FROM circuits ci
            LEFT JOIN races ra ON ra.circuitId = ci.circuitId
            WHERE ci.circuitId = :cid
            GROUP BY ci.circuitId, ci.name, ci.country
        ),
        top_driver AS (
            SELECT d.forename || ' ' || d.surname AS name,
                   COUNT(*) AS wins
            FROM results r
            JOIN races ra ON ra.raceId = r.raceId
            JOIN drivers d ON d.driverId = r.driverId
            WHERE ra.circuitId = :cid AND r.position = 1
            GROUP BY d.forename, d.surname
            ORDER BY wins DESC LIMIT 1
        ),
        top_constructor AS (
            SELECT c.name, COUNT(*) AS wins
            FROM results r
            JOIN races ra ON ra.raceId = r.raceId
            JOIN constructors c ON c.constructorId = r.constructorId
            WHERE ra.circuitId = :cid AND r.position = 1
            GROUP BY c.name
            ORDER BY wins DESC LIMIT 1
        ),
        lap_record AS (
            SELECT
                r.fastestLapTime  AS lap_time,
                d.forename || ' ' || d.surname AS driver,
                ra.year
            FROM results r
            JOIN races ra ON ra.raceId = r.raceId
            JOIN drivers d ON d.driverId = r.driverId
            WHERE ra.circuitId = :cid
              AND r.rank = 1
              AND r.fastestLapTime IS NOT NULL
            ORDER BY r.fastestLapTime
            LIMIT 1
        )
        SELECT
            b.circuitId    AS circuit_id,
            b.circuit_name,
            b.country,
            b.total_races,
            td.name        AS most_wins_driver,
            tc.name        AS most_wins_constructor,
            lr.lap_time    AS lap_record_time,
            lr.driver      AS lap_record_driver,
            lr.year        AS lap_record_year
        FROM base b
        LEFT JOIN top_driver      td ON true
        LEFT JOIN top_constructor tc ON true
        LEFT JOIN lap_record       lr ON true
    """)
    result = await db.execute(stmt, {"cid": circuit_id})
    row = result.mappings().one_or_none()
    return CircuitStats.model_validate(dict(row)) if row else None
