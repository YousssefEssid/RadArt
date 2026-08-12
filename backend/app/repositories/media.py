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
    min_engagement: int | None = None,
    per_platform: int | None = None,
) -> list[dict[str, Any]]:
    lim = max(1, min(400, limit))
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
    if min_engagement is not None:
        conditions.append("COALESCE(engagement, 0) >= ?")
        params.append(int(min_engagement))
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""

    if per_platform and per_platform > 0:
        cap = max(lim, int(per_platform) * 30)
        sql = f"""SELECT id, source, platform, title, text, url, published_at, collected_at,
                  engagement, category, cluster_id, entities FROM media_items{where}
                  ORDER BY COALESCE(engagement, 0) DESC, id DESC LIMIT ?"""
        params.append(cap)
        rows = fetch_all(conn, sql, tuple(params))
        buckets: dict[str, list[dict[str, Any]]] = {}
        for row in rows:
            key = (row.get("platform") or "autre").strip() or "autre"
            bucket = buckets.setdefault(key, [])
            if len(bucket) < int(per_platform):
                bucket.append(row)
        ranked_plats = sorted(
            buckets.keys(),
            key=lambda p: (-sum(int(x.get("engagement") or 0) for x in buckets[p]), p.lower()),
        )
        out: list[dict[str, Any]] = []
        for p in ranked_plats:
            out.extend(buckets[p])
        return out[:lim]

    sql = f"""SELECT id, source, platform, title, text, url, published_at, collected_at,
              engagement, category, cluster_id, entities FROM media_items{where}
              ORDER BY COALESCE(engagement, 0) DESC, id DESC LIMIT ?"""
    params.append(lim)
    return fetch_all(conn, sql, tuple(params))


def count_media_items(conn) -> int:
    return int(conn.execute("SELECT COUNT(*) FROM media_items").fetchone()[0])
