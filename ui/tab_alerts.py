"""
ui/tab_alerts.py — Pestaña de alertas activas
=================================================
"""

from __future__ import annotations

import streamlit as st

from ui.api_client import ApiClient, is_error

SEVERIDAD_COLOR = {"alta": "🔴", "moderada": "🟡"}


def render_alerts(client: ApiClient) -> None:
    st.subheader("🚨 Alertas activas")

    resp = client.get_summary()
    if is_error(resp):
        st.error("No se pudo conectar con la API.")
        return

    alertas = resp.get("alertas", [])
    umbral = resp.get("umbral_alerta_pct")

    st.caption(f"Umbral configurado: variación absoluta ≥ {umbral}% dispara una alerta "
               "(configurable en `.env` vía `ALERT_THRESHOLD_PCT`).")

    if not alertas:
        st.success("No hay alertas activas en este momento. Todos los indicadores están "
                    "dentro del rango esperado.")
        return

    for alerta in alertas:
        icono = SEVERIDAD_COLOR.get(alerta.get("severidad"), "⚪")
        with st.container(border=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.markdown(f"{icono} **{alerta['indicador']}** — {alerta['nombre']}")
                st.caption(f"Fecha: {alerta['fecha']} · Severidad: {alerta['severidad']}")
            with col2:
                signo = "+" if alerta["variacion_pct"] >= 0 else ""
                st.metric("Variación", f"{signo}{alerta['variacion_pct']}%",
                          delta=f"{alerta['valor_actual']}")
