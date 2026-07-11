"""
domain/trend_engine.py — Detección de tendencias mediante medias móviles
============================================================================
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

UMBRAL_PENDIENTE_ESTABLE = 0.01  # pendiente relativa por debajo de esto = "estable"


@dataclass(frozen=True)
class TrendSnapshot:
    indicador_codigo: str
    indicador_nombre: str
    media_movil_corta: float | None
    media_movil_larga: float | None
    pendiente_relativa_pct: float | None
    direccion: str  # "alcista" | "bajista" | "estable" | "insuficientes_datos"


def compute_moving_average(valores: list[float], ventana: int) -> float | None:
    """Media móvil simple de los últimos `ventana` valores."""
    if len(valores) < ventana:
        return None
    return round(sum(valores[-ventana:]) / ventana, 6)


def compute_trend_direction(valores: list[float], ventana_pendiente: int = 10) -> tuple[float | None, str]:
    """Ajusta una recta (regresión lineal simple) a los últimos N valores y
    clasifica la dirección según la pendiente relativa al valor promedio.

    Devuelve (pendiente_relativa_pct, direccion).
    """
    muestra = valores[-ventana_pendiente:]
    if len(muestra) < 3:
        return None, "insuficientes_datos"

    n = len(muestra)
    xs = list(range(n))
    media_x = sum(xs) / n
    media_y = sum(muestra) / n

    numerador = sum((xs[i] - media_x) * (muestra[i] - media_y) for i in range(n))
    denominador = sum((xs[i] - media_x) ** 2 for i in range(n))
    if denominador == 0 or media_y == 0:
        return 0.0, "estable"

    pendiente = numerador / denominador
    pendiente_relativa_pct = round((pendiente / abs(media_y)) * 100, 4)

    if pendiente_relativa_pct > UMBRAL_PENDIENTE_ESTABLE:
        direccion = "alcista"
    elif pendiente_relativa_pct < -UMBRAL_PENDIENTE_ESTABLE:
        direccion = "bajista"
    else:
        direccion = "estable"

    return pendiente_relativa_pct, direccion


def build_trend_snapshot(codigo: str, session=None, ventana_corta: int = 5, ventana_larga: int = 20) -> TrendSnapshot | None:
    from data_layer.db import get_session
    from data_layer.models import DataPoint, MacroIndicator

    def _build(s):
        indicador = s.query(MacroIndicator).filter_by(codigo=codigo).first()
        if not indicador:
            return None

        puntos = (
            s.query(DataPoint)
            .filter_by(indicator_id=indicador.id)
            .order_by(DataPoint.fecha_referencia.asc())
            .all()
        )
        valores = [float(p.valor) for p in puntos]

        media_corta = compute_moving_average(valores, ventana_corta)
        media_larga = compute_moving_average(valores, ventana_larga)
        pendiente, direccion = compute_trend_direction(valores)

        return TrendSnapshot(
            indicador_codigo=indicador.codigo,
            indicador_nombre=indicador.nombre,
            media_movil_corta=media_corta,
            media_movil_larga=media_larga,
            pendiente_relativa_pct=pendiente,
            direccion=direccion,
        )

    if session is not None:
        return _build(session)
    with get_session() as s:
        return _build(s)
