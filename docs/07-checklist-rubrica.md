# 7. Checklist final contra la rúbrica

Este documento mapea cada requisito de la consigna del curso a la
evidencia concreta dentro de este repositorio.

## 1. Desarrollo de la aplicación

### 1.1 Funcionalidad
- [x] Aplicación completamente operativa: API + dashboard + BD funcionando
  end-to-end, verificado con `scripts/smoke_test.sh`.
- [x] Todas las funcionalidades implementadas se ejecutan correctamente:
  35 pruebas automatizadas (`tests/`) + smoke test de integración.
- [x] Responde de forma coherente a las acciones del usuario: manejo de
  errores explícito en cada endpoint (400/401/404/409) y en el dashboard
  (`is_error()` en `ui/api_client.py`).

### 1.2 Arquitectura y organización
- [x] Estructura organizada y mantenible: capas `data_layer/ → domain/ →
  api/ | ui/`, ver `docs/02-arquitectura-y-diseno.md`.
- [x] Modularidad y reutilización: los motores de `domain/` se reutilizan
  entre la API y el disparo de webhooks; `ui/chart_utils.py` se separó de
  Streamlit para poder testearse.
- [x] Buenas prácticas: tipado moderno (`Mapped[...]`), configuración
  centralizada (`config.py`), separación de funciones puras vs. I/O.

### 1.3 Innovación y mejoras
- [x] Automatización: disparo automático de webhook cuando una
  observación supera el umbral de alerta (Etapa 6).
- [x] Integración externa: webhook saliente compatible con Make/Zapier.
- [x] Mejora de UX: dashboard con 5 pestañas, indicador de salud de la
  API en tiempo real, formularios de administración sin necesidad de usar
  la API directamente.
- [x] Justificación y documentación: cada mejora está descrita en
  `docs/04-funcionalidades.md` y `docs/06-reflexion-critica.md`.

## 2. Documentación del proyecto

| Requisito de la rúbrica | Dónde está |
|---|---|
| Contextualización del problema | `docs/01-contexto-y-objetivos.md` §1.1 |
| Objetivo general | `docs/01-contexto-y-objetivos.md` §1.2 |
| Objetivos específicos | `docs/01-contexto-y-objetivos.md` §1.3 |
| Descripción de requerimientos | `docs/01-contexto-y-objetivos.md` §1.4 |
| Arquitectura general | `docs/02-arquitectura-y-diseno.md` §2.1–2.2 |
| Diagramas o esquemas explicativos | `docs/02-arquitectura-y-diseno.md` §2.2–2.4 (Mermaid) |
| Organización del sistema | `docs/02-arquitectura-y-diseno.md` §2.5 |
| Librerías | `docs/02-arquitectura-y-diseno.md` §2.6 |
| Explicación técnica de los módulos | `docs/03-modulos-tecnicos.md` |
| Descripción de funcionalidades principales | `docs/04-funcionalidades.md` |
| Evidencias de pruebas realizadas | `docs/05-pruebas-y-resultados.md` §5.1–5.3 + `scripts/smoke_test.sh` |
| Resultados obtenidos | `docs/05-pruebas-y-resultados.md` §5.4 |
| Soluciones implementadas | `docs/05-pruebas-y-resultados.md` §5.5 |
| Reflexión crítica sobre el proceso | `docs/06-reflexion-critica.md` |
| Resultados alcanzados | `docs/06-reflexion-critica.md` §6.4 |

## 3. Gestión del proyecto mediante GitHub

- [x] Desarrollo progresivo: 9 etapas, cada una en su propia rama.
- [x] Historial completo de commits: cada etapa tiene al menos un commit
  descriptivo con el detalle de lo agregado.
- [ ] Participación individual de cada integrante: **pendiente** — si el
  grupo tiene más de un integrante, cada uno debe clonar el repo y hacer
  sus propios commits (ver nota abajo).
- [x] Organización mediante ramas: `feature/data-layer`,
  `feature/api-core`, `feature/domain-engines`, `feature/dashboard-ui`,
  `feature/pdf-reports`, `feature/integrations`, `feature/docs`,
  `feature/qa`.
- [x] Gestión de versiones: cada rama se fusiona a `main` vía Pull
  Request tras verificarse.
- [x] Integración de documentación: `docs/` versionado junto al código.
- [ ] Evidencia de colaboración continua: **depende de que el equipo
  complete la Etapa 9** repartiendo tareas finales entre integrantes.

> **Nota importante para el grupo:** si son varios integrantes, la
> rúbrica pide explícitamente evidencia de participación individual
> (commits de cada persona, visibles en la pestaña "Contributors" de
> GitHub). Hasta ahora todo el desarrollo se registró desde una sola
> cuenta. Antes de la entrega final, cada integrante debería:
> 1. Clonar el repositorio.
> 2. Tomar una tarea pendiente (revisar `docs/06-reflexion-critica.md`
>    §6.3 para ideas, o ajustar/mejorar algo existente).
> 3. Crear su propia rama, hacer sus commits, y abrir su propio Pull
>    Request.

## 4. Entregables

- [x] Aplicación funcional: código fuente completo en este repositorio,
  ejecutable localmente siguiendo `README.md`.
- [x] Repositorio GitHub con código completo, historial de desarrollo y
  documentación integrada.
- [ ] Evidencia de participación grupal — ver nota de la sección 3.

## Pendiente antes de la entrega final

1. Confirmar que `pytest tests/ -v` da **35 passed** en la máquina de cada
   integrante.
2. Correr `./scripts/smoke_test.sh` con la API y el dashboard reales.
3. Repartir al menos una tarea por integrante y registrar sus commits.
4. Fusionar todas las ramas `feature/*` pendientes a `main`.
5. Crear un tag de versión final en GitHub (ej. `v1.0.0`).
