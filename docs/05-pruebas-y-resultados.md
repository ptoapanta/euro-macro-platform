# 5. Evidencias de pruebas y resultados

## 5.1 Estrategia de pruebas

Se separó deliberadamente la lógica de negocio pura (funciones `compute_*`
en `domain/`, `chart_utils.py`, `webhook_client.build_webhook_payload`) de
las funciones que dependen de la base de datos o de red. Esto permite que
la mayoría de las pruebas se ejecuten en milisegundos, sin necesitar una
base de datos real ni conexión a internet.

Para las pruebas que sí necesitan base de datos (`test_api.py`), se usa
una base SQLite **temporal y aislada** (`tests/conftest.py` fija
`DATABASE_URL` a un archivo en un directorio temporal antes de importar
cualquier módulo del proyecto), de forma que las pruebas nunca tocan ni
corrompen la base de datos real de desarrollo.

## 5.2 Inventario de pruebas automatizadas

| Archivo | Pruebas | Qué verifica |
|---|---|---|
| `tests/test_api.py` | 13 | Autenticación por API key, CRUD de indicadores y observaciones, cálculo de variación %, endpoints de series, resumen con alertas, y los 3 endpoints de analítica (volatilidad, tendencia, correlaciones) |
| `tests/test_domain_engines.py` | 12 | Lógica pura de volatilidad (casos borde: datos insuficientes, serie constante, anualización), tendencia (alcista/bajista/estable/insuficiente) y correlación (perfecta, inversa, un solo indicador) |
| `tests/test_chart_utils.py` | 3 | Transformación de la matriz de correlación a grilla para el heatmap, incluyendo valores faltantes |
| `tests/test_pdf_generator.py` | 3 | Generación de PDF con datos completos, sin datos, y con ruta por defecto |
| `tests/test_webhook_client.py` | 4 | Construcción del payload, envío sin URL configurada, envío con URL inválida — en todos los casos verificando que nunca se lance una excepción |
| **Total** | **35** | |

## 5.3 Evidencia de ejecución

Debido a que el entorno donde se desarrolló este proyecto no tuvo acceso a
internet para instalar todas las dependencias (`SQLAlchemy`, `yfinance`,
`streamlit`), la verificación se hizo en dos niveles:

1. **En el entorno de desarrollo:** se verificó la sintaxis de todos los
   módulos (`python -m py_compile`) y se ejecutó manualmente la lógica
   pura que sí tenía sus dependencias disponibles (`pandas`, `numpy`,
   `reportlab`) — incluyendo la generación real de un PDF de ejemplo y la
   validación del payload del webhook.
2. **En la máquina del desarrollador (Linux, con todas las dependencias
   instaladas):** se ejecutó la suite completa con `pytest tests/ -v`
   tras cada etapa, confirmando que las 35 pruebas pasan.

> Nota de transparencia: durante el desarrollo se reportó por error un
> conteo de "37 passed" en dos etapas intermedias. Al auditar el
> repositorio para esta documentación se detectó y corrigió el conteo real
> (35). Se deja constancia aquí como parte de la reflexión crítica del
> proceso (ver documento 6).

## 5.4 Resultados obtenidos

- Sistema funcional de extremo a extremo: ingesta → almacenamiento →
  análisis → API → dashboard → reporte → notificación externa.
- Dato real integrado (EUR/USD vía Yahoo Finance) con degradación segura a
  datos simulados si no hay conexión.
- Arquitectura verificablemente desacoplada: el dashboard puede apagarse
  sin afectar la API, y viceversa; los motores de análisis se prueban sin
  necesidad de levantar ni la API ni el dashboard.
- Integración funcional con Make/Zapier mediante webhook saliente,
  disparado automáticamente por reglas de negocio (no requiere polling
  desde la herramienta externa).

## 5.5 Soluciones implementadas ante problemas encontrados

| Problema | Solución |
|---|---|
| El proyecto base (ZIP) usaba `flask_sqlalchemy`, acoplando el modelo de datos al framework web | Se migró a SQLAlchemy puro (`db.py` con `sessionmaker` propio), permitiendo que la API, el dashboard y los scripts CLI compartan la misma capa de datos |
| Las fuentes oficiales de datos macro (BCE, Eurostat) requieren registro/credenciales fuera del alcance de la entrega | Se integró una fuente real sin credenciales (Yahoo Finance para EUR/USD) y se documentó explícitamente cuáles datos son simulados y por qué, en vez de presentarlos como reales sin aclararlo |
| Lógica de agregación y alertas duplicada entre el endpoint de resumen y lo que necesitaría el dashboard | Se extrajo a `domain/analytics_engine.py` y `domain/alert_engine.py`, reutilizada por la API y por el disparo automático de webhooks |
| Atributo `metadata` en el modelo `DataPoint` colisionaba con `Base.metadata` de SQLAlchemy | Se renombró el atributo Python a `extra_metadata`, conservando el nombre de columna `metadata` en la base de datos vía `mapped_column("metadata", ...)` |
| Prueba de webhook fallaba tras configurar una URL real en `.env` | Se corrigió el test para no depender del estado real del entorno: se usa `monkeypatch` para reemplazar el objeto `settings` completo (no se puede mutar un atributo porque es un `dataclass(frozen=True)`) |
| Sin acceso a internet en el entorno de construcción para instalar todas las dependencias | Se diseñó la lógica de negocio para ser testeable sin BD ni red siempre que fue posible, y se verificó manualmente lo que sí tenía dependencias disponibles, dejando la verificación completa documentada paso a paso para la máquina del desarrollador |
