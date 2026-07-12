"""
tests/test_webhook_client.py — Pruebas del cliente de webhook (Etapa 6)
============================================================================
"""

from __future__ import annotations

from integrations.webhook_client import build_webhook_payload, send_alert_webhook


def test_build_webhook_payload_estructura():
    alertas = [{"indicador": "EURUSD", "variacion_pct": 5.0}]
    payload = build_webhook_payload(alertas)
    assert payload["evento"] == "alerta_macro_euro"
    assert payload["total_alertas"] == 1
    assert payload["alertas"] == alertas
    assert "timestamp" in payload


def test_build_webhook_payload_sin_alertas():
    payload = build_webhook_payload([])
    assert payload["total_alertas"] == 0
    assert payload["alertas"] == []


def test_send_alert_webhook_sin_url_no_lanza_excepcion():
    resultado = send_alert_webhook([{"indicador": "TEST"}], webhook_url=None)
    assert resultado["enviado"] is False
    assert "no configurado" in resultado["detalle"].lower()


def test_send_alert_webhook_url_invalida_no_lanza_excepcion():
    """Una URL inválida/inalcanzable debe devolver enviado=False, nunca lanzar."""
    resultado = send_alert_webhook(
        [{"indicador": "TEST"}],
        webhook_url="http://dominio-que-no-existe-xyz-123.invalid/webhook",
    )
    assert resultado["enviado"] is False
    assert "detalle" in resultado
