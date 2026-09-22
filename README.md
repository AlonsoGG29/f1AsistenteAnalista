# F1 Asistente Analista

Plataforma de análisis, visualización y predicción aplicada a datos históricos de Fórmula 1. El proyecto combina una base de datos histórica procedente de Kaggle, datos de sesiones y telemetría obtenidos con FastF1 y modelos de Machine Learning para convertir datos de carrera en información útil para el análisis deportivo y la toma de decisiones.

## Propuesta de valor

F1 Asistente Analista permite consultar qué ha ocurrido en la Fórmula 1 y detectar qué podría ocurrir durante una carrera:

- Explorar pilotos, equipos, circuitos, carreras, resultados y clasificaciones históricas.
- Comparar el rendimiento de pilotos y constructores mediante estadísticas y análisis head-to-head.
- Visualizar tiempos por vuelta, evolución de ritmo y paradas en boxes.
- Estimar en qué momento es más probable que un piloto realice su próxima parada.
- Recomendar el compuesto de neumático más adecuado según el estado de la sesión y las condiciones de pista.
- Estimar la probabilidad de que aparezca un Safety Car, un Virtual Safety Car o una bandera roja.

El sistema está pensado tanto para analistas y aficionados avanzados como para equipos de producto, medios, plataformas de contenido y perfiles comerciales que necesiten convertir datos complejos de F1 en indicadores comprensibles.

## Qué contiene el proyecto

### Aplicación web

El frontend ofrece una interfaz para consultar y visualizar:

- Dashboard general.
- Clasificaciones de pilotos y constructores.
- Fichas y estadísticas de pilotos.
- Fichas y estadísticas de constructores.
- Calendario y resultados de carreras.
- Análisis de vueltas, ritmo y pit stops.
- Predicciones de Machine Learning.
- Chat de F1 preparado para una futura integración con servicios de IA y consultas en lenguaje natural.

Está construido con React, Vite, React Router, Recharts, Axios, Tailwind CSS, Framer Motion y Lucide React.

### API y capa de datos

El backend expone una API REST con FastAPI y SQLAlchemy asíncrono. Se conecta a PostgreSQL y proporciona:

- Consultas paginadas de pilotos, constructores, circuitos y carreras.
- Resultados completos de carreras.
- Clasificaciones históricas.
- Estadísticas por temporada.
- Evolución de tiempos por vuelta.
- Historial y estadísticas de pit stops.
- Comparaciones head-to-head.
- Estadísticas históricas por circuito.
- Acceso a los tres modelos predictivos.

La documentación interactiva de la API está disponible en `/docs` cuando el backend está ejecutándose.

### Pipeline de Machine Learning

El módulo `f1_ml` contiene la ingesta, preparación de variables, entrenamiento y modelos serializados. El pipeline usa FastF1 como fuente principal de datos de sesiones para construir datasets a nivel de vuelta y de Gran Premio.

## Fuentes de datos

### Datos históricos de Kaggle

El proyecto incluye un proceso de carga a PostgreSQL mediante `insertarBBDD_molde.py`, que descarga el dataset de Fórmula 1 desde Kaggle y lo organiza en tablas relacionadas, entre ellas:

- Pilotos y constructores.
- Circuitos y carreras.
- Resultados.
- Clasificaciones.
- Tiempos por vuelta.
- Paradas en boxes.

Estos datos forman la base de las consultas históricas y de las visualizaciones de la aplicación.

### FastF1

FastF1 se utiliza para obtener información detallada de sesiones y telemetría, incluyendo tiempos por vuelta, neumáticos, condiciones de pista y eventos de carrera. Esa información se transforma mediante feature engineering para alimentar los modelos predictivos.

Los datasets generados por el módulo ML pueden incluir datos de las temporadas 2020-2024, mientras que la base histórica de la aplicación cubre un periodo más amplio, documentado en el backend hasta 2024.

## Predicciones con IA

Las predicciones actuales están implementadas con modelos `XGBClassifier` entrenados sobre datos históricos procesados. Devuelven probabilidades, etiqueta interpretada, nivel de confianza y una descripción para facilitar su consumo desde la interfaz.

### 1. Probabilidad de parada en boxes

