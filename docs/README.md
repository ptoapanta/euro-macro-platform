# Documentación técnica y funcional

Este directorio contiene la documentación formal del proyecto **Plataforma de
Análisis Macroeconómico del Euro**, desarrollado como trabajo académico del
curso de Automatización.

## Índice

1. [Contextualización, objetivos y requerimientos](01-contexto-y-objetivos.md)
2. [Arquitectura general y diagramas](02-arquitectura-y-diseno.md)
3. [Explicación técnica de los módulos](03-modulos-tecnicos.md)
4. [Funcionalidades principales](04-funcionalidades.md)
5. [Evidencias de pruebas y resultados](05-pruebas-y-resultados.md)
6. [Reflexión crítica del proceso de desarrollo](06-reflexion-critica.md)
7. [Checklist final contra la rúbrica](07-checklist-rubrica.md)

## Cómo se construyó este proyecto

El desarrollo se dividió en 9 etapas incrementales, cada una en su propia
rama de Git, verificada con pruebas automatizadas antes de fusionarse a
`main`:

| Etapa | Rama | Contenido |
|---|---|---|
| 0 | `main` | Estructura del repositorio, configuración base |
| 1 | `feature/data-layer` | Modelos de datos, ingesta EUR/USD real |
| 2 | `feature/api-core` | API REST (Flask) |
| 3 | `feature/domain-engines` | Motores de volatilidad, tendencia, correlación, alertas |
| 4 | `feature/dashboard-ui` | Dashboard interactivo (Streamlit) |
| 5 | `feature/pdf-reports` | Generación de reportes PDF |
| 6 | `feature/integrations` | Webhook saliente hacia Make/Zapier |
| 7 | `feature/docs` | Esta documentación |
| 8 | `feature/qa` | Pruebas integrales y checklist final |

El historial de commits de cada rama, visible en GitHub, es en sí mismo
evidencia de la construcción progresiva del sistema.
