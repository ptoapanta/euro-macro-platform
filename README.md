# Plataforma de Análisis Macroeconómico del Euro

Proyecto académico de automatización que centraliza, procesa y visualiza
indicadores macroeconómicos clave de la eurozona (tipo de cambio EUR/USD,
inflación, PIB, desempleo, tasa de interés del BCE), con arquitectura en
capas desacopladas, API REST, dashboard interactivo y reportes automáticos.

> Proyecto construido de forma incremental. Este README se amplía en cada
> etapa de desarrollo (ver `docs/` para la documentación formal completa).

## Estado del proyecto

- [x] Etapa 0 — Preparación y repositorio
- [x] Etapa 1 — Capa de datos (modelos, seed, ingesta EUR/USD real)
- [x] Etapa 2 — API REST (Flask)
- [x] Etapa 3 — Motores de análisis (volatilidad, correlaciones, alertas)
- [x] Etapa 4 — Dashboard (Streamlit)
- [x] Etapa 5 — Reportes PDF
- [x] Etapa 6 — Integraciones externas (Make/Zapier)
- [x] Etapa 7 — Documentación formal
- [ ] Etapa 8 — Pruebas integrales
- [ ] Etapa 9 — Cierre

## Documentación

Ver [`docs/README.md`](docs/README.md) para la documentación técnica y
funcional completa: contextualización, objetivos, arquitectura, diagramas,
explicación de cada módulo, evidencias de pruebas y reflexión crítica.

## Arquitectura

```
euro_macro_platform/
├── data_layer/     # Modelos ORM, conexión a BD, ingesta de datos
├── domain/         # Motores de análisis (volatilidad, tendencias, alertas)
├── ui/             # Pestañas del dashboard Streamlit
├── reports/        # Generación de reportes PDF
├── api/            # API REST Flask
├── scripts/        # Scripts de utilidad (init_db.py, etc.)
├── tests/          # Pruebas automatizadas
├── docs/           # Documentación formal del proyecto
├── config.py       # Configuración centralizada (.env)
└── requirements.txt
```

## Instalación local

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python scripts/init_db.py
```

## Equipo

_(Completar con los nombres de los integrantes del grupo)_

## Licencia

Proyecto académico — Universidad Internacional de Valencia.
