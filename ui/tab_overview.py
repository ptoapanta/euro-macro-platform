"""
ui/tab_overview.py — Pestaña de resumen general
===================================================
"""

from __future__ import annotations

from datetime import datetime

import streamlit as st

from ui.api_client import ApiClient, is_error


def render_overview(client: ApiClient) -> None:
    st.subheader("📊 Resumen general")

    indicadores_resp = client.get_indicators()
    resumen_resp = client.get_summary()

    if is_error(indicadores_resp) or is_error(resumen_resp):
        st.error("No se pudo conectar con la API. Verifica que esté corriendo en "
                  f"`{client.base_url}` (`python api/app.py`).")
        return

    indicadores = indicadores_resp.get("indicadores", [])
    alertas = resumen_resp.get("alertas", [])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Indicadores activos", len(indicadores))
    col2.metric("Categorías", len(resumen_resp.get("resumen_por_categoria", {})))
    col3.metric("Alertas activas", len(alertas),
                delta=f"umbral {resumen_resp.get('umbral_alerta_pct')}%")
    col4.metric("Alertas severidad alta", sum(1 for a in alertas if a.get("severidad") == "alta"))

    st.divider()

    col_titulo, col_boton = st.columns([4, 1])
    with col_titulo:
        st.markdown("### Últimos valores por indicador")
    with col_boton:
        if st.button("📄 Generar reporte PDF"):
            pdf_bytes = client.download_pdf_report()
            if pdf_bytes:
                st.session_state["pdf_generado"] = pdf_bytes
            else:
                st.error("No se pudo generar el reporte.")

    if "pdf_generado" in st.session_state:
        nombre_archivo = f"reporte_macro_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        st.download_button(
            "⬇️ Descargar PDF", data=st.session_state["pdf_generado"],
            file_name=nombre_archivo, mime="application/pdf",
        )

    filas = []
    for ind in indicadores:
        serie_resp = client.get_series(ind["codigo"])
        if is_error(serie_resp) or not serie_resp.get("serie"):
            continue
        ultimo = serie_resp["serie"][-1]
        filas.append({
            "Código": ind["codigo"],
            "Nombre": ind["nombre"],
            "Categoría": ind.get("categoria", "—"),
            "Último valor": ultimo["valor"],
            "Variación %": ultimo.get("variacion_pct"),
            "Fecha": ultimo["fecha"],
        })

    if filas:
        st.dataframe(filas, use_container_width=True, hide_index=True)
    else:
        st.info("Aún no hay observaciones cargadas. Ejecuta `python scripts/init_db.py`.")
