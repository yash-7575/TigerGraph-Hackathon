"""TigerGraph Savanna connection helper."""

from __future__ import annotations

import threading
from functools import lru_cache

from pyTigerGraph import TigerGraphConnection

from core.config import settings


_lock = threading.Lock()


@lru_cache(maxsize=1)
def _base_conn() -> TigerGraphConnection:
    conn = TigerGraphConnection(
        host=settings.tg_host,
        graphname=settings.tg_graphname,
        gsqlSecret=settings.tg_secret,
        restppPort=settings.tg_restpp_port,
        gsPort=settings.tg_gsql_port,
    )
    conn.getToken(settings.tg_secret)
    return conn


def conn() -> TigerGraphConnection:
    """Thread-safe cached pyTigerGraph connection."""
    with _lock:
        return _base_conn()


def gsql(query: str) -> str:
    return conn().gsql(query)
