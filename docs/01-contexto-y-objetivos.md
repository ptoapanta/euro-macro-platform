# 1. Contextualización, objetivos y requerimientos

## 1.1 Contextualización del problema

Los indicadores macroeconómicos de la zona euro (tipo de cambio EUR/USD,
inflación, PIB, desempleo, tipo de interés del Banco Central Europeo) se
publican en fuentes dispersas y con formatos heterogéneos: el Banco Central
Europeo, Eurostat, y proveedores financieros como Yahoo Finance manejan
frecuencias distintas (diaria, mensual, trimestral), unidades distintas, y
no ofrecen de forma nativa un panel unificado que permita a un analista, un
estudiante o un pequeño equipo de tesorería comparar la evolución conjunta
de estas variables, detectar variaciones anómalas, o recibir una alerta
automática cuando algo se sale de rango.

Replicar manualmente ese seguimiento —revisar cada fuente, calcular
variaciones, decidir si algo amerita atención y comunicarlo— es un proceso
lento, propenso a errores y difícil de mantener de forma consistente en el
tiempo.

## 1.2 Objetivo general

Desarrollar una plataforma de software que automatice la ingesta,
almacenamiento, análisis y visualización de indicadores macroeconómicos
clave de la eurozona, con capacidad de generar alertas automáticas y
notificarlas a herramientas externas de automatización (Make/Zapier), bajo
una arquitectura modular, documentada y verificada mediante pruebas
automatizadas.

## 1.3 Objetivos específicos

1. Diseñar un modelo de datos capaz de representar indicadores
   macroeconómicos de distinta frecuencia y sus observaciones históricas,
   con trazabilidad de cambios (auditoría).
2. Integrar al menos una fuente de datos real (tipo de cambio EUR/USD) sin
   depender de credenciales de pago, y complementar con datos simulados
   realistas donde la fuente oficial requiera acceso restringido.
3. Exponer los datos y el análisis mediante una API REST documentada y
   protegida por autenticación.
4. Implementar motores de análisis independientes (volatilidad, tendencia,
   correlación, alertas) desacoplados de la capa de presentación, para que
   puedan reutilizarse tanto desde la API como desde el dashboard.
5. Construir un dashboard interactivo que permita explorar series
   temporales, correlaciones y alertas sin conocimientos técnicos.
6. Generar reportes PDF descargables con el estado consolidado de los
   indicadores.
7. Conectar el sistema con una herramienta de automatización externa
   (Make o Zapier) para que las alertas puedan disparar acciones fuera de
   la plataforma (correo, mensajería, hojas de cálculo).
8. Verificar cada componente con pruebas automatizadas y documentar
   formalmente el proceso de desarrollo, incluyendo sus limitaciones y
   decisiones técnicas.

## 1.4 Descripción de requerimientos

### Requerimientos funcionales

| # | Requerimiento |
|---|---|
| RF1 | El sistema debe mantener un catálogo de indicadores macroeconómicos (código, nombre, categoría, unidad, frecuencia, fuente). |
| RF2 | El sistema debe registrar observaciones históricas por indicador, calculando automáticamente la variación % respecto a la observación anterior. |
| RF3 | El sistema debe calcular volatilidad, tendencia y correlaciones entre indicadores. |
| RF4 | El sistema debe generar alertas automáticas cuando la variación de un indicador supere un umbral configurable. |
| RF5 | El sistema debe permitir consultar todo lo anterior vía API REST autenticada. |
| RF6 | El sistema debe ofrecer un dashboard visual con series temporales, mapa de correlaciones y panel de alertas. |
| RF7 | El sistema debe generar un reporte PDF descargable con el resumen del estado actual. |
| RF8 | El sistema debe notificar alertas a un webhook externo configurable (Make/Zapier). |

### Requerimientos no funcionales

| # | Requerimiento |
|---|---|
| RNF1 | Arquitectura en capas desacopladas (datos, dominio, presentación, integraciones). |
| RNF2 | El dashboard no debe acceder nunca directamente a la base de datos; solo vía API. |
| RNF3 | Cobertura de pruebas automatizadas para la lógica de negocio (motores de análisis) independiente de la base de datos. |
| RNF4 | Configuración externalizada vía variables de entorno (`.env`), sin credenciales embebidas en el código. |
| RNF5 | El sistema debe funcionar en un entorno Linux estándar con Python 3.11+, sin dependencias de infraestructura pesada (contenedores, servicios en la nube). |
| RNF6 | Historial de desarrollo trazable en GitHub, organizado por ramas por etapa funcional. |
