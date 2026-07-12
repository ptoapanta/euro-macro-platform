"""
data_layer/seed_data.py — Población inicial de la base de datos
===================================================================
Dos fuentes conviven a propósito, y quedan documentadas en cada
DataPoint mediante 'referencia_fuente':
  - EUR/USD  -> datos reales descargados de Yahoo Finance (market_client.py)
  - resto    -> series simuladas con caminata aleatoria realista,
                porque sus fuentes oficiales (BCE/Eurostat) requieren
                credenciales que están fuera del alcance de esta entrega.
"""

from __future__ import annotations

import random
import sys
from datetime import date, timedelta
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from data_layer.db import get_session  # noqa: E402
from data_layer.market_client import fetch_eurusd_history  # noqa: E402
from data_layer.models import DataPoint, MacroIndicator  # noqa: E402
from config import settings  # noqa: E402


INDICADORES_BASE = [
    dict(
        codigo="EURUSD", nombre="Tipo de cambio EUR/USD",
        categoria="tipo_cambio", unidad="USD por EUR",
        frecuencia="diaria", fuente_datos="Yahoo Finance",
        descripcion="Precio de 1 euro en dólares estadounidenses",
    ),
    dict(
        codigo="CPI_EA", nombre="IPC Armonizado Eurozona",
        categoria="inflacion", unidad="% interanual",
        frecuencia="mensual", fuente_datos="Eurostat (simulado)",
        descripcion="Índice de Precios al Consumo Armonizado de la zona euro",
    ),
    dict(
        codigo="GDP_EA", nombre="PIB Eurozona",
        categoria="pib", unidad="miles de millones EUR",
        frecuencia="trimestral", fuente_datos="Eurostat (simulado)",
        descripcion="Producto Interior Bruto de los 20 países de la zona euro",
    ),
    dict(
        codigo="UNEMP_EA", nombre="Tasa de Desempleo Eurozona",
        categoria="empleo", unidad="%",
        frecuencia="mensual", fuente_datos="Eurostat (simulado)",
        descripcion="Porcentaje de población activa desempleada en la zona euro",
    ),
    dict(
        codigo="ECB_RATE", nombre="Tipo de Interés BCE",
        categoria="politica_monetaria", unidad="%",
        frecuencia="mensual", fuente_datos="BCE (simulado)",
        descripcion="Tipo de interés de referencia del Banco Central Europeo",
    ),
]

# Parámetros: (valor_inicial, volatilidad, min_razonable, max_razonable, drift_esperado)
SIMULACION_PARAMS = {
    "CPI_EA": (2.4, 0.05, 0.0, 6.0, 0.01),      # Ligera tendencia inflacionaria
    "GDP_EA": (2950.0, 4.0, 2700.0, 3200.0, 1.5), # Crecimiento económico sostenido
    "UNEMP_EA": (6.5, 0.03, 5.5, 9.0, 0.0),     # Se mantiene sin tendencia clara
    "ECB_RATE": (3.75, 0.05, 0.0, 6.0, 0.0),    # Controlado por política monetaria
}


def seed_indicators(session) -> dict[str, MacroIndicator]:
    """Crea el catálogo de indicadores si aún no existe. Devuelve {codigo: obj}."""
    existentes = {i.codigo: i for i in session.query(MacroIndicator).all()}
    creados = dict(existentes)

    for datos in INDICADORES_BASE:
        if datos["codigo"] in existentes:
            continue
        indicador = MacroIndicator(**datos)
        session.add(indicador)
        creados[datos["codigo"]] = indicador

    session.commit()
    return creados


