"""
domain/correlation_engine.py — Correlación entre indicadores macro
======================================================================
Usa pandas para alinear series de distinta frecuencia (diaria/mensual/
trimestral) por fecha, con forward-fill, y calcular la matriz de
correlación de Pearson sobre las variaciones porcentuales.
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parent.parent))


@dataclass(frozen=True)
class CorrelationMatrix:
    codigos: list[str]
    matriz: dict[str, dict[str, float | None]]
    n_observaciones_comunes: int


def compute_correlation_matrix(series_por_codigo: dict[str, list[tuple[str, float]]]) -> CorrelationMatrix:
    """Recibe {codigo: [(fecha_iso, variacion_pct), ...]} y devuelve la
    matriz de correlación de Pearson entre todas las series, alineadas
    por fecha con forward-fill para series de distinta frecuencia.
    """
    codigos = sorted(series_por_codigo.keys())
    if len(codigos) < 2:
        return CorrelationMatrix(codigos=codigos, matriz={}, n_observaciones_comunes=0)

    frames = []
    for codigo, puntos in series_por_codigo.items():
        if not puntos:
            continue
        df = pd.DataFrame(puntos, columns=["fecha", codigo])
        df["fecha"] = pd.to_datetime(df["fecha"])
        df = df.set_index("fecha").sort_index()
        frames.append(df)

    if len(frames) < 2:
        return CorrelationMatrix(codigos=codigos, matriz={}, n_observaciones_comunes=0)

    combinado = pd.concat(frames, axis=1).sort_index().ffill().dropna()

    if combinado.empty or len(combinado) < 3:
        return CorrelationMatrix(codigos=codigos, matriz={}, n_observaciones_comunes=len(combinado))

    corr = combinado.corr(method="pearson")
    matriz = {
        fila: {col: (round(float(corr.loc[fila, col]), 4) if pd.notna(corr.loc[fila, col]) else None)
               for col in corr.columns}
        for fila in corr.index
    }
    return CorrelationMatrix(codigos=list(corr.columns), matriz=matriz, n_observaciones_comunes=len(combinado))


def build_correlation_matrix(codigos: list[str] | None = None, session=None) -> CorrelationMatrix:
    from data_layer.db import get_session
    from data_layer.models import DataPoint, MacroIndicator

    def _build(s):
        query = s.query(MacroIndicator).filter_by(activo=True)
        if codigos:
            query = query.filter(MacroIndicator.codigo.in_(codigos))
        indicadores = query.all()

        series_por_codigo = {}
        for indicador in indicadores:
            puntos = (
                s.query(DataPoint)
                .filter_by(indicator_id=indicador.id)
                .order_by(DataPoint.fecha_referencia.asc())
                .all()
            )
            series_por_codigo[indicador.codigo] = [
                (p.fecha_referencia.isoformat(), float(p.variacion_pct))
                for p in puntos if p.variacion_pct is not None
            ]

        return compute_correlation_matrix(series_por_codigo)

    if session is not None:
        return _build(session)
    with get_session() as s:
        return _build(s)
