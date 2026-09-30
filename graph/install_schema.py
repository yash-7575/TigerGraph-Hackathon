"""Install the graph schema into TigerGraph Savanna.

Idempotent — safe to rerun. Drops OlympicsKG if it exists, then re-creates.
"""

from __future__ import annotations

import sys
from pathlib import Path

from loguru import logger

from core.tg import conn


SCHEMA_PATH = Path(__file__).parent / "schema.gsql"


def install() -> None:
    c = conn()

    # Try dropping existing graph (safe if absent).
    try:
        logger.info("dropping existing OlympicsKG (if any)...")
        c.gsql("USE GLOBAL DROP GRAPH OlympicsKG")
    except Exception as e:  # noqa: BLE001
        logger.warning(f"drop failed (ok if new): {e}")

    logger.info("installing schema...")
    result = c.gsql(SCHEMA_PATH.read_text())
    logger.info(f"schema result:\n{result}")

    logger.info("listing graphs...")
    print(c.gsql("SHOW GRAPH"))


if __name__ == "__main__":
    install()
    sys.exit(0)