def _generar_serie_simulada(valor_inicial: float, volatilidad: float,
                             minimo: float, maximo: float, n_periodos: int, drift: float = 0.0) -> list[float]:
    """Caminata aleatoria acotada con tendencia (drift) para mayor realismo financiero."""
    valores = [valor_inicial]
    for _ in range(n_periodos - 1):
        # Al valor anterior le sumamos la tendencia (drift) y el shock aleatorio (gauss)
        siguiente = valores[-1] + drift + random.gauss(0, volatilidad)
        siguiente = max(minimo, min(maximo, siguiente))
        valores.append(round(siguiente, 4))
    return valores


def seed_historical_data(session, indicadores: dict[str, MacroIndicator]) -> int:
    """Genera observaciones históricas si el indicador aún no tiene ninguna.

    Devuelve el número total de DataPoint insertados.
    """
    total_insertados = 0
    hoy = date.today()

    # ── EUR/USD: intentar datos reales, si falla, simular ──
    eurusd = indicadores.get("EURUSD")
    if eurusd and not eurusd.series:
        serie_real = fetch_eurusd_history() if settings.use_real_eurusd else []

        if serie_real:
            puntos = serie_real
            fuente = "Yahoo Finance (real)"
        else:
            valores_sim = _generar_serie_simulada(1.08, 0.004, 0.95, 1.20, 180)
            fechas_sim = [hoy - timedelta(days=180 - i) for i in range(180)]
            puntos = [{"fecha": f, "valor": v} for f, v in zip(fechas_sim, valores_sim)]
            fuente = "Simulado (fallback, sin conexión a Yahoo Finance)"

        anterior = None
        for p in puntos:
            variacion = (
                round((p["valor"] - anterior) / anterior * 100, 4) if anterior else None
            )
            dp = DataPoint(
                indicator_id=eurusd.id,
                valor=p["valor"],
                valor_anterior=anterior,
                variacion_pct=variacion,
                moneda="USD",
                tipo_dato="spot",
                estado="confirmado",
                referencia_fuente=fuente,
                fecha_referencia=p["fecha"],
                periodo_label=p["fecha"].isoformat(),
            )
            session.add(dp)
            anterior = p["valor"]
            total_insertados += 1

    # ── Resto de indicadores: series simuladas con frecuencia propia ──
    frecuencia_dias = {"mensual": 30, "trimestral": 90}

    for codigo, (v0, vol, vmin, vmax, drift) in SIMULACION_PARAMS.items():
        indicador = indicadores.get(codigo)
        if not indicador or indicador.series:
            continue

        paso_dias = frecuencia_dias.get(indicador.frecuencia, 30)
        n_periodos = 24  # ~2 años de histórico
        valores = _generar_serie_simulada(v0, vol, vmin, vmax, n_periodos)
        fechas = [hoy - timedelta(days=paso_dias * (n_periodos - 1 - i)) for i in range(n_periodos)]

        anterior = None
        for fecha, valor in zip(fechas, valores):
            variacion = round((valor - anterior) / anterior * 100, 4) if anterior else None
            dp = DataPoint(
                indicator_id=indicador.id,
                valor=valor,
                valor_anterior=anterior,
                variacion_pct=variacion,
                moneda="EUR" if codigo != "UNEMP_EA" else "N/A",
                tipo_dato="spot",
                estado="confirmado",
                referencia_fuente=indicador.fuente_datos,
                fecha_referencia=fecha,
                periodo_label=fecha.strftime("%Y-%m") if indicador.frecuencia == "mensual"
                else f"{fecha.year}-Q{(fecha.month - 1)//3 + 1}",
            )
            session.add(dp)
            anterior = valor
            total_insertados += 1

    session.commit()
    return total_insertados


def run_full_seed() -> None:
    with get_session() as session:
        indicadores = seed_indicators(session)
        # refrescar para tener .series poblado tras el commit
        for ind in indicadores.values():
            session.refresh(ind)
        insertados = seed_historical_data(session, indicadores)
        print(f"✓ Indicadores en catálogo: {len(indicadores)}")
        print(f"✓ Observaciones históricas insertadas: {insertados}")


if __name__ == "__main__":
    run_full_seed()
