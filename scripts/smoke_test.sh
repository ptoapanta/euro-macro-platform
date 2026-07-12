#!/usr/bin/env bash
# scripts/smoke_test.sh — Pruebas integrales de extremo a extremo
# ====================================================================
# Levanta la API real (no un mock), le pega con curl a los endpoints
# principales en secuencia (incluyendo el flujo completo de una alerta:
# crear observación -> variación -> alerta -> webhook -> reporte PDF), y
# reporta un resumen PASS/FAIL. Pensado para correr en la máquina del
# desarrollador (Linux), no en el entorno de construcción.
#
# Uso:
#   chmod +x scripts/smoke_test.sh
#   ./scripts/smoke_test.sh

set -uo pipefail

API_URL="http://localhost:${API_PORT:-5000}"
API_KEY="${API_KEY:-euro_macro_key_2024}"
PDF_TMP="/tmp/smoke_test_reporte.pdf"
API_LOG="/tmp/smoke_test_api.log"

TOTAL=0
FALLOS=0
API_PID=""

# ── Utilidades ──
color() { printf "\033[%sm%s\033[0m" "$1" "$2"; }

check() {
    local descripcion="$1" esperado="$2" real="$3"
    TOTAL=$((TOTAL + 1))
    if [ "$real" = "$esperado" ]; then
        echo "$(color 32 '✓') $descripcion (HTTP $real)"
    else
        echo "$(color 31 '✗') $descripcion (esperado $esperado, obtuve $real)"
        FALLOS=$((FALLOS + 1))
    fi
}

check_json_field() {
    local descripcion="$1" archivo_json="$2" expresion_python="$3"
    TOTAL=$((TOTAL + 1))
    if python3 -c "
import json, sys
data = json.load(open('$archivo_json'))
assert $expresion_python
" 2>/dev/null; then
        echo "$(color 32 '✓') $descripcion"
    else
        echo "$(color 31 '✗') $descripcion"
        FALLOS=$((FALLOS + 1))
    fi
}

cleanup() {
    if [ -n "$API_PID" ]; then
        kill "$API_PID" 2>/dev/null
        wait "$API_PID" 2>/dev/null
    fi
}
trap cleanup EXIT

# ── 1. Pruebas unitarias/integración con pytest ──
echo "=== 1. Suite de pytest ==="
if pytest tests/ -q; then
    echo "$(color 32 '✓') pytest: todas las pruebas pasaron"
else
    echo "$(color 31 '✗') pytest: hay pruebas fallando (revisa arriba)"
    FALLOS=$((FALLOS + 1))
fi
TOTAL=$((TOTAL + 1))
echo

# ── 2. Levantar la API real ──
echo "=== 2. Levantando la API ==="
python api/app.py > "$API_LOG" 2>&1 &
API_PID=$!

intentos=0
until curl -s -o /dev/null "$API_URL/api/health"; do
    intentos=$((intentos + 1))
    if [ "$intentos" -ge 20 ]; then
        echo "$(color 31 '✗') La API no respondió tras 20 intentos. Revisa $API_LOG"
        exit 1
    fi
    sleep 0.5
done
echo "API arriba en $API_URL (PID $API_PID)"
echo

# ── 3. Flujo completo vía HTTP ──
echo "=== 3. Flujo end-to-end vía HTTP ==="

codigo=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/health")
check "GET /api/health (sin key, publico)" "200" "$codigo"

codigo=$(curl -s -o /dev/null -w "%{http_code}" "$API_URL/api/indicators")
check "GET /api/indicators sin API key -> debe rechazar" "401" "$codigo"

codigo=$(curl -s -o /tmp/smoke_indicators.json -w "%{http_code}" -H "X-API-Key: $API_KEY" "$API_URL/api/indicators")
check "GET /api/indicators con API key" "200" "$codigo"
check_json_field "El catalogo tiene al menos 5 indicadores" /tmp/smoke_indicators.json "data['total'] >= 5"

