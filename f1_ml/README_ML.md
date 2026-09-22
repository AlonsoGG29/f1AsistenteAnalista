# 🤖 F1 ML Module - Pipeline Completo

## 📋 Descripción General

Módulo de Machine Learning para predicciones en Fórmula 1 usando **FastF1**, **Polars**, y **XGBoost**. Integra el contenido completo de los notebooks (`mlf1_pit.ipynb` y `mlf1_sc.ipynb`) en archivos Python ejecutables.

## 🏗️ Arquitectura

```
f1_ml/
├── features.py          # Feature Engineering (Polars)
├── ingestion.py         # Ingesta de datos (FastF1)
├── trainer.py           # Entrenamiento de modelos (XGBoost)
├── quick_train.py       # Script de ejecución rápida
├── models/              # Modelos serializados (.joblib)
│   ├── pit_predictor.joblib
│   ├── tyre_predictor.joblib
│   ├── sc_predictor.joblib
│   └── tyre_mapping.joblib
└── notebooks/           # Notebooks originales (referencia)
    ├── mlf1_pit.ipynb
    └── mlf1_sc.ipynb
```

## 📊 Tres Modelos Principales

### 1️⃣ **Pit Stop Predictor** (`pit_predictor.joblib`)
- **Tipo**: Clasificación binaria (XGBClassifier)
- **Nivel de datos**: Por vuelta (lap-level)
- **Entrada**: 9 features (Year, TyreLife, LapTime, LapDelta, RollingLapTime, TrackTemp, Rainfall, TrackType, Compound)
- **Output**: Probabilidad de parada en próxima vuelta
- **Features clave**:
  - `EstimatedPitLoss`: Pérdida de tiempo estimada en pit lane
  - `PrevLapStatus`: Si viene de salida de boxes (OutLap)

### 2️⃣ **Tyre Strategy Recommender** (`tyre_predictor.joblib` + `tyre_mapping.joblib`)
- **Tipo**: Clasificación multi-clase (XGBClassifier)
- **Nivel de datos**: Por vuelta
- **Entrada**: Mismas 9 features que Pit Stop
- **Output**: 
  - Probabilidades para cada compuesto (HARD, MEDIUM, SOFT, INTERMEDIATE, WET)
  - Mapeo de índices a nombres (`tyre_mapping.joblib`)
- **Features especiales**:
  - Detección automática de condiciones de lluvia
  - Boost heurístico para INTERMEDIATE/WET cuando llueve

### 3️⃣ **Safety Car Risk Predictor** (`sc_predictor.joblib`)
- **Tipo**: Clasificación binaria (XGBClassifier)
- **Nivel de datos**: Por Gran Premio (race-level)
- **Entrada**: 5 features (Circuit_Risk_Score, Adjusted_Risk, TrackType, Rainfall_Any, TrackTemp_Avg)
- **Output**: Probabilidad de SC/VSC/Red Flag
- **Features especiales**:
  - `Circuit_Risk_Score`: Media histórica de incidentes por circuito
  - `Adjusted_Risk`: Riesgo ajustado por condiciones (callejero + lluvia = 1.4x)

## 🔄 Pipeline de Ejecución

### Ingesta (2-5 horas primera vez)
```python
from ingestion import F1DataIngestor, F1SafetyCarIngestor

# Descargar datos de vueltas individuales
ingestor = F1DataIngestor()
data = ingestor.fetch_multiple_seasons([2023, 2024])
# Output: dataset_f1_multiaño_raw.csv (~100MB para 2 años)

# Descargar datos de Safety Car por GP
ingestor_sc = F1SafetyCarIngestor()
data_sc = ingestor_sc.fetch_sc_history([2023, 2024])
# Output: dataset_sc_future.csv (~100KB)
```

### Feature Engineering
```python
from features import F1FeatureEngine

# Pit Stops & Neumáticos (nivel de vuelta)
engine = F1FeatureEngine(data)
dataset = engine.build_ml_dataset()
# Incluye: PitStatus, EstimatedPitLoss, PrevLapStatus, targets

# Safety Car (nivel de GP)
engine_sc = F1FeatureEngine(data_sc)
dataset_sc = engine_sc.build_ml_sc_dataset()
```

### Entrenamiento
```python
from trainer import F1ModelTrainer

trainer = F1ModelTrainer(dataset)
trainer.train_pit_model()      # → pit_predictor.joblib
trainer.train_tyre_model()     # → tyre_predictor.joblib + tyre_mapping.joblib

trainer_sc = F1ModelTrainer()
trainer_sc.train_sc_model()    # → sc_predictor.joblib
```

