"""
data_layer/market_client.py — Ingesta de datos reales de mercado
===================================================================
Obtiene la cotización histórica EUR/USD desde Yahoo Finance (yfinance),
sin necesidad de API key. Es la única fuente "real" de esta primera
versión; el resto de indicadores (IPC, PIB, desempleo, tasa BCE) se
generan de forma simulada pero realista en seed_data.py, ya que sus
fuentes oficiales (BCE, Eurostat) requieren credenciales/registro.
"""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import settings  # noqa: E402


def fetch_eurusd_history(period: str | None = None) -> list[dict]:
    """Descarga la serie histórica de cierre diario EUR/USD.

    Devuelve una lista de dicts: [{"fecha": date, "valor": float}, ...]
    ordenada cronológicamente. Si yfinance no está disponible o falla
    la descarga (p. ej. sin conexión a internet), devuelve lista vacía
    y el caller debe recurrir a datos simulados.
    """
    try:
        import yfinance as yf
    except ImportError:
        print("⚠ yfinance no está instalado; usa 'pip install yfinance'.")
        return []

    ticker = settings.eurusd_ticker
    period = period or settings.eurusd_history_period

    try:
        data = yf.Ticker(ticker).history(period=period, interval="1d")
    except Exception as exc:  # noqa: BLE001
        print(f"⚠ No se pudo descargar {ticker}: {exc}")
        return []

    if data is None or data.empty:
        return []

    resultado = []
    for idx, row in data.iterrows():
        resultado.append({
            "fecha": idx.date() if hasattr(idx, "date") else date.today(),
            "valor": round(float(row["Close"]), 6),
        })
    return resultado


if __name__ == "__main__":
    # Prueba manual: python -m data_layer.market_client
    serie = fetch_eurusd_history()
    print(f"Observaciones descargadas: {len(serie)}")
    for punto in serie[-5:]:
        print(punto)
