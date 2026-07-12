# 3. Explicación técnica de los módulos desarrollados

## 3.1 `data_layer/` — Capa de datos

- **`db.py`**: expone `engine`, `SessionLocal` y el context manager
  `get_session()`. Se usa SQLAlchemy "puro" (no `flask_sqlalchemy`)
  deliberadamente, para que tanto la API como el dashboard, los scripts
  CLI y las pruebas compartan la misma capa de datos sin acoplarse al
  framework web.
- **`models.py`**: evolución directa de los modelos del proyecto base
  (`MacroIndicator`, `DataPoint`, `AuditLog`), migrados de
  `flask_sqlalchemy` a SQLAlchemy 2.0 con tipado moderno (`Mapped[...]`).
  Se conserva la relación uno-a-muchos indicador→observaciones y
  observación→auditoría.
- **`market_client.py`**: única fuente de datos real del proyecto.
  Descarga el histórico de cierre diario EUR/USD desde Yahoo Finance sin
  necesidad de API key. Si la descarga falla (sin conexión, límite de
  tasa), devuelve una lista vacía y el llamador cae a datos simulados —
  nunca lanza una excepción que interrumpa la inicialización del sistema.
- **`seed_data.py`**: puebla el catálogo de 5 indicadores y genera series
  históricas. Para EUR/USD usa `market_client`; para el resto (IPC, PIB,
  desempleo, tasa BCE), genera una caminata aleatoria acotada
  (`_generar_serie_simulada`), documentando explícitamente en
  `referencia_fuente` que son datos simulados y por qué (las fuentes
  oficiales como Eurostat/BCE requieren credenciales fuera del alcance de
  esta entrega).

## 3.2 `domain/` — Motores de análisis

Cada motor separa **funciones de cálculo puras** (sin dependencias de la
base de datos, fácilmente testeables) de **funciones "snapshot"** que sí
consultan la BD:

- **`volatility_engine.py`**: `compute_volatility()` calcula la desviación
  estándar de una serie de variaciones % y la anualiza según la
  frecuencia del indicador (252 para diaria, 12 mensual, 4 trimestral).
- **`trend_engine.py`**: `compute_moving_average()` y
  `compute_trend_direction()` (regresión lineal simple sobre los últimos
  N puntos) clasifican la tendencia en alcista/bajista/estable.
- **`correlation_engine.py`**: `compute_correlation_matrix()` usa
  `pandas` para alinear por fecha series de distinta frecuencia
  (forward-fill) y calcular la matriz de correlación de Pearson.
- **`alert_engine.py`**: `build_alerts_snapshot()` detecta variaciones que
  superan el umbral configurado y clasifica la severidad (moderada/alta).
- **`analytics_engine.py`**: `build_summary_by_category()` agrega los
  últimos valores por categoría (máximo, mínimo, promedio de variación).

**Nota de refactorización:** en la Etapa 3, la lógica de agregación y
alertas vivía originalmente duplicada dentro del endpoint
`/api/reports/summary`. Se extrajo a `alert_engine.py` y
`analytics_engine.py` para que el endpoint solo orquestara y serializara,
eliminando la duplicación y permitiendo que el mismo cálculo se reutilice
en el disparo automático de webhooks (Etapa 6).

## 3.3 `api/` — API REST

- **`app.py`**: application factory de Flask. Middleware
  `verificar_api_key()` que exige el header `X-API-Key` en todas las
  rutas excepto `/` y `/api/health`. Inicializa las tablas (`init_db()`)
  al arrancar, pero no siembra datos — eso queda a cargo explícito de
  `scripts/init_db.py`, para no acoplar el arranque de la API a un
  proceso de carga potencialmente lento.
- **`routes.py`**: 13 endpoints agrupados en indicadores, observaciones,
  series, analítica (volatilidad/tendencia/correlaciones), reportes y
  webhooks. Cada endpoint delega el cálculo a `domain/` y solo se ocupa
  de validar la entrada HTTP y serializar la salida.

## 3.4 `ui/` — Dashboard

- **`api_client.py`**: única puerta de entrada del dashboard hacia los
  datos. Todos los métodos capturan `requests.exceptions.RequestException`
  y devuelven `{"_error": ...}` en vez de lanzar, para que cada pestaña
  pueda mostrar un mensaje de error controlado si la API no responde.
- **`chart_utils.py`**: transformación de la matriz de correlación
  (diccionario anidado) a una grilla 2D para el heatmap de Plotly. Se
  separó deliberadamente de `tab_correlations.py` porque no depende de
  Streamlit, lo que permite probarla con `pytest` sin necesitar
  `streamlit` instalado.
- **5 pestañas** (`tab_overview`, `tab_series`, `tab_correlations`,
  `tab_alerts`, `tab_admin`): cada una es una función `render_*(client)`
  independiente, orquestada desde `app_streamlit.py` mediante `st.tabs`.

## 3.5 `reports/` — Generación de PDF

- **`pdf_generator.py`**: usa `reportlab`/Platypus para construir un
  documento con tres tablas (resumen por categoría, alertas activas con
  color por severidad, últimos valores). Sigue explícitamente la
  recomendación de no usar caracteres Unicode de sub/superíndice en
  `reportlab` (se listó como advertencia conocida en la guía de la
  librería), aunque este reporte en particular no los necesita.

## 3.6 `integrations/` — Webhook saliente

- **`webhook_client.py`**: `build_webhook_payload()` (función pura,
  testeable sin red) construye el JSON; `send_alert_webhook()` lo envía
  por POST a `OUTBOUND_WEBHOOK_URL`. Diseñado para **nunca** propagar una
  excepción: cualquier fallo de red o configuración ausente se traduce en
  `{"enviado": false, "detalle": "..."}`, para que un problema con
  Make/Zapier no tumbe la creación de una observación en la API.
- El disparo es automático: `POST /api/datapoints` evalúa la variación
  recién calculada y, si supera el umbral, llama a `send_alert_webhook()`
  antes de responder al cliente.

## 3.7 `scripts/init_db.py`

Punto de entrada CLI que encadena `init_db()` (creación de tablas) y
`run_full_seed()` (población de datos). Es idempotente: si las tablas ya
existen y los indicadores ya tienen observaciones, no duplica datos.
