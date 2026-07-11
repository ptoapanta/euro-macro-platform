"""
ui/tab_series.py — Pestaña de series temporales
===================================================
"""

from __future__ import annotations

import plotly.graph_objects as go
import streamlit as st

from ui.api_client import ApiClient, is_error


def render_series(client: ApiClient) -> None:
    st.subheader("📈 Series temporales")

    indicadores_resp = client.get_indicators()
    if is_error(indicadores_resp):
        st.error("No se pudo conectar con la API.")
        return

    indicadores = indicadores_resp.get("indicadores", [])
    if not indicadores:
        st.info("No hay indicadores cargados todavía.")
        return

    opciones = {f"{i['codigo']} — {i['nombre']}": i["codigo"] for i in indicadores}
    seleccion = st.selectbox("Indicador", list(opciones.keys()))
    codigo = opciones[seleccion]

    serie_resp = client.get_series(codigo)
    if is_error(serie_resp) or not serie_resp.get("serie"):
        st.warning("Este indicador aún no tiene observaciones.")
        return

    serie = serie_resp["serie"]
    fechas = [p["fecha"] for p in serie]
    valores = [p["valor"] for p in serie]

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=fechas, y=valores, mode="lines+markers", name=codigo))
    fig.update_layout(
        title=f"{serie_resp['indicador']['nombre']} ({serie_resp['indicador']['unidad']})",
        xaxis_title="Fecha", yaxis_title=serie_resp["indicador"]["unidad"],
        height=450,
    )
    st.plotly_chart(fig, use_container_width=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Volatilidad**")
        vol_resp = client.get_volatility(codigo)
        if not is_error(vol_resp):
            st.write(f"Por periodo: `{vol_resp.get('volatilidad_periodo_pct')}%`")
            st.write(f"Anualizada: `{vol_resp.get('volatilidad_anualizada_pct')}%`")
    with col2:
        st.markdown("**Tendencia**")
        trend_resp = client.get_trend(codigo)
        if not is_error(trend_resp):
            emoji = {"alcista": "🔼", "bajista": "🔽", "estable": "➡️"}.get(trend_resp.get("direccion"), "❓")
            st.write(f"Dirección: {emoji} `{trend_resp.get('direccion')}`")
            st.write(f"Pendiente relativa: `{trend_resp.get('pendiente_relativa_pct')}%`")
