"""
tests/test_chart_utils.py — Pruebas de utilidades de gráficos (Etapa 4)
============================================================================
"""

from __future__ import annotations

from ui.chart_utils import build_heatmap_grid


def test_build_heatmap_grid_orden_correcto():
    codigos = ["A", "B"]
    matriz = {"A": {"A": 1.0, "B": 0.5}, "B": {"A": 0.5, "B": 1.0}}
    grid = build_heatmap_grid(codigos, matriz)
    assert grid == [[1.0, 0.5], [0.5, 1.0]]


def test_build_heatmap_grid_valores_faltantes_devuelve_none():
    codigos = ["A", "B", "C"]
    matriz = {"A": {"A": 1.0, "B": 0.3}, "B": {"A": 0.3, "B": 1.0}}
    grid = build_heatmap_grid(codigos, matriz)
    # C no está en la matriz -> toda su fila/columna debe ser None
    assert grid[2] == [None, None, None]
    assert grid[0][2] is None


def test_build_heatmap_grid_lista_vacia():
    assert build_heatmap_grid([], {}) == []
