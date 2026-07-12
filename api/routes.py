"""
api/routes.py — Endpoints REST de la Plataforma de Análisis Macroeconómico
==============================================================================
Evolución de routes.py del ZIP original (Customer/Transaction -> Indicator/
DataPoint), adaptado a la nueva capa de datos (SQLAlchemy puro) y ampliado
con endpoints de series temporales (para el dashboard) y alertas.
"""

from __future__ import annotations

import sys
from datetime import date, datetime
from pathlib import Path

from flask import Blueprint, jsonify, request, send_file

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import settings  # noqa: E402
from data_layer.db import get_session  # noqa: E402
from data_layer.models import DataPoint, MacroIndicator, create_audit_log  # noqa: E402
from domain.alert_engine import build_alerts_snapshot  # noqa: E402
from domain.analytics_engine import build_summary_by_category  # noqa: E402
from domain.correlation_engine import build_correlation_matrix  # noqa: E402
from domain.trend_engine import build_trend_snapshot  # noqa: E402
from domain.volatility_engine import build_volatility_snapshot, build_volatility_snapshot_all  # noqa: E402
from reports.pdf_generator import generate_summary_report  # noqa: E402

api_bp = Blueprint("api", __name__, url_prefix="/api")


# ─────────────────────────────────────────────
# Salud del servicio (pública, sin API key)
# ─────────────────────────────────────────────
@api_bp.route("/health", methods=["GET"])
def health():
    with get_session() as session:
        total_indicadores = session.query(MacroIndicator).count()
        total_datapoints = session.query(DataPoint).count()
    return jsonify({
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat(),
        "total_indicadores": total_indicadores,
        "total_observaciones": total_datapoints,
    })


# ─────────────────────────────────────────────
# Indicadores (catálogo)
# ─────────────────────────────────────────────
@api_bp.route("/indicators", methods=["GET"])
def list_indicators():
    categoria = request.args.get("categoria")
    solo_activos = request.args.get("activo", "true").lower() == "true"

    with get_session() as session:
        query = session.query(MacroIndicator)
        if categoria:
            query = query.filter(MacroIndicator.categoria == categoria)
        if solo_activos:
            query = query.filter(MacroIndicator.activo.is_(True))
        indicadores = query.order_by(MacroIndicator.codigo).all()
        return jsonify({
            "total": len(indicadores),
            "indicadores": [i.to_dict() for i in indicadores],
        })


@api_bp.route("/indicators", methods=["POST"])
def create_indicator():
    body = request.get_json(silent=True) or {}
    requeridos = ["codigo", "nombre"]
    faltantes = [f for f in requeridos if not body.get(f)]
    if faltantes:
        return jsonify({"error": f"Campos requeridos faltantes: {faltantes}"}), 400

    with get_session() as session:
        if session.query(MacroIndicator).filter_by(codigo=body["codigo"]).first():
            return jsonify({"error": f"Ya existe un indicador con código '{body['codigo']}'"}), 409

        indicador = MacroIndicator(
            codigo=body["codigo"],
            nombre=body["nombre"],
            categoria=body.get("categoria"),
            unidad=body.get("unidad"),
            frecuencia=body.get("frecuencia"),
            fuente_datos=body.get("fuente_datos"),
            descripcion=body.get("descripcion"),
        )
        session.add(indicador)
        session.commit()
        session.refresh(indicador)
        return jsonify(indicador.to_dict()), 201


@api_bp.route("/indicators/<int:indicator_id>", methods=["GET"])
def get_indicator(indicator_id: int):
    with get_session() as session:
        indicador = session.get(MacroIndicator, indicator_id)
        if not indicador:
            return jsonify({"error": "Indicador no encontrado"}), 404
        return jsonify(indicador.to_dict())


