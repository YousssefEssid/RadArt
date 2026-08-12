from __future__ import annotations

from typing import Any

from app.core.database import fetch_all


def list_recent_runs(conn, limit: int = 10) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "SELECT * FROM collection_runs ORDER BY id DESC LIMIT ?",
        (limit,),
    )


def count_trend_clusters(conn) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM trend_clusters").fetchone()[0])
