# 4. Funcionalidades principales

## 4.1 Catálogo y observaciones de indicadores

Alta, consulta y filtrado de indicadores macroeconómicos (por categoría,
estado activo/inactivo) y de sus observaciones históricas (por indicador,
rango de fechas, tipo de dato, estado), con paginación.

## 4.2 Cálculo automático de variación %

Cada vez que se registra una nueva observación, el sistema calcula
automáticamente la variación porcentual respecto a la observación
anterior del mismo indicador — no requiere que el usuario la calcule.

## 4.3 Analítica de series

- **Volatilidad** (por periodo y anualizada) de cualquier indicador o de
  todos a la vez.
- **Tendencia** (medias móviles corta/larga, dirección alcista/bajista/
  estable) por indicador.
- **Correlaciones** entre todos los indicadores activos, o un subconjunto
  elegido, alineando series de distinta frecuencia.

## 4.4 Alertas automáticas

Cuando la variación de un indicador supera el umbral configurado
(`ALERT_THRESHOLD_PCT`, 1% por defecto), el sistema:
1. La marca como alerta con severidad moderada o alta (según supere 1x o
   3x el umbral).
2. La muestra en el dashboard (pestaña Alertas) y en `/api/reports/summary`.
3. La envía automáticamente al webhook externo configurado, si existe.

## 4.5 Dashboard interactivo

Cinco vistas: resumen con KPIs, series temporales con gráfico interactivo,
mapa de calor de correlaciones, panel de alertas activas, y un panel de
administración para dar de alta indicadores y observaciones sin necesidad
de usar la API directamente.

## 4.6 Reportes PDF

Generación bajo demanda (desde el dashboard o directamente vía
`GET /api/reports/pdf`) de un reporte con el resumen por categoría, las
alertas activas y los últimos valores de todos los indicadores.

## 4.7 Integración con Make/Zapier

Cualquier alerta detectada se reenvía automáticamente como webhook a una
URL configurable, lo que permite conectar la plataforma con flujos de
Zapier o Make para notificaciones por correo, Slack, registro en hojas de
cálculo, etc., sin modificar el código de la plataforma.

## 4.8 Seguridad básica

Todos los endpoints de la API (excepto el health check) requieren un
header `X-API-Key` válido. Las credenciales y URLs sensibles se manejan
vía variables de entorno, nunca hardcodeadas ni versionadas en Git.
