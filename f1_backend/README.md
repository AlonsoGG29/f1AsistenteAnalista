# F1 Analytics — Backend API

Backend REST construido con **FastAPI** + **SQLAlchemy async** + **PostgreSQL**.

## Estructura del proyecto

```
f1_backend/
├── app/
│   ├── main.py              # Entrada FastAPI, CORS, lifespan
│   ├── config.py            # Settings via pydantic-settings (.env)
│   ├── db/
│   │   └── session.py       # Engine async, get_db dependency
│   ├── models/
│   │   └── f1_models.py     # Modelos ORM (espejo exacto de f1db.sql)
│   ├── schemas/
│   │   └── f1_schemas.py    # Schemas Pydantic de request/response
│   ├── services/
│   │   ├── query_service.py    # Consultas básicas (pilotos, equipos…)
│   │   └── analysis_service.py # Análisis (vueltas, pit stops, h2h…)
│   └── routers/
│       ├── queries.py       # Endpoints /api/*
│       └── analysis.py      # Endpoints /api/analysis/*
├── tests/
│   └── test_endpoints.py
├── requirements.txt
└── .env.example
```

## Instalación

```bash
# 1. Crear entorno virtual
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 2. Instalar dependencias
pip install -r requirements.txt

# 3. Configurar variables de entorno
cp .env.example .env
# Editar .env con tu DATABASE_URL

# 4. Arrancar el servidor
uvicorn app.main:app --reload
```

La API queda disponible en `http://localhost:8000`.
Documentación interactiva (Swagger): `http://localhost:8000/docs`

## Endpoints disponibles

### Consultas básicas

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/drivers` | Lista de pilotos. Params: `search`, `nationality`, `page`, `page_size` |
| GET | `/api/drivers/{id}` | Detalle + estadísticas totales de un piloto |
| GET | `/api/constructors` | Lista de constructores |
| GET | `/api/constructors/{id}` | Detalle + estadísticas totales |
| GET | `/api/circuits` | Lista de circuitos. Param: `country` |
| GET | `/api/circuits/{id}` | Detalle de un circuito |
| GET | `/api/races` | Lista de carreras. Params: `year`, `circuit_id` |
| GET | `/api/races/{id}/results` | Resultados completos de una carrera |
| GET | `/api/standings/drivers/{year}` | Clasificación de pilotos. Param: `after_round` |
| GET | `/api/standings/constructors/{year}` | Clasificación de constructores |

### Análisis

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/analysis/races/{id}/lap-times` | Tiempos de vuelta. Param: `driver_ids` (CSV) |
| GET | `/api/analysis/drivers/{id}/lap-progression/{year}` | Evolución de tiempos en la temporada |
| GET | `/api/analysis/races/{id}/pit-stops` | Pit stops de una carrera |
| GET | `/api/analysis/drivers/{id}/pit-stops` | Stats de pit stops de un piloto. Param: `year` |
| GET | `/api/analysis/drivers/{id}/season-stats` | Stats por temporada de un piloto |
| GET | `/api/analysis/constructors/{id}/season-stats` | Stats por temporada de un constructor |
| GET | `/api/analysis/head-to-head` | H2H entre dos pilotos. Params: `driver_a`, `driver_b`, `year` |
| GET | `/api/analysis/circuits/{id}/stats` | Estadísticas históricas de un circuito |

## Ejecutar tests

```bash
pytest tests/ -v
```

## Próximos módulos

- `app/services/ml_service.py` — predicción de fallos mecánicos y Safety Car
- `app/routers/predict.py` — endpoints `/api/predict/*`
- `app/services/ai_service.py` — integración Azure AI Foundry (chat + text-to-SQL)
- `app/routers/ai.py` — endpoints `/api/chat` y `/api/query`
