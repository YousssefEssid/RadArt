from __future__ import annotations

from typing import Any

from app.core.database import fetch_all


def list_media_items(
    conn,
    *,
    limit: int = 50,
    category: str | None = None,
    platform: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    lim = max(1, min(200, limit))
    conditions: list[str] = []
    params: list[Any] = []
    if category and category.strip():
        cats = [c.strip().lower() for c in category.split(",") if c.strip()]
        if cats:
            placeholders = ",".join("?" * len(cats))
            conditions.append(f"lower(category) IN ({placeholders})")
            params.extend(cats)
    if platform and platform.strip():
        plats = [p.strip().lower() for p in platform.split(",") if p.strip()]
        if plats:
            placeholders = ",".join("?" * len(plats))
            conditions.append(f"lower(platform) IN ({placeholders})")
            params.extend(plats)
    if q and q.strip():
        like = f"%{q.strip()}%"
        conditions.append("(title LIKE ? OR text LIKE ?)")
        params.extend([like, like])
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""SELECT id, source, platform, title, text, url, published_at, collected_at,
              engagement, category, cluster_id, entities FROM media_items{where}
              ORDER BY id DESC LIMIT ?"""
    params.append(lim)
    return fetch_all(conn, sql, tuple(params))


def count_media_items(conn) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM media_items").fetchone()[0])
