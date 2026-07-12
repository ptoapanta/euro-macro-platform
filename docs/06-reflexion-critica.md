# 6. Reflexión crítica sobre el proceso de desarrollo

## 6.1 Decisiones que funcionaron bien

**Separar lógica pura de lógica con I/O desde el principio.** Diseñar cada
motor de `domain/` con una función `compute_*` sin dependencias de base de
datos y una función `build_*_snapshot` que sí las tiene, resultó ser la
decisión con mejor retorno del proyecto: permitió verificar buena parte de
la lógica de negocio incluso en un entorno sin todas las dependencias
instaladas, y facilita agregar pruebas nuevas sin necesitar levantar toda
la pila.

**Desacoplar el dashboard de la base de datos.** Obligar a que
`ui/api_client.py` sea la única puerta de entrada, en vez de que Streamlit
importe `data_layer` directamente (que habría sido más rápido de escribir),
pagó dividendos en la Etapa 6: agregar el webhook no requirió tocar el
dashboard en absoluto.

**Construir por etapas verificables en ramas separadas.** Cada etapa
dejó un artefacto probado antes de empezar la siguiente, lo que hizo más
fácil detectar en qué momento se introducía un problema (como el de la
prueba del webhook en la Etapa 6).

## 6.2 Limitaciones encontradas

**Entorno de desarrollo sin acceso a internet.** No fue posible instalar
`SQLAlchemy`, `yfinance` ni `streamlit` en el entorno donde se escribió el
código, por lo que buena parte de la verificación real (no solo de
sintaxis) tuvo que delegarse a la máquina del desarrollador. Esto es una
limitación real del proceso: el código se validó por revisión cuidadosa y
pruebas parciales antes de la primera ejecución completa, en vez de
mediante ejecución continua.

**Datos macroeconómicos simulados para 4 de los 5 indicadores.** Las
fuentes oficiales (Eurostat, BCE) requieren registro y, en algunos casos,
acceso de pago, fuera del alcance de una entrega académica. Se optó por
ser explícito sobre qué es real y qué es simulado en vez de presentar
datos ficticios como si fueran oficiales — una decisión de honestidad
técnica que limita el valor analítico del sistema para uso en producción,
pero que es apropiada para el propósito de este ejercicio.

**Errores de conteo humano.** Durante el desarrollo se reportaron
conteos de pruebas incorrectos en dos ocasiones (ver documento 5, sección
5.3). El origen fue calcular mentalmente el acumulado en lugar de contar
directamente desde el código en cada paso. Se corrigió al auditar el
repositorio para esta documentación, pero es una lección concreta sobre
verificar en la fuente en vez de propagar sumas manuales.

## 6.3 Qué se haría diferente con más tiempo

- Integrar Eurostat/BCE de forma real (aunque sea con una capa de caché
  agresiva) en vez de simular 4 de los 5 indicadores.
- Agregar un pipeline de integración continua (GitHub Actions) que
  ejecute `pytest` automáticamente en cada push, en vez de depender de que
  el desarrollador lo corra manualmente antes de cada commit.
- Añadir pruebas de integración que sí levanten la base de datos real
  (con un contenedor SQLite temporal en CI), no solo pruebas unitarias
  con mocks.
- Versionar el esquema de la base de datos con una herramienta de
  migraciones (Alembic) en vez de `create_all()`, para soportar cambios
  futuros sin perder datos existentes.

## 6.4 Aprendizajes principales

1. La arquitectura en capas no es solo una preferencia estética: se
   notó su valor concreto cada vez que una etapa nueva (reportes,
   webhooks) se integró sin tener que modificar las etapas anteriores.
2. Diseñar para ser "testeable sin dependencias externas" desde el
   inicio es más barato que intentar añadirlo después.
3. La documentación honesta de las limitaciones (datos simulados,
   entorno sin red, errores de conteo) aporta más valor académico que
   ocultarlas — y es coherente con la reflexión crítica que pide
   explícitamente la rúbrica del curso.
