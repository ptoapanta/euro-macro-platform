"""
ui/tab_correlations.py — Pestaña de correlaciones (mapa de calor)
=====================================================================
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from ui.api_client import ApiClient, is_error
from ui.chart_utils import build_heatmap_grid


def render_correlations(client: ApiClient) -> None:
    st.subheader("🔗 Correlaciones entre indicadores")

    resp = client.get_correlations()
    if is_error(resp):
        st.error("No se pudo conectar con la API.")
        return

    codigos = resp.get("codigos", [])
    matriz = resp.get("matriz", {})

    if len(codigos) < 2 or not matriz:
        st.info("Se necesitan al menos 2 indicadores con observaciones superpuestas en el "
                 "tiempo para calcular correlaciones.")
        return

    grid = build_heatmap_grid(codigos, matriz)

    fig = go.Figure(data=go.Heatmap(
        z=grid, x=codigos, y=codigos,
        colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
        text=[[f"{v:.2f}" if v is not None else "—" for v in fila] for fila in grid],
        texttemplate="%{text}",
    ))
    fig.update_layout(title="Correlación de Pearson (variaciones %)", height=500)
    st.plotly_chart(fig, use_container_width=True)

    st.caption(f"Basado en {resp.get('n_observaciones_comunes', 0)} observaciones "
               "coincidentes en el tiempo entre todos los indicadores (con forward-fill "
               "para series de distinta frecuencia).")
