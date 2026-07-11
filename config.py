"""
config.py — Configuración centralizada de la plataforma
=========================================================
Todas las variables de entorno y rutas del proyecto se resuelven aquí,
para que ningún otro módulo lea os.environ directamente.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv es opcional: si no está instalado, se sigue leyendo
    # directamente de las variables de entorno del sistema.
    pass


PROJECT_ROOT = Path(__file__).resolve().parent
DATA_DIR = PROJECT_ROOT / "data_layer" / "storage"
REPORTS_DIR = PROJECT_ROOT / "reports" / "generated"

DATA_DIR.mkdir(parents=True, exist_ok=True)
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


@dataclass(frozen=True)
class Settings:
    # Base de datos
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{DATA_DIR / 'euro_macro.db'}"
    )

    # Seguridad de la API
    api_key: str = os.getenv("API_KEY", "euro_macro_key_2024")

    # Fuente de datos reales
    use_real_eurusd: bool = os.getenv("USE_REAL_EURUSD", "true").lower() == "true"
    eurusd_ticker: str = os.getenv("EURUSD_TICKER", "EURUSD=X")
    eurusd_history_period: str = os.getenv("EURUSD_HISTORY_PERIOD", "6mo")

    # Umbral de alertas (variación % que dispara una alerta)
    alert_threshold_pct: float = float(os.getenv("ALERT_THRESHOLD_PCT", "1.0"))

    # Webhook saliente (Make / Zapier) — opcional
    outbound_webhook_url: str = os.getenv("OUTBOUND_WEBHOOK_URL", "")

    # Entorno
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    api_port: int = int(os.getenv("API_PORT", "5000"))
    streamlit_port: int = int(os.getenv("STREAMLIT_PORT", "8501"))


settings = Settings()
