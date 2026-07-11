"""
tests/conftest.py — Configuración compartida de pytest
==========================================================
Fuerza el uso de una base de datos SQLite temporal y aislada ANTES de
importar cualquier módulo del proyecto, para que las pruebas nunca toquen
la base de datos real (data_layer/storage/euro_macro.db).
"""

import os
import sys
import tempfile
from pathlib import Path

import pytest

sys.path.append(str(Path(__file__).resolve().parent.parent))

# IMPORTANTE: estas variables deben fijarse antes de que config.py se importe
# por primera vez en cualquier parte del código (Settings lee os.getenv al
# definirse la dataclass).
_tmp_dir = tempfile.mkdtemp()
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp_dir}/test_euro_macro.db"
os.environ["API_KEY"] = "test_key_123"
os.environ["USE_REAL_EURUSD"] = "false"  # pruebas no dependen de internet


@pytest.fixture(scope="session")
def app():
    from api.app import create_app
    flask_app = create_app()
    flask_app.config.update(TESTING=True)
    return flask_app


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_headers():
    return {"X-API-Key": "test_key_123", "Content-Type": "application/json"}
