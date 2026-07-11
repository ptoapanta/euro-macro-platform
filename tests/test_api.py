"""
tests/test_api.py — Pruebas de la API REST (Etapa 2)
========================================================
Ejecutar con:
    pytest tests/test_api.py -v
"""

from __future__ import annotations


def test_health_no_requiere_api_key(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "ok"


def test_endpoints_protegidos_sin_api_key(client):
    resp = client.get("/api/indicators")
    assert resp.status_code == 401


def test_endpoints_protegidos_con_api_key_invalida(client, auth_headers):
    headers = dict(auth_headers)
    headers["X-API-Key"] = "clave_incorrecta"
    resp = client.get("/api/indicators", headers=headers)
    assert resp.status_code == 401


def test_crear_y_listar_indicador(client, auth_headers):
    payload = {
        "codigo": "TEST_IND",
        "nombre": "Indicador de prueba",
        "categoria": "test",
        "unidad": "%",
        "frecuencia": "diaria",
    }
    resp = client.post("/api/indicators", json=payload, headers=auth_headers)
    assert resp.status_code == 201
    creado = resp.get_json()
    assert creado["codigo"] == "TEST_IND"

    # No debe permitir duplicados
    resp_dup = client.post("/api/indicators", json=payload, headers=auth_headers)
    assert resp_dup.status_code == 409

    resp_list = client.get("/api/indicators?activo=true", headers=auth_headers)
    assert resp_list.status_code == 200
    codigos = [i["codigo"] for i in resp_list.get_json()["indicadores"]]
    assert "TEST_IND" in codigos


def test_crear_indicador_sin_campos_requeridos(client, auth_headers):
    resp = client.post("/api/indicators", json={"nombre": "Sin código"}, headers=auth_headers)
    assert resp.status_code == 400


def test_crear_datapoint_y_calcular_variacion(client, auth_headers):
    # Indicador base para esta prueba
    client.post("/api/indicators", json={
        "codigo": "TEST_DP", "nombre": "Indicador para datapoints",
        "categoria": "test",
    }, headers=auth_headers)

    p1 = client.post("/api/datapoints", json={
        "indicator_codigo": "TEST_DP", "valor": 100.0,
        "tipo_dato": "spot", "fecha_referencia": "2026-01-01",
    }, headers=auth_headers)
    assert p1.status_code == 201
    assert p1.get_json()["variacion_pct"] is None  # primer punto, sin anterior

    p2 = client.post("/api/datapoints", json={
        "indicator_codigo": "TEST_DP", "valor": 110.0,
        "tipo_dato": "spot", "fecha_referencia": "2026-01-02",
    }, headers=auth_headers)
    assert p2.status_code == 201
    assert p2.get_json()["variacion_pct"] == 10.0  # (110-100)/100 * 100


def test_series_endpoint(client, auth_headers):
    resp = client.get("/api/series/TEST_DP", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["indicador"]["codigo"] == "TEST_DP"
    assert len(data["serie"]) == 2


def test_series_indicador_inexistente(client, auth_headers):
    resp = client.get("/api/series/NO_EXISTE", headers=auth_headers)
    assert resp.status_code == 404


def test_reports_summary_detecta_alerta(client, auth_headers):
    # La variación de 10% del test anterior supera el umbral por defecto (1%)
    resp = client.get("/api/reports/summary", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["total_alertas"] >= 1
    codigos_en_alerta = [a["indicador"] for a in data["alertas"]]
    assert "TEST_DP" in codigos_en_alerta