- **Modelo:** `pit_predictor.joblib`.
- **Granularidad:** vuelta del piloto.
- **Objetivo:** estimar la probabilidad de que el piloto pare en la próxima vuelta.
- **Variables principales:** temporada, vida del neumático, tiempo de vuelta, diferencia respecto a la vuelta anterior, media móvil de ritmo, temperatura, lluvia, tipo de circuito y compuesto actual.

### 2. Recomendación del mejor neumático

- **Modelos:** `tyre_predictor.joblib` y `tyre_mapping.joblib`.
- **Granularidad:** vuelta del piloto.
- **Objetivo:** estimar qué compuesto es más conveniente en las condiciones actuales.
- **Salida:** probabilidades para `HARD`, `MEDIUM`, `SOFT`, `INTERMEDIATE` y `WET`.
- **Tratamiento específico:** detección de lluvia y ajuste de la recomendación hacia neumáticos intermedios o de lluvia cuando corresponde.

### 3. Probabilidad de Safety Car

- **Modelo:** `sc_predictor.joblib`.
- **Granularidad:** Gran Premio.
- **Objetivo:** estimar el riesgo de Safety Car, Virtual Safety Car o bandera roja.
- **Variables principales:** riesgo histórico del circuito, riesgo ajustado, tipo de trazado, presencia de lluvia y temperatura media de pista.
- **Regla de contexto:** el riesgo se ajusta especialmente para circuitos urbanos con lluvia.

Estas salidas deben interpretarse como apoyo analítico y no como certezas ni como sustituto del criterio de un estratega, comentarista o analista deportivo.

## Arquitectura

```text
                +----------------------+
                |  React + Vite        |
                |  Dashboard y vistas  |
                +----------+-----------+
                           |
                           | HTTP / JSON
                           v
                +----------------------+
                |  FastAPI             |
                |  Consultas y ML      |
                +-----+------------+---+
                      |            |
                      |            +------------------+
                      v                               v
             +----------------+              +----------------+
             | PostgreSQL     |              | Modelos ML     |
             | Histórico F1   |              | XGBoost/joblib |
             +----------------+              +--------+-------+
                                                     ^
                                                     |
                                            +--------+-------+
                                            | FastF1         |
                                            | Ingesta y      |
                                            | feature engine |
                                            +----------------+
```

## Estructura del repositorio

```text
.
├── insertarBBDD_molde.py       # Descarga y carga del histórico de Kaggle
├── f1_backend/                 # API REST y acceso a PostgreSQL
│   ├── app/
│   │   ├── main.py             # Aplicación FastAPI y endpoints ML
│   │   ├── config.py           # Configuración mediante variables de entorno
│   │   ├── models/             # Modelos ORM
│   │   ├── schemas/            # Schemas de entrada y salida
│   │   ├── routers/            # Rutas de consultas y análisis
│   │   └── services/           # Lógica de negocio y servicio ML
│   ├── tests/                  # Pruebas del backend
│   └── requirements.txt
├── f1_frontend/                # Aplicación React/Vite
│   ├── src/pages/              # Dashboard, análisis, predicciones, etc.
│   ├── src/components/         # Componentes reutilizables
│   └── package.json
└── f1_ml/                     # Ingesta, feature engineering y entrenamiento
    ├── ingestion.py            # Descarga de sesiones mediante FastF1
    ├── features.py             # Construcción de variables de ML
    ├── trainer.py              # Entrenamiento de modelos
    ├── quick_train.py          # Ejecución completa del pipeline
    ├── models/                 # Modelos .joblib entrenados
    └── notebooks/              # Exploración y experimentación
```

## Tecnologías

| Capa | Tecnologías |
| --- | --- |
| Frontend | React 18, Vite, React Router, Recharts, Axios, Tailwind CSS |
| Backend | Python, FastAPI, Uvicorn, Pydantic, SQLAlchemy async |
| Base de datos | PostgreSQL, asyncpg |
| Datos F1 | Dataset histórico de Kaggle y FastF1 |
| Machine Learning | XGBoost, scikit-learn, Polars, pandas, joblib |
| Visualización y exploración | Recharts, Matplotlib, Seaborn, Jupyter |

## Puesta en marcha

### Requisitos

