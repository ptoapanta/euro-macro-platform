"""
domain/analytics_engine.py — Resumen agregado por categoría
================================================================
Extrae y reutiliza la lógica de agregación por categoría que antes
vivía embebida en api/routes.py (reports_summary).
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))


@dataclass(frozen=True)
class CategorySummary:
    categoria: str
    indicadores: list[str]
    total_indicadores: int
    variacion_max: float | None
    variacion_min: float | None
    variacion_promedio: float | None


def build_summary_by_category(session=None) -> list[CategorySummary]:
    from data_layer.db import get_session
    from data_layer.models import DataPoint, MacroIndicator

    def _build(s):
        indicadores = s.query(MacroIndicator).filter_by(activo=True).all()
        agrupado: dict[str, dict] = {}

        for indicador in indicadores:
            ultimo = (
                s.query(DataPoint)
                .filter_by(indicator_id=indicador.id)
                .order_by(DataPoint.fecha_referencia.desc())
                .first()
            )
            if not ultimo:
                continue

            cat = indicador.categoria or "sin_categoria"
            agrupado.setdefault(cat, {"indicadores": [], "variaciones": []})
            agrupado[cat]["indicadores"].append(indicador.codigo)
            if ultimo.variacion_pct is not None:
                agrupado[cat]["variaciones"].append(float(ultimo.variacion_pct))

        resultado = []
        for cat, datos in agrupado.items():
            variaciones = datos["variaciones"]
            resultado.append(CategorySummary(
                categoria=cat,
                indicadores=datos["indicadores"],
                total_indicadores=len(datos["indicadores"]),
                variacion_max=max(variaciones) if variaciones else None,
                variacion_min=min(variaciones) if variaciones else None,
                variacion_promedio=round(sum(variaciones) / len(variaciones), 4) if variaciones else None,
            ))
        return resultado

    if session is not None:
        return _build(session)
    with get_session() as s:
        return _build(s)
