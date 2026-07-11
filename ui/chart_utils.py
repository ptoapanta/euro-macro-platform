"""
ui/chart_utils.py — Transformaciones de datos para gráficos
================================================================
Separado de las pestañas de Streamlit a propósito: estas funciones son
puras (no importan streamlit ni hacen I/O), por lo que se pueden probar
con pytest sin necesitar streamlit instalado.
"""

from __future__ import annotations


def build_heatmap_grid(codigos: list[str], matriz: dict[str, dict[str, float | None]]) -> list[list[float | None]]:
    """Convierte la matriz {fila: {columna: valor}} en una grilla 2D en el
    mismo orden que `codigos`, lista para pasar a un heatmap de Plotly.
    """
    return [[matriz.get(fila, {}).get(col) for col in codigos] for fila in codigos]