- Python 3.13 o compatible con las dependencias del proyecto.
- Node.js y npm.
- PostgreSQL.
- Acceso a Kaggle si se va a cargar la base de datos desde cero.
- Conexión a Internet para descargar datos con FastF1.

### 1. Configurar la base de datos

Crear una base de datos PostgreSQL llamada `f1db` y configurar las credenciales en `f1_backend/.env`:

```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/f1db
APP_ENV=development
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

Para cargar el histórico desde Kaggle, ejecutar desde la raíz:

```bash
python insertarBBDD_molde.py
```

### 2. Arrancar el backend

```bash
cd f1_backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

El backend queda disponible en `http://localhost:8000`.

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

### 3. Arrancar el frontend

En otra terminal:

```bash
cd f1_frontend
npm install
npm run dev
```

La aplicación queda disponible normalmente en `http://localhost:5173`.

### 4. Entrenar o actualizar los modelos

```bash
cd f1_ml
pip install -r requirements_ml.txt
python quick_train.py
```

La primera ingesta con FastF1 puede tardar varias horas según las temporadas solicitadas, la conexión y la caché local. Los modelos generados se guardan en `f1_ml/models/`.

## Endpoints principales

| Método | Ruta | Uso |
| --- | --- | --- |
| `GET` | `/api/drivers` | Consultar pilotos |
| `GET` | `/api/constructors` | Consultar constructores |
| `GET` | `/api/circuits` | Consultar circuitos |
| `GET` | `/api/races` | Consultar carreras |
| `GET` | `/api/standings/drivers/{year}` | Clasificación de pilotos |
| `GET` | `/api/analysis/races/{id}/lap-times` | Tiempos por vuelta |
| `GET` | `/api/analysis/races/{id}/pit-stops` | Paradas en boxes |
| `GET` | `/api/analysis/head-to-head` | Comparativa entre pilotos |
| `GET` | `/api/predict/status` | Estado de los modelos |
| `POST` | `/api/predict/pit-stop` | Probabilidad de parada |
| `POST` | `/api/predict/tyre-strategy` | Recomendación de neumáticos |
| `POST` | `/api/predict/safety-car` | Riesgo de Safety Car |

## Utilidad para negocio y usuarios comerciales

La plataforma puede servir como base para:

- **Medios y contenido deportivo:** generar análisis previos y posteriores a cada carrera con datos verificables.
- **Plataformas de entretenimiento:** ofrecer paneles interactivos y funcionalidades de predicción para aficionados.
- **Patrocinadores y marcas:** crear activaciones basadas en pilotos, equipos, circuitos y momentos clave de la carrera.
- **Analistas y departamentos de estrategia:** centralizar indicadores de ritmo, degradación, neumáticos y riesgo de neutralización.
- **Formación y divulgación:** explicar decisiones estratégicas de F1 con datos históricos y visualizaciones.

El valor comercial puede crecer incorporando históricos actualizados automáticamente, perfiles de usuario, alertas en directo, exportación de informes, modelos calibrados por circuito y conexión con fuentes oficiales o feeds live.

## Limitaciones y estado actual

- Las probabilidades dependen de la calidad, cobertura y actualidad de los datos de entrenamiento.
- FastF1 requiere descargar y procesar sesiones; la disponibilidad de datos puede variar y existen límites prácticos de tiempo y caché.
- Los modelos predicen escenarios probables, no resultados garantizados.
- Los endpoints de podio y fallo mecánico presentes en el código son demostrativos/mock y no forman parte de las tres predicciones ML principales.
- La vista de circuitos está preparada en la navegación, pero su experiencia específica continúa en desarrollo.
- Las integraciones de chat con Azure AI y text-to-SQL están contempladas como evolución del producto, no como requisito para ejecutar el núcleo analítico actual.

## Pruebas

Para ejecutar las pruebas del backend:

```bash
cd f1_backend
pytest tests/ -v
```

También puede comprobarse la conexión y el contenido de PostgreSQL con:

```bash
python verify_db.py
```

## Referencias

- [FastF1](https://docs.fastf1.dev/)
- [XGBoost](https://xgboost.readthedocs.io/)
- [Polars](https://docs.pola.rs/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://react.dev/)
