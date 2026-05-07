from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import date


# ── Utilidades ────────────────────────────────────────────────────────────────

class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list


# ── Circuitos ─────────────────────────────────────────────────────────────────

class CircuitBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    circuitId: int
    circuitRef: str
    name: str
    location: Optional[str] = None
    country: Optional[str] = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    alt: Optional[int] = None
    url: Optional[str] = None


# ── Pilotos ───────────────────────────────────────────────────────────────────

class DriverBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    driverId: int
    driverRef: str
    number: Optional[int] = None
    code: Optional[str] = None
    forename: str
    surname: str
    dob: Optional[date] = None
    nationality: Optional[str] = None
    url: Optional[str] = None

    @property
    def full_name(self) -> str:
        return f"{self.forename} {self.surname}"


class DriverDetail(DriverBase):
    total_races: int = 0
    total_wins: int = 0
    total_points: float = 0.0
    championships: int = 0
    constructors: List[str] = []


# ── Constructores ─────────────────────────────────────────────────────────────

class ConstructorBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    constructorId: int
    constructorRef: str
    name: str
    nationality: Optional[str] = None
    url: Optional[str] = None


class ConstructorDetail(ConstructorBase):
    total_races: int = 0
    total_wins: int = 0
    total_points: float = 0.0
    championships: int = 0
    drivers: List[str] = []


# ── Carreras ──────────────────────────────────────────────────────────────────

class RaceBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    raceId: int
    year: int
    round: int
    name: str
    date: date
    circuit_name: Optional[str] = None
    circuit_country: Optional[str] = None


class RaceResult(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    position: Optional[int] = None
    positionText: str
    points: float
    grid: Optional[int] = None
    laps: int
    time: Optional[str] = None
    fastestLapTime: Optional[str] = None
    fastestLapSpeed: Optional[str] = None
    status: Optional[str] = None
    driver_forename: str
    driver_surname: str
    driver_code: Optional[str] = None
    constructor_name: str


# ── Tiempos de vuelta ─────────────────────────────────────────────────────────

class LapTimeItem(BaseModel):
    lap: int
    position: Optional[int] = None
    time: Optional[str] = None
    milliseconds: Optional[int] = None


class DriverLapTimes(BaseModel):
    driver_id: int
    driver_name: str
    constructor_name: str
    laps: List[LapTimeItem]


# ── Pit Stops ─────────────────────────────────────────────────────────────────

class PitStopItem(BaseModel):
    stop: int
    lap: int
    duration: Optional[str] = None
    milliseconds: Optional[int] = None
    driver_name: str
    constructor_name: str


# ── Análisis ──────────────────────────────────────────────────────────────────

class DriverSeasonStats(BaseModel):
    year: int
    driver_id: int
    driver_name: str
    constructor_name: str
    races: int
    wins: int
    podiums: int
    points: float
    avg_grid: Optional[float] = None
    avg_finish: Optional[float] = None
    dnfs: int
    fastest_laps: int


class ConstructorSeasonStats(BaseModel):
    year: int
    constructor_id: int
    constructor_name: str
    races: int
    wins: int
    podiums: int
    points: float
    drivers: List[str]
    dnfs: int


class HeadToHeadStats(BaseModel):
    driver_a_id: int
    driver_a_name: str
    driver_b_id: int
    driver_b_name: str
    races_together: int
    driver_a_wins: int
    driver_b_wins: int
    driver_a_podiums: int = 0
    driver_b_podiums: int = 0
    driver_a_poles: int = 0
    driver_b_poles: int = 0
    driver_a_avg_position: float
    driver_b_avg_position: float
    driver_a_avg_grid: Optional[float] = None
    driver_b_avg_grid: Optional[float] = None
    driver_a_total_points: float
    driver_b_total_points: float
    driver_a_dnfs: int = 0
    driver_b_dnfs: int = 0
    driver_a_teammate_name: Optional[str] = None
    driver_a_teammate_diff: Optional[float] = None
    driver_b_teammate_name: Optional[str] = None
    driver_b_teammate_diff: Optional[float] = None


class PitStopStats(BaseModel):
    race_id: int
    race_name: str
    year: int
    driver_id: int
    driver_name: str
    constructor_name: str
    total_stops: int
    avg_duration_ms: Optional[float] = None
    fastest_stop_ms: Optional[int] = None
    fastest_stop_lap: Optional[int] = None


class CircuitStats(BaseModel):
    circuit_id: int
    circuit_name: str
    country: str
    total_races: int
    most_wins_driver: Optional[str] = None
    most_wins_constructor: Optional[str] = None
    avg_pit_stops: Optional[float] = None
    lap_record_time: Optional[str] = None
    lap_record_driver: Optional[str] = None
    lap_record_year: Optional[int] = None


class StandingsEntry(BaseModel):
    position: int
    driver_id: Optional[int] = None
    driver_name: Optional[str] = None
    constructor_id: Optional[int] = None
    constructor_name: Optional[str] = None
    points: float
    wins: int
