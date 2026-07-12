"""
reports/pdf_generator.py — Generación de reportes PDF
==========================================================
Construye un reporte con: resumen por categoría, alertas activas y
últimos valores por indicador. Usa reportlab/Platypus (ver /mnt/skills/
public/pdf/SKILL.md), evitando caracteres Unicode de sub/superíndice.
"""

from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

sys.path.append(str(Path(__file__).resolve().parent.parent))

COLOR_PRIMARIO = colors.HexColor("#1a3c6e")
COLOR_ALERTA_ALTA = colors.HexColor("#c0392b")
COLOR_ALERTA_MODERADA = colors.HexColor("#e67e22")
COLOR_FILA_PAR = colors.HexColor("#f2f5f9")


def _estilos():
    base = getSampleStyleSheet()
    base.add(ParagraphStyle(
        name="TituloReporte", parent=base["Title"], textColor=COLOR_PRIMARIO, fontSize=20,
    ))
    base.add(ParagraphStyle(
        name="Subtitulo", parent=base["Heading2"], textColor=COLOR_PRIMARIO, spaceBefore=14,
    ))
    return base


def _tabla_resumen_categorias(resumen_por_categoria: dict) -> Table:
    encabezado = ["Categoría", "Indicadores", "Var. máx %", "Var. mín %", "Var. promedio %"]
    filas = [encabezado]
    for cat, datos in resumen_por_categoria.items():
        filas.append([
            cat,
            str(datos.get("total_indicadores", "—")),
            f"{datos.get('variacion_max')}" if datos.get("variacion_max") is not None else "—",
            f"{datos.get('variacion_min')}" if datos.get("variacion_min") is not None else "—",
            f"{datos.get('variacion_promedio')}" if datos.get("variacion_promedio") is not None else "—",
        ])

    tabla = Table(filas, colWidths=[4.5 * cm, 2.8 * cm, 2.8 * cm, 2.8 * cm, 3.2 * cm])
    tabla.setStyle(_estilo_tabla_base())
    return tabla


def _tabla_alertas(alertas: list[dict]) -> Table:
    encabezado = ["Indicador", "Valor actual", "Variación %", "Fecha", "Severidad"]
    filas = [encabezado]
    for a in alertas:
        filas.append([
            f"{a['indicador']} — {a['nombre']}",
            str(a["valor_actual"]),
            f"{a['variacion_pct']:+.2f}",
            a["fecha"],
            a["severidad"].upper(),
        ])

    tabla = Table(filas, colWidths=[6.5 * cm, 3 * cm, 2.5 * cm, 2.5 * cm, 2.5 * cm])
    estilo = _estilo_tabla_base()

    for i, a in enumerate(alertas, start=1):
        color = COLOR_ALERTA_ALTA if a["severidad"] == "alta" else COLOR_ALERTA_MODERADA
        estilo.add("TEXTCOLOR", (4, i), (4, i), color)
        estilo.add("FONTNAME", (4, i), (4, i), "Helvetica-Bold")

    tabla.setStyle(estilo)
    return tabla


def _tabla_ultimos_valores(ultimos_valores: list[dict]) -> Table:
    encabezado = ["Código", "Nombre", "Último valor", "Variación %", "Fecha"]
    filas = [encabezado]
    for v in ultimos_valores:
        filas.append([
            v["codigo"], v["nombre"], str(v["valor"]),
            f"{v['variacion_pct']:+.2f}" if v.get("variacion_pct") is not None else "—",
            v["fecha"],
        ])

    tabla = Table(filas, colWidths=[2.5 * cm, 6 * cm, 3 * cm, 2.5 * cm, 3 * cm])
    tabla.setStyle(_estilo_tabla_base())
    return tabla


def _estilo_tabla_base() -> TableStyle:
    return TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), COLOR_PRIMARIO),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, COLOR_FILA_PAR]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
    ])


def generate_summary_report(
    resumen_por_categoria: dict,
    alertas: list[dict],
    ultimos_valores: list[dict],
    output_path: str | Path | None = None,
) -> Path:
    """Genera el PDF y devuelve la ruta del archivo creado."""
    if output_path is None:
        marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(__file__).resolve().parent / "generated" / f"reporte_macro_{marca_tiempo}.pdf"

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    estilos = _estilos()
    doc = SimpleDocTemplate(
        str(output_path), pagesize=letter,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )

    story = [
        Paragraph("Plataforma de Análisis Macroeconómico del Euro", estilos["TituloReporte"]),
        Paragraph(f"Reporte generado el {datetime.now().strftime('%d/%m/%Y a las %H:%M')}", estilos["Normal"]),
        Spacer(1, 16),
    ]

    story.append(Paragraph("Resumen por categoría", estilos["Subtitulo"]))
    if resumen_por_categoria:
        story.append(_tabla_resumen_categorias(resumen_por_categoria))
    else:
        story.append(Paragraph("Sin datos disponibles.", estilos["Normal"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph(f"Alertas activas ({len(alertas)})", estilos["Subtitulo"]))
    if alertas:
        story.append(_tabla_alertas(alertas))
    else:
        story.append(Paragraph("No hay alertas activas en este momento.", estilos["Normal"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph("Últimos valores por indicador", estilos["Subtitulo"]))
    if ultimos_valores:
        story.append(_tabla_ultimos_valores(ultimos_valores))
    else:
        story.append(Paragraph("Sin observaciones registradas.", estilos["Normal"]))

    doc.build(story)
    return output_path