# ─────────────────────────────────────────────
# Observaciones (data points)
# ─────────────────────────────────────────────
@api_bp.route("/datapoints", methods=["GET"])
def list_datapoints():
    codigo = request.args.get("codigo")
    tipo_dato = request.args.get("tipo_dato")
    estado = request.args.get("estado")
    fecha_desde = request.args.get("fecha_desde")
    fecha_hasta = request.args.get("fecha_hasta")
    page = max(int(request.args.get("page", 1)), 1)
    per_page = min(int(request.args.get("per_page", 50)), 500)

    with get_session() as session:
        query = session.query(DataPoint).join(MacroIndicator)

        if codigo:
            query = query.filter(MacroIndicator.codigo == codigo)
        if tipo_dato:
            query = query.filter(DataPoint.tipo_dato == tipo_dato)
        if estado:
            query = query.filter(DataPoint.estado == estado)
        if fecha_desde:
            query = query.filter(DataPoint.fecha_referencia >= date.fromisoformat(fecha_desde))
        if fecha_hasta:
            query = query.filter(DataPoint.fecha_referencia <= date.fromisoformat(fecha_hasta))

        total = query.count()
        registros = (
            query.order_by(DataPoint.fecha_referencia.desc())
            .offset((page - 1) * per_page)
            .limit(per_page)
            .all()
        )
        return jsonify({
            "total": total,
            "page": page,
            "per_page": per_page,
            "datapoints": [d.to_dict() for d in registros],
        })


@api_bp.route("/datapoints", methods=["POST"])
def create_datapoint():
    body = request.get_json(silent=True) or {}
    requeridos = ["indicator_codigo", "valor", "tipo_dato", "fecha_referencia"]
    faltantes = [f for f in requeridos if body.get(f) is None]
    if faltantes:
        return jsonify({"error": f"Campos requeridos faltantes: {faltantes}"}), 400

    with get_session() as session:
        indicador = session.query(MacroIndicator).filter_by(codigo=body["indicator_codigo"]).first()
        if not indicador:
            return jsonify({"error": f"Indicador '{body['indicator_codigo']}' no existe"}), 404

        ultimo = (
            session.query(DataPoint)
            .filter_by(indicator_id=indicador.id)
            .order_by(DataPoint.fecha_referencia.desc())
            .first()
        )
        valor_anterior = float(ultimo.valor) if ultimo else None
        valor_nuevo = float(body["valor"])
        variacion = (
            round((valor_nuevo - valor_anterior) / valor_anterior * 100, 4)
            if valor_anterior else None
        )

        dp = DataPoint(
            indicator_id=indicador.id,
            valor=valor_nuevo,
            valor_anterior=valor_anterior,
            variacion_pct=variacion,
            moneda=body.get("moneda", "EUR"),
            tipo_dato=body["tipo_dato"],
            estado=body.get("estado", "confirmado"),
            referencia_fuente=body.get("referencia_fuente"),
            fecha_referencia=date.fromisoformat(body["fecha_referencia"]),
            periodo_label=body.get("periodo_label"),
            extra_metadata=body.get("metadata"),
        )
        session.add(dp)
        session.flush()  # asigna dp.id sin cerrar la transacción

        create_audit_log(
            session, data_point_id=dp.id, accion="created",
            usuario=request.headers.get("X-User", "api_client"),
            ip_address=request.remote_addr,
            datos_nuevos=dp.to_dict(),
        )

        session.commit()
        session.refresh(dp)
        return jsonify(dp.to_dict()), 201


# ─────────────────────────────────────────────
# Series temporales (para gráficas del dashboard)
# ─────────────────────────────────────────────
@api_bp.route("/series/<codigo>", methods=["GET"])
def get_series(codigo: str):
    with get_session() as session:
        indicador = session.query(MacroIndicator).filter_by(codigo=codigo).first()
        if not indicador:
            return jsonify({"error": f"Indicador '{codigo}' no existe"}), 404

        puntos = (
            session.query(DataPoint)
            .filter_by(indicator_id=indicador.id)
            .order_by(DataPoint.fecha_referencia.asc())
            .all()
        )
        return jsonify({
            "indicador": indicador.to_dict(),
            "serie": [
                {"fecha": p.fecha_referencia.isoformat(), "valor": float(p.valor),
                 "variacion_pct": float(p.variacion_pct) if p.variacion_pct is not None else None}
                for p in puntos
            ],
        })


