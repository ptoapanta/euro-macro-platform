"""
domain/alert_engine.py — Alertas automáticas por variación anómala
======================================================================
Centraliza la lógica que antes vivía embebida en api/routes.py
(reports_summary), para que tanto la API como el dashboard (Etapa 4)
la reutilicen sin duplicar código.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import settings  # noqa: E402


@dataclass(frozen=True)
class Alert:
    indicador_codigo: str
    indicador_nombre: str
    valor_actual: float
    variacion_pct: float
    fecha: str
    umbral_configurado: float
    severidad: str  # "moderada" | "alta"


def clasificar_severidad(variacion_abs_pct: float, umbral: float) -> str:
    """Alta si supera 3x el umbral configurado; moderada en caso contrario."""
    return "alta" if variacion_abs_pct >= umbral * 3 else "moderada"


def build_alerts_snapshot(threshold_pct: float | None = None, session=None) -> list[Alert]:
    from data_layer.db import get_session
    from data_layer.models import DataPoint, MacroIndicator

    umbral = threshold_pct if threshold_pct is not None else settings.alert_threshold_pct

    def _build(s):
        indicadores = s.query(MacroIndicator).filter_by(activo=True).all()
        alertas = []

        for indicador in indicadores:
            ultimo = (
                s.query(DataPoint)
                .filter_by(indicator_id=indicador.id)
                .order_by(DataPoint.fecha_referencia.desc())
                .first()
            )
            if not ultimo or ultimo.variacion_pct is None:
                continue

            variacion = float(ultimo.variacion_pct)
            if abs(variacion) >= umbral:
                alertas.append(Alert(
                    indicador_codigo=indicador.codigo,
                    indicador_nombre=indicador.nombre,
                    valor_actual=float(ultimo.valor),
                    variacion_pct=variacion,
                    fecha=ultimo.fecha_referencia.isoformat(),
                    umbral_configurado=umbral,
                    severidad=clasificar_severidad(abs(variacion), umbral),
                ))

        return sorted(alertas, key=lambda a: abs(a.variacion_pct), reverse=True)

    if session is not None:
        return _build(session)
    with get_session() as s:
        return _build(s)
