# F1 Analytics — Módulo ML

Tres modelos de predicción integrados en el backend FastAPI.

## Estructura

```
f1_ml/
├── scripts/
│   ├── explore_race_events.py    # Paso 0: inspeccionar el dataset jtrotman
│   ├── feature_engineering.py   # Construcción de features para los 3 modelos
│   └── train_models.py          # Entrenamiento + evaluación + persistencia
├── app/
│   ├── services/
│   │   └── ml_service.py        # Inferencia (carga modelos, expone predict_*)
│   ├── schemas/
│   │   └── ml_schemas.py        # Schemas Pydantic request/response
│   └── routers/
│       └── predict.py           # Endpoints /api/predict/*
├── notebooks/
│   └── exploracion_modelos.ipynb
├── models_trained/              # Generado al entrenar (.joblib + metrics.json)
└── requirements_ml.txt
```

## Workflow completo

### Paso 0 — Explorar Race Events (obligatorio la primera vez)

```bash
python scripts/explore_race_events.py --path /ruta/a/race_events.csv
```

Lee la salida y si los nombres de columna difieren de los esperados,
ajusta `EVENT_COL` y `RACE_ID_COL` al inicio de `feature_engineering.py`.

### Paso 1 — Instalar dependencias

```bash
pip install -r requirements_ml.txt
# XGBoost es opcional; si no instala, el código usa GradientBoostingClassifier
```

### Paso 2 — Entrenar los modelos

```bash
python scripts/train_models.py \
    --data-dir /ruta/a/ergast/csvs/ \
    --events   /ruta/a/race_events.csv \
    --out-dir  models_trained/ \
    --models   sc,dnf,pos
```

Genera en `models_trained/`:
- `safety_car_model.joblib`
- `mechanical_failure_model.joblib`
- `position_model.joblib`
- `training_metrics.json`

### Paso 3 — Integrar en el backend

Añadir al `app/main.py` del backend:

```python
from app.routers import predict          # nuevo
app.include_router(predict.router)       # nuevo
```

Copiar:
- `app/services/ml_service.py`  → `f1_backend/app/services/`
- `app/schemas/ml_schemas.py`   → `f1_backend/app/schemas/`
- `app/routers/predict.py`      → `f1_backend/app/routers/`
- `models_trained/`             → `f1_backend/models_trained/`

### Paso 4 — Verificar

```
GET /api/predict/status
```

Todos los modelos deben mostrar `"loaded": true`.

---

## Endpoints disponibles

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET  | `/api/predict/status` | Estado de carga de los 3 modelos |
| GET  | `/api/predict/feature-importance/{model}` | Importancia de features |
| POST | `/api/predict/safety-car` | P(Safety Car en la carrera) |
| POST | `/api/predict/mechanical-failure` | P(DNF mecánico del piloto) |
| POST | `/api/predict/podium` | P(top 3 del piloto) |

## Ejemplo de uso (curl)

```bash
# Safety Car — Gran Premio de Mónaco 2024
curl -X POST http://localhost:8000/api/predict/safety-car \
  -H "Content-Type: application/json" \
  -d '{
    "year": 2024, "round": 8, "season_progress": 0.38,
    "lat": 43.7347, "lng": 7.4205, "alt": 7,
    "country_sc_rate": 0.72,
    "circuit_sc_rate_3y": 0.67,
    "circuit_sc_rate_all": 0.65,
    "n_finishers": 17,
    "n_pit_stops": 52
  }'

# Respuesta esperada
{
  "probability": 0.74,
  "label": true,
  "threshold": 0.5,
  "confidence": "media",
  "model_auc": 0.71
}
```

## Notas de diseño

**Safety Car**: se entrena a nivel de carrera. El target es si hubo al menos un SC/VSC
en esa carrera según el dataset Race Events. Las features más importantes suelen ser
`circuit_sc_rate_all` y `circuit_sc_rate_3y` — el historial del circuito domina.

**Fallo mecánico**: se entrena a nivel (carrera, piloto). El target es DNF por avería,
definido usando la tabla `status` de Ergast. El threshold se baja a 0.3 porque el
coste de no detectar un fallo es mayor que el de un falso positivo.

**Podio**: clasificación binaria (top 3 o no) en lugar de regresión de posición.
Más robusta estadísticamente dado el tamaño del dataset. La posición de clasificación
(`quali_pos`) suele ser la feature más predictiva.

**Calibración**: todos los modelos usan `CalibratedClassifierCV(method="isotonic")`
para que las probabilidades sean fieles (Brier score < 0.20 es un buen objetivo).
