import polars as pl
import pandas as pd

class F1FeatureEngine:
    """Feature Engineering para modelos ML de F1 - Pit Stops, Neumáticos y Safety Car"""
    
    def __init__(self, raw_df):
        """
        Inicializa con dataframe crudo (pandas o polars)
        """
        if isinstance(raw_df, pd.DataFrame):
            self.df_pandas = raw_df
            self.df = pl.from_pandas(raw_df)
        else:
            self.df = raw_df
            self.df_pandas = raw_df.to_pandas() if hasattr(raw_df, 'to_pandas') else raw_df

    def build_ml_dataset(self):
        """
        Pipeline completo de feature engineering para Pit Stops y Neumáticos
        Incluye: PitStatus, EstimatedPitLoss, PrevLapStatus y todas las features avanzadas
        """
        # 1. Limpieza previa en Pandas
        df_temp = self.df_pandas.copy()
        
        # Aseguramos que PitInTime, PitOutTime y LapTime sean timedelta
        for col in ['LapTime', 'PitInTime', 'PitOutTime']:
            if col in df_temp.columns:
                df_temp[col] = pd.to_timedelta(df_temp[col], errors='coerce')

        # 2. Pasamos a Polars Lazy
        df_pl = pl.from_pandas(df_temp).lazy()
        
        return (
            df_pl
            # 3. Identificar tipo de vuelta ANTES de convertir tiempos a float
            .with_columns([
                pl.when(pl.col("PitInTime").is_not_null()).then(pl.lit("InLap"))
                .when(pl.col("PitOutTime").is_not_null()).then(pl.lit("OutLap"))
                .otherwise(pl.lit("Racing"))
                .alias("PitStatus")
            ])
            # 4. Preparación de tipos básicos
            .with_columns([
                (pl.col("LapTime").dt.total_milliseconds().cast(pl.Float64) / 1000).alias("LapTime"),
                pl.col("TyreLife").cast(pl.Float32),
                pl.col("Compound").cast(pl.Categorical),
                pl.col("TrackType").cast(pl.Categorical),
                pl.col("TrackTemp").cast(pl.Float32),
                pl.col("Rainfall").cast(pl.Int8)
            ])
            # 5. CÁLCULO DE PÉRDIDA ESTIMADA (Feature Engineering Avanzado)
            .with_columns([
                # Calculamos la media de vueltas de carrera (excluyendo In/Out laps) por GP
                pl.col("LapTime").filter(pl.col("PitStatus") == "Racing")
                .mean().over(["Year", "EventName"])
                .alias("AvgCleanLapTime")
            ])
            .with_columns([
                # Si es vuelta de box, restamos la media para ver cuánto se pierde en el Pit Lane
                pl.when(pl.col("PitStatus") != "Racing")
                .then(pl.col("LapTime") - pl.col("AvgCleanLapTime"))
                .otherwise(0.0)
                .alias("EstimatedPitLoss")
            ])
            # 6. Ingeniería de Rendimiento e Historial
            .with_columns([
                (pl.col("LapTime") - pl.col("LapTime").shift(1))
                    .over(["Year", "EventName", "Driver"]).alias("LapDelta"),
                pl.col("LapTime").rolling_mean(window_size=3)
                    .over(["Year", "EventName", "Driver"]).alias("RollingLapTime"),
                # Nueva Feature: ¿Viene el piloto de haber parado justo ahora?
                pl.col("PitStatus").shift(1).fill_null("Racing").alias("PrevLapStatus")
            ])
            # 7. TARGETS (Lo que queremos predecir)
            .with_columns([
                # Probabilidad de parada: ¿Entra en la vuelta siguiente?
                pl.col("PitInTime").is_not_null().shift(-1).fill_null(False).cast(pl.Int8).alias("target_pit"),
                # Neumático: ¿Qué compuesto pone después?
                pl.col("Compound").shift(-1).alias("target_next_tyre"),
                # Safety Car: Detectamos periodos de bandera amarilla/SC por tiempos lentos (>30% del normal)
                pl.when(pl.col("LapTime") > pl.col("AvgCleanLapTime") * 1.3)
                .then(1).otherwise(0).alias("sc_event")
            ])
            # 8. Target de SC: ¿Habrá un SC en las próximas 5 vueltas?
            .with_columns([
                pl.col("sc_event").shift(-5).rolling_max(window_size=5).fill_null(0).alias("target_sc_upcoming")
            ])
            .collect()
        )
    
    def build_ml_sc_dataset(self):
        """
        Pipeline de feature engineering para Safety Car a nivel de GP
        """
        df_pl = pl.from_pandas(self.df_pandas).lazy()
        
        return (
            df_pl
            # Aseguramos tipos de datos
            .with_columns([
                pl.col("TrackType").cast(pl.Categorical),
                pl.col("Location").cast(pl.Categorical),
                pl.col("Target_Had_SC").cast(pl.Int8)
            ])
            # Calculamos la probabilidad histórica de SC por circuito (Variable clave)
            .with_columns([
                pl.col("Target_Had_SC").mean().over("Location").alias("Circuit_Risk_Score")
            ])
            # Ajustamos el riesgo si es callejero y llueve
            .with_columns([
                pl.when((pl.col("TrackType") == "Street") & (pl.col("Rainfall_Any") == 1))
                .then(pl.col("Circuit_Risk_Score") * 1.4)
                .otherwise(pl.col("Circuit_Risk_Score"))
                .alias("Adjusted_Risk")
            ])
            .collect()
        )