codigo=$(curl -s -o /tmp/smoke_create_ind.json -w "%{http_code}" -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
    -d '{"codigo":"SMOKE_TEST","nombre":"Indicador de prueba integral","categoria":"test"}' \
    "$API_URL/api/indicators")
check "POST /api/indicators (crear indicador de prueba)" "201" "$codigo"

codigo=$(curl -s -o /dev/null -w "%{http_code}" -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
    -d '{"indicator_codigo":"SMOKE_TEST","valor":100,"tipo_dato":"spot","fecha_referencia":"2026-01-01"}' \
    "$API_URL/api/datapoints")
check "POST /api/datapoints (primer valor, sin variacion)" "201" "$codigo"

codigo=$(curl -s -o /tmp/smoke_dp2.json -w "%{http_code}" -X POST -H "X-API-Key: $API_KEY" -H "Content-Type: application/json" \
    -d '{"indicator_codigo":"SMOKE_TEST","valor":150,"tipo_dato":"spot","fecha_referencia":"2026-01-02"}' \
    "$API_URL/api/datapoints")
check "POST /api/datapoints (segundo valor, +50% -> debe disparar alerta)" "201" "$codigo"
check_json_field "La variacion calculada es 50.0%" /tmp/smoke_dp2.json "data['variacion_pct'] == 50.0"
check_json_field "La respuesta incluye el resultado del intento de webhook" /tmp/smoke_dp2.json "'webhook' in data"

codigo=$(curl -s -o /tmp/smoke_series.json -w "%{http_code}" -H "X-API-Key: $API_KEY" "$API_URL/api/series/SMOKE_TEST")
check "GET /api/series/SMOKE_TEST" "200" "$codigo"
check_json_field "La serie tiene 2 observaciones" /tmp/smoke_series.json "len(data['serie']) == 2"

codigo=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" "$API_URL/api/analytics/volatility?codigo=SMOKE_TEST")
check "GET /api/analytics/volatility?codigo=SMOKE_TEST" "200" "$codigo"

codigo=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" "$API_URL/api/analytics/trend/SMOKE_TEST")
check "GET /api/analytics/trend/SMOKE_TEST" "200" "$codigo"

codigo=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" "$API_URL/api/analytics/correlations")
check "GET /api/analytics/correlations" "200" "$codigo"

codigo=$(curl -s -o /tmp/smoke_summary.json -w "%{http_code}" -H "X-API-Key: $API_KEY" "$API_URL/api/reports/summary")
check "GET /api/reports/summary" "200" "$codigo"
check_json_field "SMOKE_TEST aparece en las alertas activas" /tmp/smoke_summary.json \
    "any(a['indicador'] == 'SMOKE_TEST' for a in data['alertas'])"

codigo=$(curl -s -o "$PDF_TMP" -w "%{http_code}" -H "X-API-Key: $API_KEY" "$API_URL/api/reports/pdf")
check "GET /api/reports/pdf" "200" "$codigo"
TOTAL=$((TOTAL + 1))
if [ -s "$PDF_TMP" ] && head -c4 "$PDF_TMP" | grep -q "%PDF"; then
    echo "$(color 32 '✓') El PDF generado es un archivo PDF valido y no esta vacio"
else
    echo "$(color 31 '✗') El PDF generado esta vacio o no es un PDF valido"
    FALLOS=$((FALLOS + 1))
fi

codigo=$(curl -s -o /dev/null -w "%{http_code}" -H "X-API-Key: $API_KEY" "$API_URL/api/webhooks/status")
check "GET /api/webhooks/status" "200" "$codigo"

echo
echo "=== Resumen ==="
echo "Total verificaciones: $TOTAL"
echo "Fallos: $FALLOS"
rm -f /tmp/smoke_*.json

if [ "$FALLOS" -eq 0 ]; then
    echo "$(color 32 'TODO PASO CORRECTAMENTE')"
    exit 0
else
    echo "$(color 31 'HAY VERIFICACIONES FALLIDAS — revisa el detalle arriba y $API_LOG')"
    exit 1
fi
