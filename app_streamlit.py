"""
app_streamlit.py — Punto de entrada del dashboard
=====================================================
Ejecución local:
    streamlit run app_streamlit.py

Requiere que la API (api/app.py) esté corriendo en paralelo, ya que este
dashboard consume datos exclusivamente vía HTTP (ver ui/api_client.py).
"""

from __future__ import annotations

import streamlit as st

from config import settings
from ui.api_client import ApiClient, is_error
from ui.tab_admin import render_admin
from ui.tab_alerts import render_alerts
from ui.tab_correlations import render_correlations
from ui.tab_overview import render_overview
from ui.tab_series import render_series

st.set_page_config(
    page_title="Análisis Macroeconómico del Euro",
    page_icon="💶",
    layout="wide",
)

client = ApiClient()

with st.sidebar:
    st.title("💶 Euro Macro Platform")
    st.caption(f"API: `{client.base_url}`")

    salud = client.health()
    if is_error(salud):
        st.error("⚠️ API no disponible")
        st.code("python api/app.py", language="bash")
    else:
        st.success("✓ API conectada")
        st.metric("Indicadores", salud.get("total_indicadores", 0))
        st.metric("Observaciones", salud.get("total_observaciones", 0))

    st.divider()
    st.caption("Proyecto académico — Automatización de Procesos Financieros")

st.title("Plataforma de Análisis Macroeconómico del Euro")

tab_resumen, tab_series, tab_correlaciones, tab_alertas, tab_admin = st.tabs(
    ["📊 Resumen", "📈 Series", "🔗 Correlaciones", "🚨 Alertas", "⚙️ Administración"]
)

with tab_resumen:
    render_overview(client)
with tab_series:
    render_series(client)
with tab_correlaciones:
    render_correlations(client)
with tab_alertas:
    render_alerts(client)
with tab_admin:
    render_admin(client)
