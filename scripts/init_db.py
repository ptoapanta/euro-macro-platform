"""
scripts/init_db.py — Inicializa la base de datos desde cero
==============================================================
Uso:
    python scripts/init_db.py
"""

import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from data_layer.db import init_db  # noqa: E402
from data_layer.seed_data import run_full_seed  # noqa: E402


def main() -> None:
    print("→ Creando tablas...")
    init_db()
    print("→ Poblando datos iniciales...")
    run_full_seed()
    print("✓ Base de datos lista.")


if __name__ == "__main__":
    main()
