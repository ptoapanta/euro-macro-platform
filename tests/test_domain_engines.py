"""
tests/test_domain_engines.py — Pruebas de la lógica pura de los motores
============================================================================
Estas pruebas NO tocan la base de datos: validan únicamente las funciones
de cálculo (compute_*), que son las que concentran la lógica de negocio.
"""

from __future__ import annotations

from domain.correlation_engine import compute_correlation_matrix
from domain.trend_engine import compute_moving_average, compute_trend_direction
from domain.volatility_engine import compute_volatility


def test_volatilidad_con_datos_insuficientes():
    assert compute_volatility([0.5]) == (None, None)
    assert compute_volatility([]) == (None, None)


def test_volatilidad_serie_constante_es_cero():
    vol_periodo, vol_anual = compute_volatility([1.0, 1.0, 1.0, 1.0])
    assert vol_periodo == 0.0
    assert vol_anual == 0.0


def test_volatilidad_anualizada_mayor_que_periodo():
    vol_periodo, vol_anual = compute_volatility([0.5, -0.3, 0.8, -0.6, 1.1], periodos_por_anio=252)
    assert vol_anual > vol_periodo


def test_media_movil_insuficientes_datos_devuelve_none():
    assert compute_moving_average([1, 2, 3], ventana=5) is None


def test_media_movil_calculo_correcto():
    assert compute_moving_average([10, 20, 30], ventana=3) == 20.0


def test_tendencia_alcista():
    serie = [100 + i for i in range(20)]
    pendiente, direccion = compute_trend_direction(serie)
    assert direccion == "alcista"
    assert pendiente > 0


def test_tendencia_bajista():
    serie = [100 - i for i in range(20)]
    pendiente, direccion = compute_trend_direction(serie)
    assert direccion == "bajista"
    assert pendiente < 0


def test_tendencia_estable():
    serie = [100.0] * 20
    _, direccion = compute_trend_direction(serie)
    assert direccion == "estable"


def test_tendencia_datos_insuficientes():
    _, direccion = compute_trend_direction([1, 2])
    assert direccion == "insuficientes_datos"


def test_correlacion_series_perfectamente_correlacionadas():
    serie_a = [(f"2026-01-{i:02d}", float(i)) for i in range(1, 10)]
    serie_b = [(f"2026-01-{i:02d}", float(i) * 3) for i in range(1, 10)]
    matriz = compute_correlation_matrix({"A": serie_a, "B": serie_b})
    assert abs(matriz.matriz["A"]["B"] - 1.0) < 0.01


def test_correlacion_series_inversas():
    serie_a = [(f"2026-01-{i:02d}", float(i)) for i in range(1, 10)]
    serie_b = [(f"2026-01-{i:02d}", float(-i)) for i in range(1, 10)]
    matriz = compute_correlation_matrix({"A": serie_a, "B": serie_b})
    assert abs(matriz.matriz["A"]["B"] - (-1.0)) < 0.01


def test_correlacion_con_un_solo_indicador():
    serie_a = [(f"2026-01-{i:02d}", float(i)) for i in range(1, 5)]
    matriz = compute_correlation_matrix({"A": serie_a})
    assert matriz.matriz == {}
