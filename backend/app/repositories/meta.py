from __future__ import annotations

from typing import Any


def get_filter_options(conn) -> dict[str, Any]:
    cats_m = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT category FROM media_items WHERE category IS NOT NULL AND trim(category) != '' ORDER BY category COLLATE NOCASE"
        ).fetchall()
    ]
    cats_t = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT category FROM trend_clusters WHERE category IS NOT NULL AND trim(category) != '' ORDER BY category COLLATE NOCASE"
        ).fetchall()
    ]
    plats = [
        r[0]
        for r in conn.execute(
            "SELECT DISTINCT platform FROM media_items WHERE platform IS NOT NULL ORDER BY platform COLLATE NOCASE"
        ).fetchall()
    ]
    cats = sorted(set(cats_m + cats_t), key=str.lower)
    return {"categories": cats, "platforms": plats}