# ─────────────────────────────────────────────
# Reporte resumen + alertas automáticas
# ─────────────────────────────────────────────
@api_bp.route("/reports/summary", methods=["GET"])
def reports_summary():
    with get_session() as session:
        resumen = build_summary_by_category(session)
        alertas = build_alerts_snapshot(session=session)

        return jsonify({
            "generado_en": datetime.utcnow().isoformat(),
            "umbral_alerta_pct": settings.alert_threshold_pct,
            "resumen_por_categoria": {
                r.categoria: {
                    "indicadores": r.indicadores,
                    "total_indicadores": r.total_indicadores,
                    "variacion_max": r.variacion_max,
                    "variacion_min": r.variacion_min,
                    "variacion_promedio": r.variacion_promedio,
                } for r in resumen
            },
            "alertas": [
                {
                    "indicador": a.indicador_codigo, "nombre": a.indicador_nombre,
                    "valor_actual": a.valor_actual, "variacion_pct": a.variacion_pct,
                    "fecha": a.fecha, "umbral_configurado": a.umbral_configurado,
                    "severidad": a.severidad,
                } for a in alertas
            ],
            "total_alertas": len(alertas),
        })


# ─────────────────────────────────────────────
# Analítica avanzada (Etapa 3: motores de dominio)
# ─────────────────────────────────────────────
@api_bp.route("/analytics/volatility", methods=["GET"])
def analytics_volatility():
    codigo = request.args.get("codigo")
    with get_session() as session:
        if codigo:
            snap = build_volatility_snapshot(codigo, session)
            if not snap:
                return jsonify({"error": f"Indicador '{codigo}' no existe"}), 404
            return jsonify(snap.__dict__)

        snaps = build_volatility_snapshot_all(session)
        return jsonify({"total": len(snaps), "volatilidades": [s.__dict__ for s in snaps]})


@api_bp.route("/analytics/trend/<codigo>", methods=["GET"])
def analytics_trend(codigo: str):
    with get_session() as session:
        snap = build_trend_snapshot(codigo, session)
        if not snap:
            return jsonify({"error": f"Indicador '{codigo}' no existe"}), 404
        return jsonify(snap.__dict__)


@api_bp.route("/analytics/correlations", methods=["GET"])
def analytics_correlations():
    codigos_param = request.args.get("codigos")
    codigos = codigos_param.split(",") if codigos_param else None
    with get_session() as session:
        matriz = build_correlation_matrix(codigos, session)
        return jsonify({
            "codigos": matriz.codigos,
            "matriz": matriz.matriz,
            "n_observaciones_comunes": matriz.n_observaciones_comunes,
        })


# ─────────────────────────────────────────────
# Reporte PDF (Etapa 5)
# ─────────────────────────────────────────────
@api_bp.route("/reports/pdf", methods=["GET"])
def reports_pdf():
    with get_session() as session:
        resumen = build_summary_by_category(session)
        alertas = build_alerts_snapshot(session=session)

        indicadores = session.query(MacroIndicator).filter_by(activo=True).order_by(MacroIndicator.codigo).all()
        ultimos_valores = []
        for indicador in indicadores:
            ultimo = (
                session.query(DataPoint)
                .filter_by(indicator_id=indicador.id)
                .order_by(DataPoint.fecha_referencia.desc())
                .first()
            )
            if not ultimo:
                continue
            ultimos_valores.append({
                "codigo": indicador.codigo,
                "nombre": indicador.nombre,
                "valor": float(ultimo.valor),
                "variacion_pct": float(ultimo.variacion_pct) if ultimo.variacion_pct is not None else None,
                "fecha": ultimo.fecha_referencia.isoformat(),
            })

        resumen_dict = {
            r.categoria: {
                "total_indicadores": r.total_indicadores,
                "variacion_max": r.variacion_max,
                "variacion_min": r.variacion_min,
                "variacion_promedio": r.variacion_promedio,
            } for r in resumen
        }
        alertas_dict = [
            {
                "indicador": a.indicador_codigo, "nombre": a.indicador_nombre,
                "valor_actual": a.valor_actual, "variacion_pct": a.variacion_pct,
                "fecha": a.fecha, "severidad": a.severidad,
            } for a in alertas
        ]

        ruta_pdf = generate_summary_report(resumen_dict, alertas_dict, ultimos_valores)

    return send_file(
        str(ruta_pdf),
        mimetype="application/pdf",
        as_attachment=True,
        download_name=ruta_pdf.name,
    )
