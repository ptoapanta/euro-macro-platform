"""
integrations/webhook_client.py — Webhook saliente hacia Make / Zapier
==========================================================================
Cuando la API detecta una alerta (variación % por encima del umbral),
envía un POST con el payload a la URL configurada en OUTBOUND_WEBHOOK_URL
(típicamente un "Catch Hook" de Zapier o un "Custom webhook" de Make).

Un fallo en el webhook (URL no configurada, sin conexión, timeout) NUNCA
debe romper el flujo principal de la API — por eso todo va en un
try/except y se devuelve un resultado descriptivo en vez de lanzar.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import settings  # noqa: E402


def build_webhook_payload(alertas: list[dict]) -> dict:
    """Construye el payload JSON que se envía al webhook. Función pura,
    sin I/O — testeable sin necesidad de red.
    """
    return {
        "evento": "alerta_macro_euro",
        "timestamp": datetime.utcnow().isoformat(),
        "total_alertas": len(alertas),
        "alertas": alertas,
    }


def send_alert_webhook(alertas: list[dict], webhook_url: str | None = None) -> dict:
    """Envía las alertas al webhook configurado.

    Devuelve {"enviado": bool, "detalle": str}. Nunca lanza una excepción.
    """
    url = webhook_url or settings.outbound_webhook_url
    if not url:
        return {"enviado": False, "detalle": "OUTBOUND_WEBHOOK_URL no configurado en .env"}

    payload = build_webhook_payload(alertas)

    try:
        import requests
        resp = requests.post(url, json=payload, timeout=8)
        resp.raise_for_status()
        return {"enviado": True, "detalle": f"HTTP {resp.status_code}"}
    except Exception as exc:  # noqa: BLE001 — cualquier fallo de red no debe propagar
        return {"enviado": False, "detalle": str(exc)}
