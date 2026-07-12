"""
tests/test_pdf_generator.py — Pruebas del generador de reportes PDF (Etapa 5)
==================================================================================
"""

from __future__ import annotations

from pathlib import Path

from reports.pdf_generator import generate_summary_report


def test_genera_pdf_con_datos_completos(tmp_path):
    resumen = {"tipo_cambio": {"total_indicadores": 1, "variacion_max": 5.0,
                                "variacion_min": 5.0, "variacion_promedio": 5.0}}
    alertas = [{"indicador": "EURUSD", "nombre": "EUR/USD", "valor_actual": 1.15,
                "variacion_pct": 5.0, "fecha": "2026-01-01", "severidad": "alta"}]
    ultimos = [{"codigo": "EURUSD", "nombre": "EUR/USD", "valor": 1.15,
                "variacion_pct": 5.0, "fecha": "2026-01-01"}]

    destino = tmp_path / "reporte.pdf"
    ruta = generate_summary_report(resumen, alertas, ultimos, output_path=destino)

    assert ruta.exists()
    assert ruta.stat().st_size > 0
    assert ruta.suffix == ".pdf"


def test_genera_pdf_sin_alertas_ni_datos(tmp_path):
    """No debe fallar aunque no haya alertas ni observaciones (proyecto recién iniciado)."""
    destino = tmp_path / "reporte_vacio.pdf"
    ruta = generate_summary_report({}, [], [], output_path=destino)
    assert ruta.exists()
    assert ruta.stat().st_size > 0


def test_genera_pdf_con_ruta_por_defecto():
    """Si no se especifica output_path, debe crear el archivo dentro de reports/generated/."""
    ruta = generate_summary_report({}, [], [])
    assert ruta.exists()
    assert "generated" in str(ruta)
    ruta.unlink()  # limpieza
