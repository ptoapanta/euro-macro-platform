"""
ui/tab_admin.py — Pestaña de administración (alta de indicadores y datos)
==============================================================================
"""

from __future__ import annotations

from datetime import date

import streamlit as st

from ui.api_client import ApiClient, is_error


def render_admin(client: ApiClient) -> None:
    st.subheader("⚙️ Administración")

    tab_ind, tab_dp = st.tabs(["Nuevo indicador", "Nueva observación"])

    with tab_ind:
        with st.form("form_nuevo_indicador"):
            codigo = st.text_input("Código único (ej. GDP_US)").strip().upper()
            nombre = st.text_input("Nombre descriptivo")
            categoria = st.text_input("Categoría (ej. inflacion, pib, empleo)")
            unidad = st.text_input("Unidad (ej. %, USD, miles de millones)")
            frecuencia = st.selectbox("Frecuencia", ["diaria", "mensual", "trimestral"])
            fuente = st.text_input("Fuente de datos")
            enviado = st.form_submit_button("Crear indicador")

        if enviado:
            if not codigo or not nombre:
                st.error("Código y nombre son obligatorios.")
            else:
                resp = client.create_indicator({
                    "codigo": codigo, "nombre": nombre, "categoria": categoria or None,
                    "unidad": unidad or None, "frecuencia": frecuencia,
                    "fuente_datos": fuente or None,
                })
                if is_error(resp):
                    st.error(f"Error: {resp.get('_error', 'desconocido')}")
                else:
                    st.success(f"Indicador '{resp['codigo']}' creado correctamente.")

    with tab_dp:
        indicadores_resp = client.get_indicators()
        if is_error(indicadores_resp) or not indicadores_resp.get("indicadores"):
            st.warning("Primero crea al menos un indicador.")
            return

        opciones = {f"{i['codigo']} — {i['nombre']}": i["codigo"]
                    for i in indicadores_resp["indicadores"]}

        with st.form("form_nueva_observacion"):
            seleccion = st.selectbox("Indicador", list(opciones.keys()))
            valor = st.number_input("Valor", step=0.01, format="%.4f")
            tipo_dato = st.selectbox("Tipo de dato", ["spot", "proyeccion", "revision"])
            fecha_ref = st.date_input("Fecha de referencia", value=date.today())
            fuente_ref = st.text_input("Referencia de la fuente (opcional)")
            enviado_dp = st.form_submit_button("Registrar observación")

        if enviado_dp:
            resp = client.create_datapoint({
                "indicator_codigo": opciones[seleccion],
                "valor": valor,
                "tipo_dato": tipo_dato,
                "fecha_referencia": fecha_ref.isoformat(),
                "referencia_fuente": fuente_ref or None,
            })
            if is_error(resp):
                st.error(f"Error: {resp.get('_error', 'desconocido')}")
            else:
                st.success(f"Observación registrada. Variación calculada: "
                           f"{resp.get('variacion_pct', 'N/A')}%")
