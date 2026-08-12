from __future__ import annotations

import json
from typing import Any

from app.core.database import fetch_one


def get_latest_brief(conn) -> dict[str, Any]:
    row = fetch_one(
        conn,
        """SELECT id, client_name, sector, target, competitors_json, created_at
           FROM client_briefs ORDER BY id DESC LIMIT 1""",
    )
    if not row:
        return {}
    comps: list[str] = []
    raw = row.get("competitors_json")
    if raw:
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, list):
                comps = [str(x) for x in loaded if str(x).strip()]
        except json.JSONDecodeError:
            comps = []
    return {
        "id": row["id"],
        "client_name": row.get("client_name"),
        "sector": row.get("sector"),
        "target": row.get("target"),
        "competitors": comps,
        "created_at": row.get("created_at"),
    }


def brief_exists(conn, brief_id: int) -> bool:
    row = conn.execute("SELECT id FROM client_briefs WHERE id = ?", (brief_id,)).fetchone()
    return row is not None
