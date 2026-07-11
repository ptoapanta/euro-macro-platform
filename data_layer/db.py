"""
data_layer/db.py — Conexión y sesión de base de datos
=======================================================
Se usa SQLAlchemy "puro" (no flask_sqlalchemy) para que esta capa sea
independiente del framework de UI: tanto la API Flask como el dashboard
Streamlit y los scripts CLI comparten la misma capa de datos.
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))
from config import settings  # noqa: E402


class Base(DeclarativeBase):
    """Clase base declarativa para todos los modelos ORM."""
    pass


engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)

SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


def init_db() -> None:
    """Crea todas las tablas si no existen. Idempotente."""
    from data_layer import models  # noqa: F401  (registra los modelos en Base)
    Base.metadata.create_all(bind=engine)


@contextmanager
def get_session() -> Iterator[Session]:
    """Context manager para obtener una sesión y garantizar su cierre.

    Uso:
        with get_session() as session:
            session.add(objeto)
            session.commit()
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
