"""
data_layer/models.py — Modelos de datos para el análisis macroeconómico del Euro
==================================================================================
Evolución del models.py original (flask_sqlalchemy) a SQLAlchemy puro,
para desacoplar la capa de datos del framework web.

Se conservan las 3 entidades originales del proyecto base:
  - MacroIndicator : catálogo de indicadores
  - DataPoint      : observaciones puntuales de cada indicador
  - AuditLog       : trazabilidad de cambios
"""

from __future__ import annotations

from datetime import date, datetime, timezone

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, JSON, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from data_layer.db import Base


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────
# MODELO 1: MacroIndicator — catálogo de indicadores
# ─────────────────────────────────────────────
class MacroIndicator(Base):
    __tablename__ = "macro_indicators"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    nombre: Mapped[str] = mapped_column(String(200), nullable=False)
    categoria: Mapped[str | None] = mapped_column(String(50))
    unidad: Mapped[str | None] = mapped_column(String(50))
    frecuencia: Mapped[str | None] = mapped_column(String(20))
    fuente_datos: Mapped[str | None] = mapped_column(String(100))
    descripcion: Mapped[str | None] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    series: Mapped[list["DataPoint"]] = relationship(back_populates="indicator")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "codigo": self.codigo,
            "nombre": self.nombre,
            "categoria": self.categoria,
            "unidad": self.unidad,
            "frecuencia": self.frecuencia,
            "fuente_datos": self.fuente_datos,
            "descripcion": self.descripcion,
            "activo": self.activo,
            "total_observaciones": len(self.series),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─────────────────────────────────────────────
# MODELO 2: DataPoint — observación puntual de un indicador
# ─────────────────────────────────────────────
class DataPoint(Base):
    __tablename__ = "data_points"

    id: Mapped[int] = mapped_column(primary_key=True)
    indicator_id: Mapped[int] = mapped_column(ForeignKey("macro_indicators.id"), nullable=False), index=True)

    valor: Mapped[float] = mapped_column(Numeric(18, 6), nullable=False)
    valor_anterior: Mapped[float | None] = mapped_column(Numeric(18, 6))
    variacion_pct: Mapped[float | None] = mapped_column(Numeric(10, 4))

    moneda: Mapped[str] = mapped_column(String(10), default="EUR")
    tipo_dato: Mapped[str] = mapped_column(String(30), nullable=False)  # spot | proyeccion | revision
    estado: Mapped[str] = mapped_column(String(20), default="confirmado")

    referencia_fuente: Mapped[str | None] = mapped_column(String(200))

    fecha_referencia: Mapped[date] = mapped_column(Date, nullable=False), index=True)
    periodo_label: Mapped[str | None] = mapped_column(String(20))

    extra_metadata: Mapped[dict | None] = mapped_column("metadata", JSON)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=_utcnow, onupdate=_utcnow)

    indicator: Mapped["MacroIndicator"] = relationship(back_populates="series")
    audit_logs: Mapped[list["AuditLog"]] = relationship(back_populates="data_point")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "indicator_id": self.indicator_id,
            "indicator_codigo": self.indicator.codigo if self.indicator else None,
            "indicator_nombre": self.indicator.nombre if self.indicator else None,
            "valor": float(self.valor),
            "valor_anterior": float(self.valor_anterior) if self.valor_anterior is not None else None,
            "variacion_pct": float(self.variacion_pct) if self.variacion_pct is not None else None,
            "moneda": self.moneda,
            "tipo_dato": self.tipo_dato,
            "estado": self.estado,
            "referencia_fuente": self.referencia_fuente,
            "fecha_referencia": self.fecha_referencia.isoformat() if self.fecha_referencia else None,
            "periodo_label": self.periodo_label,
            "metadata": self.extra_metadata,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


# ─────────────────────────────────────────────
# MODELO 3: AuditLog — trazabilidad de cambios
# ─────────────────────────────────────────────
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    data_point_id: Mapped[int | None] = mapped_column(ForeignKey("data_points.id"))

    accion: Mapped[str] = mapped_column(String(50), nullable=False)  # created, updated, deleted
    usuario: Mapped[str | None] = mapped_column(String(100))
    ip_address: Mapped[str | None] = mapped_column(String(50))
    datos_anteriores: Mapped[dict | None] = mapped_column(JSON)
    datos_nuevos: Mapped[dict | None] = mapped_column(JSON)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=_utcnow)

    data_point: Mapped["DataPoint"] = relationship(back_populates="audit_logs")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "data_point_id": self.data_point_id,
            "accion": self.accion,
            "usuario": self.usuario,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "datos_anteriores": self.datos_anteriores,
            "datos_nuevos": self.datos_nuevos,
        }


def create_audit_log(
    session,
    data_point_id: int,
    accion: str,
    usuario: str = "system",
    ip_address: str | None = None,
    datos_anteriores: dict | None = None,
    datos_nuevos: dict | None = None,
) -> AuditLog:
    """Registrar un cambio en audit_logs (no hace commit, eso lo decide el caller)."""
    log = AuditLog(
        data_point_id=data_point_id,
        accion=accion,
        usuario=usuario,
        ip_address=ip_address,
        datos_anteriores=datos_anteriores,
        datos_nuevos=datos_nuevos,
    )
    session.add(log)
    return log
