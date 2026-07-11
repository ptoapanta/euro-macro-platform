"""
domain/volatility_engine.py — Cálculo de volatilidad de indicadores
========================================================================
Separa el cálculo puro (testeable sin base de datos) de la construcción
del snapshot (que sí consulta la BD), siguiendo el patrón de "motores"
usado en toda la capa domain/.
"""

from __future__ import annotations

import math
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

# Periodos por año según la frecuencia del indicador, para anualizar la
# volatilidad de forma comparable entre series de distinta frecuencia.
PERIODOS_POR_ANIO = {
    "diaria": 252,
    "mensual": 12,
    "trimestral": 4,
}


@dataclass(frozen=True)
class VolatilitySnapshot:
    indicador_codigo: str
    indicador_nombre: str
    n_observaciones: int
    volatilidad_periodo_pct: float | None
    volatilidad_anualizada_pct: float | None
    valor_actual: float | None
    variacion_ultima_pct: float | None


def compute_volatility(variaciones_pct: list[float], periodos_por_anio: int = 252) -> tuple[float | None, float | None]:
    """Calcula la volatilidad (desviación estándar) de una serie de variaciones %.

    Devuelve (volatilidad_del_periodo, volatilidad_anualizada), ambas en
    puntos porcentuales. Requiere al menos 2 observaciones; si no,
    devuelve (None, None).
    """
    valores = [v for v in variaciones_pct if v is not None]
    if len(valores) < 2:
        return None, None

    media = sum(valores) / len(valores)
    varianza = sum((v - media) ** 2 for v in valores) / (len(valores) - 1)
    desviacion = math.sqrt(varianza)
    anualizada = desviacion * math.sqrt(periodos_por_anio)
    return round(desviacion, 4), round(anualizada, 4)


def build_volatility_snapshot(codigo: str, session=None) -> VolatilitySnapshot | None:
    """Construye el snapshot de volatilidad para un indicador desde la BD.

    Si se pasa `session`, se reutiliza (útil para tests o para agrupar
    varias consultas en una sola transacción); si no, abre una nueva.
    """
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
        if not puntos:
            return VolatilitySnapshot(
                indicador_codigo=indicador.codigo, indicador_nombre=indicador.nombre,
                n_observaciones=0, volatilidad_periodo_pct=None,
                volatilidad_anualizada_pct=None, valor_actual=None, variacion_ultima_pct=None,
            )

        variaciones = [float(p.variacion_pct) for p in puntos if p.variacion_pct is not None]
        periodos = PERIODOS_POR_ANIO.get(indicador.frecuencia, 252)
        vol_periodo, vol_anual = compute_volatility(variaciones, periodos)

        ultimo = puntos[-1]
        return VolatilitySnapshot(
            indicador_codigo=indicador.codigo,
            indicador_nombre=indicador.nombre,
            n_observaciones=len(puntos),
            volatilidad_periodo_pct=vol_periodo,
            volatilidad_anualizada_pct=vol_anual,
            valor_actual=float(ultimo.valor),
            variacion_ultima_pct=float(ultimo.variacion_pct) if ultimo.variacion_pct is not None else None,
        )

    if session is not None:
        return _build(session)
    with get_session() as s:
        return _build(s)


def build_volatility_snapshot_all(session=None) -> list[VolatilitySnapshot]:
    """Volatilidad de todos los indicadores activos."""
    from data_layer.db import get_session
    from data_layer.models import MacroIndicator

    def _build(s):
        codigos = [i.codigo for i in s.query(MacroIndicator).filter_by(activo=True).all()]
        return [snap for c in codigos if (snap := build_volatility_snapshot(c, s)) is not None]

    if session is not None:
        return _build(session)
    with get_session() as s:
        return _build(s)
