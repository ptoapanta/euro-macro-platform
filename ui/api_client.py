"""
ui/api_client.py — Cliente HTTP hacia la API REST
=====================================================
El dashboard Streamlit NUNCA toca la base de datos directamente: siempre
pasa por la API, para que ambas capas queden desacopladas de verdad (se
podría desplegar la API en un servidor distinto sin tocar el dashboard).
"""

from __future__ import annotations

import sys
from pathlib import Path

import requests

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import settings  # noqa: E402


class ApiClient:
    def __init__(self, base_url: str | None = None, api_key: str | None = None, timeout: int = 10):
        self.base_url = (base_url or settings.api_base_url).rstrip("/")
        self.headers = {"X-API-Key": api_key or settings.api_key}
        self.timeout = timeout

    def _get(self, path: str, params: dict | None = None) -> dict | None:
        try:
            resp = requests.get(f"{self.base_url}{path}", headers=self.headers,
                                 params=params, timeout=self.timeout)
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.RequestException as exc:
            return {"_error": str(exc)}

    def _post(self, path: str, payload: dict) -> dict | None:
        try:
            resp = requests.post(f"{self.base_url}{path}", headers=self.headers,
                                  json=payload, timeout=self.timeout)
            data = resp.json()
            if not resp.ok:
                return {"_error": data.get("error", f"HTTP {resp.status_code}")}
            return data
        except requests.exceptions.RequestException as exc:
            return {"_error": str(exc)}

    # ── Salud ──
    def health(self) -> dict | None:
        return self._get("/api/health")

    # ── Indicadores ──
    def get_indicators(self, categoria: str | None = None, activo: bool = True) -> dict | None:
        params = {"activo": str(activo).lower()}
        if categoria:
            params["categoria"] = categoria
        return self._get("/api/indicators", params)

    def create_indicator(self, payload: dict) -> dict | None:
        return self._post("/api/indicators", payload)

    # ── Observaciones ──
    def get_datapoints(self, **filtros) -> dict | None:
        return self._get("/api/datapoints", filtros)

    def create_datapoint(self, payload: dict) -> dict | None:
        return self._post("/api/datapoints", payload)

    def get_series(self, codigo: str) -> dict | None:
        return self._get(f"/api/series/{codigo}")

    # ── Reportes y analítica ──
    def get_summary(self) -> dict | None:
        return self._get("/api/reports/summary")

    def get_volatility(self, codigo: str | None = None) -> dict | None:
        params = {"codigo": codigo} if codigo else None
        return self._get("/api/analytics/volatility", params)

    def get_trend(self, codigo: str) -> dict | None:
        return self._get(f"/api/analytics/trend/{codigo}")

    def get_correlations(self, codigos: list[str] | None = None) -> dict | None:
        params = {"codigos": ",".join(codigos)} if codigos else None
        return self._get("/api/analytics/correlations", params)

    def download_pdf_report(self) -> bytes | None:
        """Descarga el reporte PDF. Devuelve los bytes o None si falla."""
        try:
            resp = requests.get(f"{self.base_url}/api/reports/pdf", headers=self.headers,
                                 timeout=30)
            resp.raise_for_status()
            return resp.content
        except requests.exceptions.RequestException:
            return None


def is_error(response: dict | None) -> bool:
    """True si la respuesta representa un fallo de conexión o de la API."""
    return response is None or "_error" in response
