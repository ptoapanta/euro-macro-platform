"""
api/app.py — Punto de entrada de la API REST
================================================
Evolución de app.py del ZIP original: mismo patrón de app factory,
middleware de autenticación por API key y CORS, adaptado a la nueva
capa de datos e importando las rutas ampliadas de routes.py.

Ejecución local:
    python api/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

from flask import Flask, jsonify, request
from flask_cors import CORS

sys.path.append(str(Path(__file__).resolve().parent.parent))

from config import settings  # noqa: E402
from data_layer.db import init_db  # noqa: E402

# Rutas públicas que NO requieren API key
RUTAS_PUBLICAS = {"/", "/api/health"}


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    # Garantiza que las tablas existan (idempotente); no siembra datos aquí,
    # eso lo hace explícitamente scripts/init_db.py para no acoplar la API
    # a un proceso de carga de datos potencialmente lento.
    init_db()

    from api.routes import api_bp
    app.register_blueprint(api_bp)

    @app.before_request
    def verificar_api_key():
        if request.path in RUTAS_PUBLICAS:
            return None
        api_key_recibida = request.headers.get("X-API-Key")
        if api_key_recibida != settings.api_key:
            return jsonify({"error": "API key inválida o ausente (header X-API-Key)"}), 401
        return None

    @app.route("/", methods=["GET"])
    def index():
        return jsonify({
            "servicio": "Plataforma de Análisis Macroeconómico del Euro",
            "version": "0.4.0-etapa5",
            "endpoints": [
                "GET  /api/health",
                "GET  /api/indicators",
                "POST /api/indicators",
                "GET  /api/indicators/<id>",
                "GET  /api/datapoints",
                "POST /api/datapoints",
                "GET  /api/series/<codigo>",
                "GET  /api/reports/summary",
                "GET  /api/reports/pdf",
                "GET  /api/analytics/volatility",
                "GET  /api/analytics/trend/<codigo>",
                "GET  /api/analytics/correlations",
            ],
        })

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=settings.api_port, debug=settings.debug)
