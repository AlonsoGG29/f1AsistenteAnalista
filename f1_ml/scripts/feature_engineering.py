"""
scripts/feature_engineering.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Construye los DataFrames de entrenamiento para los tres modelos.
Lee desde CSVs (Kaggle) o directamente desde PostgreSQL.

Ajusta las constantes de la sección CONFIGURACIÓN si los nombres
de columna de tu Race Events dataset difieren de los defaults.
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional


# ── CONFIGURACIÓN ─────────────────────────────────────────────────────────────
# Ajusta estos valores tras ejecutar explore_race_events.py

# Columna del tipo de evento en Race Events
EVENT_COL = "event_type"
# Columna del ID de carrera en Race Events
RACE_ID_COL = "raceId"
# Textos que identifican Safety Car (lowercase)
SC_LABELS = ["safety car", "sc deployed", "virtual safety car", "vsc", "red flag"]
# Textos que identifican Safety Car real (excluye VSC si quieres)
FULL_SC_LABELS = ["safety car", "sc deployed"]


# ── STATUS IDs que son DNF mecánico en Ergast ─────────────────────────────────
# Estos son los status de la tabla `status` que corresponden a averías mecánicas.
# Excluimos accidentes, colisiones, descalificaciones, etc.
MECHANICAL_DNF_STATUSES = {
    "Engine", "Gearbox", "Transmission", "Clutch", "Hydraulics",
    "Electrical", "Radiator", "Suspension", "Brakes", "Differential",
    "Fuel system", "Oil leak", "Oil pressure", "Water leak",
    "Water pressure", "Throttle", "Turbo", "Tyre", "Wheel",
    "Puncture", "Wheel nut", "Driveshaft", "ERS", "MGU-K", "MGU-H",
    "Exhaust", "Overheating", "Fire", "Power Unit", "Energy store",
    "Fuel pressure", "Fuel pump",
}


# ── 1. SAFETY CAR ─────────────────────────────────────────────────────────────

def build_safety_car_features(
    races_csv: str,
    circuits_csv: str,
    results_csv: str,
    race_events_csv: str,
    pit_stops_csv: Optional[str] = None,
) -> pd.DataFrame:
    """
    Devuelve un DataFrame a nivel de carrera con:
    - Features del circuito, temporada, historial de SC, pit stops
    - Target: had_safety_car (1/0)

    Cada fila = una carrera.
    """
    races    = pd.read_csv(races_csv)
    circuits = pd.read_csv(circuits_csv)
    results  = pd.read_csv(results_csv)
    events   = pd.read_csv(race_events_csv, low_memory=False)

    # ── Etiqueta: ¿hubo Safety Car en esta carrera? ──
    sc_mask  = events[EVENT_COL].astype(str).str.lower().str.contains(
        "|".join(SC_LABELS), na=False
    )
    races_with_sc = set(events.loc[sc_mask, RACE_ID_COL].unique())

    # ── Base: una fila por carrera ──
    df = races[["raceId", "year", "round", "circuitId"]].copy()
    df["had_safety_car"] = df["raceId"].isin(races_with_sc).astype(int)

    # ── Features de circuito ──
    circuits_feat = circuits[["circuitId", "lat", "lng", "alt", "country"]].copy()
    # Encode de país como frecuencia (evita high-cardinality)
    country_sc_rate = (
        df.merge(circuits_feat, on="circuitId", how="left")
        .groupby("country")["had_safety_car"].mean()
        .rename("country_sc_rate")
    )
    df = df.merge(circuits_feat, on="circuitId", how="left")
    df = df.merge(country_sc_rate, on="country", how="left")
    df["alt"] = df["alt"].fillna(0)

    # ── Features históricas del circuito (ventana rolling) ──
    df = df.sort_values(["circuitId", "year", "round"])
    df["circuit_sc_rate_3y"] = (
        df.groupby("circuitId")["had_safety_car"]
        .transform(lambda x: x.shift(1).rolling(3, min_periods=1).mean())
    )
    df["circuit_sc_rate_all"] = (
        df.groupby("circuitId")["had_safety_car"]
        .transform(lambda x: x.shift(1).expanding().mean())
    )

    # ── Número de pilotos que terminaron la carrera (proxy de incidentes) ──
    finishers = (
        results[results["positionOrder"].notna()]
        .groupby("raceId")["driverId"].count()
        .rename("n_finishers")
    )
    df = df.merge(finishers, on="raceId", how="left")
    df["n_finishers"] = df["n_finishers"].fillna(20)

    # ── Número de pit stops por carrera (si disponible) ──
    if pit_stops_csv:
        pit = pd.read_csv(pit_stops_csv)
        pit_count = pit.groupby("raceId").size().rename("n_pit_stops")
        df = df.merge(pit_count, on="raceId", how="left")
        df["n_pit_stops"] = df["n_pit_stops"].fillna(df["n_pit_stops"].median())
    else:
        df["n_pit_stops"] = 0

    # ── Era moderna de F1 (reglas aerodinámica / seguridad) ──
    df["is_modern_era"] = (df["year"] >= 2011).astype(int)
    df["season_progress"] = df["round"] / df.groupby("year")["round"].transform("max")

    feature_cols = [
        "year", "round", "season_progress",
        "lat", "lng", "alt",
        "country_sc_rate",
        "circuit_sc_rate_3y", "circuit_sc_rate_all",
        "n_finishers", "n_pit_stops",
        "is_modern_era",
    ]
    df[feature_cols] = df[feature_cols].fillna(0)
    df = df.dropna(subset=["had_safety_car"])

    print(f"[SC] Dataset: {len(df)} carreras | SC rate: {df['had_safety_car'].mean():.1%}")
    return df[feature_cols + ["raceId", "had_safety_car"]]


# ── 2. FALLO MECÁNICO ─────────────────────────────────────────────────────────

def build_mechanical_failure_features(
    races_csv: str,
    results_csv: str,
    status_csv: str,
    drivers_csv: str,
    constructors_csv: str,
    lap_times_csv: Optional[str] = None,
) -> pd.DataFrame:
    """
    Devuelve un DataFrame a nivel de (carrera, piloto) con:
    - Features del piloto, constructor, historial de DNFs
    - Target: mechanical_dnf (1/0)
    """
    races        = pd.read_csv(races_csv)
    results      = pd.read_csv(results_csv)
    status       = pd.read_csv(status_csv)
    drivers      = pd.read_csv(drivers_csv)
    constructors = pd.read_csv(constructors_csv)

    # ── Etiqueta: DNF mecánico ──
    status["is_mechanical"] = status["status"].isin(MECHANICAL_DNF_STATUSES).astype(int)
    results = results.merge(status[["statusId", "status", "is_mechanical"]], on="statusId")

    df = results.merge(races[["raceId", "year", "round", "circuitId"]], on="raceId")
    df = df.merge(drivers[["driverId", "nationality"]], on="driverId", how="left")
    df = df.merge(constructors[["constructorId", "nationality"]]
                  .rename(columns={"nationality": "constructor_nationality"}),
                  on="constructorId", how="left")

    df = df.sort_values(["driverId", "year", "round"])

    # ── Features históricas por piloto ──
    df["driver_dnf_rate_5r"] = (
        df.groupby("driverId")["is_mechanical"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    )
    df["driver_dnf_rate_all"] = (
        df.groupby("driverId")["is_mechanical"]
        .transform(lambda x: x.shift(1).expanding().mean())
    )
    df["driver_races_count"] = (
        df.groupby("driverId").cumcount()
    )

    # ── Features históricas por constructor ──
    df = df.sort_values(["constructorId", "year", "round"])
    constructor_dnf = (
        df.groupby(["constructorId", "raceId"])["is_mechanical"].mean()
        .reset_index()
        .rename(columns={"is_mechanical": "constructor_dnf_race_rate"})
    )
    constructor_dnf["constructor_dnf_rate_5r"] = (
        constructor_dnf.groupby("constructorId")["constructor_dnf_race_rate"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    )
    df = df.merge(
        constructor_dnf[["constructorId", "raceId", "constructor_dnf_rate_5r"]],
        on=["constructorId", "raceId"], how="left"
    )

    # ── Features de la propia carrera ──
    df["grid_position"] = df["grid"].fillna(20)
    df["season_progress"] = df["round"] / df.groupby("year")["round"].transform("max")
    df["is_modern_era"] = (df["year"] >= 2014).astype(int)  # era híbrida

    # ── Número de vueltas completadas (si hay lap_times) ──
    if lap_times_csv:
        lt = pd.read_csv(lap_times_csv)
        laps_done = lt.groupby(["raceId", "driverId"])["lap"].max().reset_index()
        laps_done.rename(columns={"lap": "laps_completed"}, inplace=True)
        df = df.merge(laps_done, on=["raceId", "driverId"], how="left")
    else:
        df["laps_completed"] = df["laps"]
    df["laps_completed"] = df["laps_completed"].fillna(0)

    feature_cols = [
        "year", "round", "season_progress", "is_modern_era",
        "grid_position", "laps_completed",
        "driver_dnf_rate_5r", "driver_dnf_rate_all", "driver_races_count",
        "constructor_dnf_rate_5r",
    ]
    df[feature_cols] = df[feature_cols].fillna(0)

    target = "is_mechanical"
    print(f"[DNF] Dataset: {len(df)} entradas | DNF mec. rate: {df[target].mean():.1%}")
    return df[feature_cols + ["raceId", "driverId", "constructorId", target]]


# ── 3. POSICIÓN FINAL ─────────────────────────────────────────────────────────

def build_position_features(
    races_csv: str,
    results_csv: str,
    qualifying_csv: str,
    constructors_csv: str,
) -> pd.DataFrame:
    """
    Devuelve DataFrame a nivel (carrera, piloto).
    Target: podium (top 3) — clasificación binaria más robusta que posición exacta.
    """
    races     = pd.read_csv(races_csv)
    results   = pd.read_csv(results_csv)
    quali     = pd.read_csv(qualifying_csv)
    constructors = pd.read_csv(constructors_csv)

    df = results.merge(races[["raceId", "year", "round", "circuitId"]], on="raceId")
    df = df.merge(constructors[["constructorId"]], on="constructorId", how="left")

    df["podium"] = (df["position"] <= 3).astype(int)
    df = df[df["position"].notna()].copy()

    df = df.sort_values(["driverId", "year", "round"])

    # ── Rolling win/podium rate por piloto ──
    df["driver_podium_rate_5r"] = (
        df.groupby("driverId")["podium"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    )
    df["driver_win_rate_all"] = (
        df.groupby("driverId")["podium"]
        .transform(lambda x: (x.shift(1) == 1).expanding().mean())
    )
    df["driver_avg_pos_5r"] = (
        df.groupby("driverId")["positionOrder"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    )

    # ── Rolling por constructor ──
    constr_podium = (
        df.groupby(["constructorId", "raceId"])["podium"].sum()
        .reset_index().rename(columns={"podium": "constr_podiums_race"})
    )
    constr_podium["constr_podium_rate_5r"] = (
        constr_podium.groupby("constructorId")["constr_podiums_race"]
        .transform(lambda x: x.shift(1).rolling(5, min_periods=1).mean())
    )
    df = df.merge(
        constr_podium[["constructorId", "raceId", "constr_podium_rate_5r"]],
        on=["constructorId", "raceId"], how="left"
    )

    # ── Posición de clasificación ──
    quali["quali_pos"] = quali["position"].fillna(20)
    df = df.merge(quali[["raceId", "driverId", "quali_pos"]], on=["raceId", "driverId"], how="left")
    df["quali_pos"] = df["quali_pos"].fillna(df["grid"].fillna(20))

    # ── Historial en este circuito ──
    circuit_hist = (
        df.groupby(["driverId", "circuitId"])["podium"]
        .apply(lambda x: x.shift(1).expanding().mean())
        .reset_index(level=[0, 1], drop=True)
        .rename("driver_circuit_podium_rate")
    )
    df["driver_circuit_podium_rate"] = circuit_hist.values

    df["season_progress"] = df["round"] / df.groupby("year")["round"].transform("max")
    df["is_modern_era"]   = (df["year"] >= 2014).astype(int)

    feature_cols = [
        "year", "round", "season_progress", "is_modern_era",
        "quali_pos",
        "driver_podium_rate_5r", "driver_win_rate_all", "driver_avg_pos_5r",
        "constr_podium_rate_5r", "driver_circuit_podium_rate",
    ]
    df[feature_cols] = df[feature_cols].fillna(0)

    print(f"[POS] Dataset: {len(df)} entradas | Podium rate: {df['podium'].mean():.1%}")
    return df[feature_cols + ["raceId", "driverId", "constructorId", "podium"]]
