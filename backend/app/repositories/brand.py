from __future__ import annotations

import json
from typing import Any

from app.core.database import fetch_one
from app.utils.time_utils import utc_now_iso


def _loads_list(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(x).strip() for x in raw if str(x).strip()]
    if not raw:
        return []
    if isinstance(raw, str):
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, list):
                return [str(x).strip() for x in loaded if str(x).strip()]
        except json.JSONDecodeError:
            return [p.strip() for p in raw.split(",") if p.strip()]
    return []


def row_to_brand(row: dict[str, Any] | None) -> dict[str, Any] | None:
    if not row:
        return None
    return {
        "id": row["id"],
        "brand_name": row.get("brand_name") or "",
        "industry": row.get("industry") or "",
        "country": row.get("country") or "Tunisia",
        "audience": row.get("audience") or "",
        "personality": row.get("personality") or "",
        "languages": _loads_list(row.get("languages_json")),
        "competitors": _loads_list(row.get("competitors_json")),
        "channels": _loads_list(row.get("channels_json")),
        "objectives": _loads_list(row.get("objectives_json")),
        "forbidden_topics": _loads_list(row.get("forbidden_topics_json")),
        "tone": row.get("tone") or "",
        "previous_campaigns": row.get("previous_campaigns") or "",
        "brand_guidelines_text": row.get("brand_guidelines_text") or "",
        "products": row.get("products") or "",
        "budget_level": row.get("budget_level") or "",
        "is_active": bool(row.get("is_active", 1)),
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
    }


def get_active_brand(conn) -> dict[str, Any] | None:
    row = fetch_one(
        conn,
        """
        SELECT * FROM brand_profiles
        WHERE is_active = 1
        ORDER BY id DESC LIMIT 1
        """,
    )
    return row_to_brand(row)


def get_brand(conn, brand_id: int) -> dict[str, Any] | None:
    row = fetch_one(conn, "SELECT * FROM brand_profiles WHERE id = ?", (brand_id,))
    return row_to_brand(row)


def list_brands(conn) -> list[dict[str, Any]]:
    rows = conn.execute(
        "SELECT * FROM brand_profiles ORDER BY is_active DESC, id DESC"
    ).fetchall()
    return [row_to_brand(dict(r)) for r in rows]  # type: ignore[arg-type]


def _dumps(values: list[str] | None) -> str:
    return json.dumps([v for v in (values or []) if str(v).strip()], ensure_ascii=False)


def upsert_brand(conn, payload: dict[str, Any], brand_id: int | None = None) -> dict[str, Any]:
    now = utc_now_iso()
    fields = (
        payload.get("brand_name") or "",
        payload.get("industry") or "",
        payload.get("country") or "Tunisia",
        payload.get("audience") or "",
        payload.get("personality") or "",
        _dumps(payload.get("languages")),
        _dumps(payload.get("competitors")),
        _dumps(payload.get("channels")),
        _dumps(payload.get("objectives")),
        _dumps(payload.get("forbidden_topics")),
        payload.get("tone") or "",
        payload.get("previous_campaigns") or "",
        payload.get("brand_guidelines_text") or "",
        payload.get("products") or "",
        payload.get("budget_level") or "",
    )
    if brand_id:
        conn.execute(
            """
            UPDATE brand_profiles SET
              brand_name=?, industry=?, country=?, audience=?, personality=?,
              languages_json=?, competitors_json=?, channels_json=?, objectives_json=?,
              forbidden_topics_json=?, tone=?, previous_campaigns=?, brand_guidelines_text=?,
              products=?, budget_level=?, updated_at=?
            WHERE id=?
            """,
            (*fields, now, brand_id),
        )
        brand = get_brand(conn, brand_id)
        assert brand
        return brand

    # New active brand: deactivate previous actives (single-tenant MVP)
    conn.execute("UPDATE brand_profiles SET is_active = 0 WHERE is_active = 1")
    cur = conn.execute(
        """
        INSERT INTO brand_profiles (
          brand_name, industry, country, audience, personality,
          languages_json, competitors_json, channels_json, objectives_json,
          forbidden_topics_json, tone, previous_campaigns, brand_guidelines_text,
          products, budget_level, is_active, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """,
        (*fields, now, now),
    )
    new_id = int(cur.lastrowid)
    brand = get_brand(conn, new_id)
    assert brand
    return brand
