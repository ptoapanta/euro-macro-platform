# 2. Arquitectura general y diagramas

## 2.1 Visión general

La plataforma sigue una **arquitectura en capas desacopladas**, inspirada
en el patrón usado en el proyecto de referencia `TRABAJO_FINAL_AUTOMATIZACION`,
pero adaptada al dominio macroeconómico y partiendo de la base de datos del
proyecto `grupo1_actividad2_automatizacion`. Cada capa solo conoce a la capa
inmediatamente inferior, nunca salta capas:

```
Dashboard (Streamlit)  →  API REST (Flask)  →  Motores de dominio  →  Capa de datos (SQLAlchemy)
     ui/                      api/                  domain/              data_layer/
```

El dashboard **nunca** consulta la base de datos directamente: todo pasa
por la API, incluso cuando ambos corren en la misma máquina. Esto permite,
sin cambiar una línea del dashboard, desplegar la API en un servidor
distinto en el futuro.

## 2.2 Diagrama de componentes

```mermaid
graph TD
    subgraph Presentacion
        UI[Dashboard Streamlit<br/>ui/]
    end

    subgraph API
        APIAPP[Flask app.py<br/>autenticacion API key]
        ROUTES[routes.py<br/>8+ endpoints REST]
    end

    subgraph Dominio
        VOL[volatility_engine]
        TREND[trend_engine]
        CORR[correlation_engine]
        ALERT[alert_engine]
        ANALYT[analytics_engine]
    end

    subgraph Datos
        DB[(SQLite<br/>euro_macro.db)]
        MODELS[models.py<br/>MacroIndicator / DataPoint / AuditLog]
        MARKET[market_client.py<br/>yfinance EUR/USD]
    end

    subgraph Integraciones
        REPORTS[pdf_generator.py]
        WEBHOOK[webhook_client.py]
        EXT[Make / Zapier]
    end

    UI -->|HTTP + X-API-Key| APIAPP
    APIAPP --> ROUTES
    ROUTES --> VOL
    ROUTES --> TREND
    ROUTES --> CORR
    ROUTES --> ALERT
    ROUTES --> ANALYT
    ROUTES --> REPORTS
    ROUTES --> WEBHOOK
    VOL --> MODELS
    TREND --> MODELS
    CORR --> MODELS
    ALERT --> MODELS
    ANALYT --> MODELS
    MODELS --> DB
    MARKET --> DB
    WEBHOOK -->|POST alerta| EXT
```

## 2.3 Diagrama entidad-relación (base de datos)

```mermaid
erDiagram
    MACRO_INDICATORS ||--o{ DATA_POINTS : "tiene"
    DATA_POINTS ||--o{ AUDIT_LOGS : "genera"

    MACRO_INDICATORS {
        int id PK
        string codigo UK
        string nombre
        string categoria
        string unidad
        string frecuencia
        string fuente_datos
        bool activo
    }
    DATA_POINTS {
        int id PK
        int indicator_id FK
        numeric valor
        numeric valor_anterior
        numeric variacion_pct
        string tipo_dato
        string estado
        date fecha_referencia
        json metadata
    }
    AUDIT_LOGS {
        int id PK
        int data_point_id FK
        string accion
        string usuario
        string ip_address
        json datos_anteriores
        json datos_nuevos
        datetime timestamp
    }
```

## 2.4 Flujo de una alerta de extremo a extremo

```mermaid
sequenceDiagram
    participant Cliente as Cliente API / Admin UI
    participant API as Flask API
    participant Alert as alert_engine
    participant Hook as webhook_client
    participant Zapier as Make / Zapier

    Cliente->>API: POST /api/datapoints (nuevo valor)
    API->>API: calcula variacion_pct
    API->>Alert: evalua umbral configurado
    alt variacion supera el umbral
        API->>Hook: send_alert_webhook(alerta)
        Hook->>Zapier: POST payload JSON
        Zapier-->>Hook: 200 OK
        Hook-->>API: {enviado: true}
    else variacion dentro de rango
        API-->>Cliente: 201 Created (sin webhook)
    end
    API-->>Cliente: 201 Created + resultado del webhook
```

## 2.5 Organización del sistema (estructura de carpetas)

```
euro-macro-platform/
├── config.py              # Configuración centralizada (.env)
├── app_streamlit.py        # Punto de entrada del dashboard
├── requirements.txt
├── .env.example
│
├── data_layer/             # Capa de datos
│   ├── db.py                #   conexión SQLAlchemy, sesión
│   ├── models.py             #   MacroIndicator, DataPoint, AuditLog
│   ├── market_client.py      #   ingesta real EUR/USD (yfinance)
│   └── seed_data.py          #   datos iniciales (reales + simulados)
│
├── domain/                 # Motores de análisis (lógica de negocio pura)
│   ├── volatility_engine.py
│   ├── trend_engine.py
│   ├── correlation_engine.py
│   ├── alert_engine.py
│   └── analytics_engine.py
│
├── api/                    # API REST
│   ├── app.py                #   app factory, middleware de API key
│   └── routes.py             #   endpoints
│
├── ui/                      # Dashboard
│   ├── api_client.py         #   cliente HTTP hacia la API
│   ├── chart_utils.py         #   transformaciones puras para gráficos
│   ├── tab_overview.py
│   ├── tab_series.py
│   ├── tab_correlations.py
│   ├── tab_alerts.py
│   └── tab_admin.py
│
├── reports/
│   └── pdf_generator.py      #   generación de reportes PDF
│
├── integrations/
│   └── webhook_client.py     #   webhook saliente Make/Zapier
│
├── scripts/
│   └── init_db.py            #   inicialización + seed de la BD
│
├── tests/                   # 37 pruebas automatizadas
└── docs/                    # esta documentación
```

## 2.6 Librerías utilizadas

| Librería | Uso en el proyecto |
|---|---|
| `SQLAlchemy` | ORM y capa de acceso a datos, independiente del framework web |
| `Flask` + `flask-cors` | API REST y CORS para el consumo desde el dashboard |
| `streamlit` | Dashboard interactivo |
| `plotly` | Gráficos de series temporales y mapa de calor de correlaciones |
| `pandas` | Alineación de series de distinta frecuencia para el cálculo de correlaciones |
| `numpy` | Soporte numérico (usado indirectamente vía pandas) |
| `yfinance` | Ingesta real de la cotización EUR/USD |
| `reportlab` | Generación de los reportes PDF |
| `requests` | Cliente HTTP del dashboard hacia la API, y del webhook hacia Make/Zapier |
| `python-dotenv` | Carga de variables de entorno desde `.env` |
| `pytest` | Framework de pruebas automatizadas |
