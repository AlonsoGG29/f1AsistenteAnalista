import polars as pl

class F1FeatureEngine:
    def __init__(self, raw_df):
        self.df = pl.from_pandas(raw_df)

    def build_ml_dataset(self):
        return (
            self.df.lazy()
            # 1. Preparación de tipos y limpieza
            .with_columns([
                pl.col("LapTime").dt.total_milliseconds().cast(pl.Float64) / 1000,
                pl.col("TyreLife").cast(pl.Float32),
                pl.col("Compound").cast(pl.Categorical)
            ])
            # 2. Ingeniería de "Rendimiento" (Telemetría resumida)
            .with_columns([
                # Delta de tiempo (Degradación)
                (pl.col("LapTime") - pl.col("LapTime").shift(1)).over(["Year", "EventName", "Driver"]).alias("LapDelta"),
                # Media móvil de las últimas 3 vueltas para detectar pérdida de ritmo
                pl.col("LapTime").rolling_mean(window_size=3).over(["Year", "EventName", "Driver"]).alias("RollingLapTime")
            ])
            # 3. TARGETS (Lo que queremos predecir)
            .with_columns([
                # Probabilidad de parada: ¿Entra en la vuelta siguiente?
                pl.col("PitInTime").is_not_null().shift(-1).fill_null(False).cast(pl.Int8).alias("target_pit"),
                # Neumático: ¿Qué compuesto pone después?
                pl.col("Compound").shift(-1).alias("target_next_tyre"),
                # Safety Car: Detectamos periodos de bandera amarilla/SC por tiempos lentos (>30% del normal)
                pl.when(pl.col("LapTime") > pl.col("LapTime").mean().over("EventName") * 1.3)
                .then(1).otherwise(0).alias("sc_event")
            ])
            # 4. Target de SC: ¿Habrá un SC en las próximas 5 vueltas?
            .with_columns([
                pl.col("sc_event").shift(-5).rolling_max(window_size=5).fill_null(0).alias("target_sc_upcoming")
            ])
            .collect()
        )