### Ejecución Rápida
```bash
python quick_train.py
# Ejecuta TODO el pipeline automáticamente
```

## 🎯 API Backend Integration

Los modelos se exponen a través de FastAPI en `f1_backend/app/main.py`:

### Endpoints

#### 1. Pit Stop Prediction
```
POST /api/predict/pit-stop
Content-Type: application/json

{
  "Year": 2024,
  "TyreLife": 15,
  "LapTime": "1:32.500",        # format: min:ss.ms o float (segundos)
  "LapDelta": 0.3,
  "RollingLapTime": "1:32.200",
  "TrackTemp": 35,
  "Rainfall": 0,
  "TrackType": "Permanent",
  "Compound": "MEDIUM"
}

Response:
{
  "probability": 0.72,
  "label": true,
  "confidence": "alta",
  "description": "Probabilidad de parada en la próxima vuelta"
}
```

#### 2. Tyre Strategy
```
POST /api/predict/tyre-strategy
# Mismos parámetros que pit-stop

Response:
[
  {"compound": "SOFT", "probability": 0.45},
  {"compound": "MEDIUM", "probability": 0.35},
  {"compound": "HARD", "probability": 0.20}
]
```

#### 3. Safety Car Risk
```
POST /api/predict/safety-car
Content-Type: application/json

{
  "Circuit_Risk_Score": 0.3,    # 0-1
  "Adjusted_Risk": 0.35,        # 0-1
  "TrackType": "Street",        # o "Permanent"
  "Rainfall_Any": 1,            # 0 o 1
  "TrackTemp_Avg": 30           # °C
}

Response:
{
  "probability": 0.68,
  "label": true,
  "confidence": "alta",
  "description": "Probabilidad de Safety Car en las próximas vueltas"
}
```

#### 4. Model Status
```
GET /api/predict/status

Response:
{
  "pit_stop": "ready",
  "tyre_strategy": "ready",
  "safety_car": "ready",
  "models_directory": "/path/to/models/",
  "pit_features": [...],
  "sc_features": [...]
}
```

## 🖥️ Frontend Integration

La página `f1_frontend/src/pages/Predictions.jsx` consume estos endpoints con:

- **Formularios interactivos** con validación en tiempo real
- **Visualización de probabilidades** con barras de progreso
- **Estado de confianza** (alta/media/baja)
- **Soporte para 3 compuestos + lluvia** (INTERMEDIATE, WET)
- **Circuit Risk Scoring** para Safety Car

## 📈 Datos de Entrenamiento

| Modelo | Datos | Período | Registros |
|--------|-------|---------|-----------|
| Pit Stop | Vueltas individuales | 2020-2024 | ~500k |
| Tyre | Cambios de neumáticos | 2020-2024 | ~50k |
| Safety Car | GPs completos | 2020-2024 | ~400 |

## 🔧 Mantenimiento

### Reentrenamiento
```bash
# Borrar modelos antiguos
rm f1_ml/models/*.joblib

# Ejecutar pipeline completo
cd f1_ml
python quick_train.py
```

### Troubleshooting

**"Model not found" error**
- Ejecutar `quick_train.py` para entrenar
- Verificar ruta en `f1_backend/app/services/ml_service.py`

**Rate limit en FastF1**
- `ingestion.py` incluye manejo automático de reintentos (5x con backoff exponencial)
- Esperar 60+ segundos entre intentos

**Features faltantes**
- `F1FeatureEngine._prepare_features()` llena valores por defecto
- Verificar que `dataset_f1_multiaño_raw.csv` tiene todas las columnas

## 📚 Referencias

- **FastF1**: https://docs.fastf1.dev/
- **Polars**: https://www.pola.rs/
- **XGBoost**: https://xgboost.readthedocs.io/
- **Notebooks originales**: `/notebooks/mlf1_pit.ipynb`, `/notebooks/mlf1_sc.ipynb`

## 🎓 Conceptos Clave

### PitStatus Classification
```python
- "Racing"   → Vuelta normal de carrera
- "InLap"    → Entra a boxes (pierde tiempo)
- "OutLap"   → Sale de boxes (tiempo muy bajo, outlier)
```

### Circuit Risk Scoring
```
risk = mean(SC_events_history) 
      × 1.4 if (is_street_circuit AND rainfall)
      else 1.0
```

### Confidence Levels
```
- alta   → |probability - threshold| > 0.25-0.30
- media  → entre valores
- baja   → cerca del threshold
```

---

**Última actualización**: Mayo 2026 | Datos hasta: Temporada 2024
