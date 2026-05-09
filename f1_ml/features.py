import polars as pl
import numpy as np

class F1FeatureEngine:
    def __init__(self, raw_df):
        # Convertimos el DataFrame de Pandas (FastF1) a Polars
        self.df = pl.from_pandas(raw_df)

    def build_ml_dataset(self):
        return (
            self.df.lazy()
            # 1. Limpieza básica y tipos
            .with_columns([
                pl.col("LapTime").dt.total_milliseconds().cast(pl.Float64) / 1000,
                pl.col("TyreLife").cast(pl.Float32),
                pl.col("Year").cast(pl.Int32),
                pl.col("Rainfall").cast(pl.Int8),
            ])
            # 2. Targets
            .with_columns([
                # Target Pit: ¿Entró en boxes en la vuelta siguiente?
                pl.col("PitInTime").is_not_null().shift(-1).fill_null(False).cast(pl.Int8).alias("target_pit"),
                # Target Tyre: ¿Qué neumático puso?
                pl.col("Compound").shift(-1).alias("target_next_tyre"),
                # Target LapTime (Telemetry): Tiempo de la vuelta actual (suavizado o real)
                pl.col("LapTime").alias("target_lap_time")
            ])
            # 3. Features de Degradación y Delta
            .with_columns([
                (pl.col("LapTime") - pl.col("LapTime").shift(1)).over(["Year", "EventName", "Driver"]).alias("LapDelta")
            ])
            # 4. Features de Clima y Pista
            .with_columns([
                pl.col("TrackTemp").alias("track_temp"),
                pl.col("AirTemp").alias("air_temp")
            ])
            # 5. Contexto de Safety Car
            # Detectamos si hubo SC en esta vuelta basado en el tiempo (heurística)
            .with_columns([
                pl.when(pl.col("LapTime") > pl.col("LapTime").mean().over(["EventName"]) * 1.3)
                .then(1).otherwise(0).alias("sc_active")
            ])
            # Target SC: ¿Habrá SC en las próximas 3 vueltas?
            .with_columns([
                pl.col("sc_active").shift(-3).rolling_max(window_size=3).fill_null(0).alias("target_sc_upcoming")
            ])
            .collect()
        )

if __name__ == "__main__":
    import pandas as pd
    import os
    if os.path.exists('data_2023_raw.csv'):
        raw = pd.read_csv('data_2023_raw.csv')
        engine = F1FeatureEngine(raw)
        dataset = engine.build_ml_dataset()
        print(f"Dataset procesado: {dataset.shape}")
        dataset.write_csv('data_2023_features.csv')