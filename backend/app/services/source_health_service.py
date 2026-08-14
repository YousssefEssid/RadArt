"""Source health dashboard — real coverage vs missing access."""

from __future__ import annotations

import asyncio
import sqlite3
from typing import Any

from app.collectors.registry import build_all_collectors
from app.core.database import fetch_one
from app.utils.time_utils import utc_now_iso

_COLLECTION_LABELS = {
    "official_api": "Official API",
    "authorized_account": "Authorized account",
    "official_public_api": "Official public API",
    "search_discovery": "Search discovery",
    "rss": "RSS",
    "public_feed": "Public feed",
    "licensed_provider": "Licensed provider",
    "manual": "Manual / customer-owned",
}


def _items_24h(conn: sqlite3.Connection, platform: str | None = None) -> int:
    sql = """
        SELECT COUNT(*) AS c FROM media_items
        WHERE collected_at >= datetime('now', '-1 day')
    """
    params: tuple[Any, ...] = ()
    if platform:
        sql += " AND platform = ?"
        params = (platform,)
    row = fetch_one(conn, sql, params)
    return int((row or {}).get("c") or 0)


async def _health_rows(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    collectors = build_all_collectors()
    platform_guess = {
        "YouTube": "youtube",
        "Google Trends (SerpApi)": "google_trends",
        "Google Trends (Official API)": "google_trends",
        "Reddit": "reddit",
        "Google News": "google_news_rss",
        "Tunisian media RSS": "rss",
        "Instagram Authorized": "instagram",
        "Instagram Hashtag Search": "instagram",
        "Instagram Business Discovery": "instagram",
        "Facebook Authorized Pages": "facebook",
        "Facebook Public Page Content": "facebook",
        "TikTok Display (authorized)": "tiktok",
        "TikTok Discovery (licensed/official)": "tiktok",
    }
    rows: list[dict[str, Any]] = []
    for col in collectors:
        h = await col.healthcheck()
        d = h.to_dict()
        if col.source == "Social Search Discovery":
            d["items_collected_24h"] = int(
                (
                    fetch_one(
                        conn,
                        """
                        SELECT COUNT(*) AS c FROM media_items
                        WHERE source_method = 'search_discovery'
                          AND collected_at >= datetime('now', '-1 day')
                        """,
                    )
                    or {}
                ).get("c")
                or 0
            )
        else:
            d["items_collected_24h"] = _items_24h(conn, platform_guess.get(col.source))

        cs = d["credential_status"]
        if cs == "connected":
            light = "green"
        elif cs in ("awaiting_credentials", "partial"):
            light = "yellow"
        elif cs == "error":
            light = "red"
        else:
            light = "gray"
        d["light"] = light
        d["collection_label"] = _COLLECTION_LABELS.get(d["source_method"], d["source_method"])
        rows.append(d)
    return rows


def build_source_health(conn: sqlite3.Connection) -> dict[str, Any]:
    rows = asyncio.run(_health_rows(conn))
    matrix = [
        _matrix_row(rows, "YouTube", "youtube"),
        _matrix_row(rows, "Google Trends", "google_trends"),
        _matrix_row(rows, "Instagram", "instagram"),
        _matrix_row(rows, "Facebook", "facebook"),
        _matrix_row(rows, "TikTok", "tiktok"),
        _matrix_row(rows, "Google News", "google_news"),
        _matrix_row(rows, "Reddit", "reddit"),
        _matrix_row(rows, "Tunisian media", "tunisian"),
        _matrix_row(rows, "Social Search Discovery", "search discovery"),
    ]
    return {
        "generated_at": utc_now_iso(),
        "principle": "Show real coverage vs missing access — never pretend full Meta/TikTok firehose.",
        "collectors": rows,
        "matrix": matrix,
    }


def _matrix_row(rows: list[dict[str, Any]], label: str, key: str) -> dict[str, Any]:
    if key == "google_trends":
        matches = [r for r in rows if "trends" in r["source"].lower()]
    elif key == "google_news":
        matches = [r for r in rows if "google news" in r["source"].lower()]
    elif key == "tunisian":
        matches = [r for r in rows if "tunisian media" in r["source"].lower()]
    elif key == "search discovery":
        matches = [r for r in rows if "search discovery" in r["source"].lower()]
    else:
        matches = [
            r
            for r in rows
            if key in r["source"].lower() or key in (r.get("provider") or "").lower()
        ]

    if not matches:
        return {"source": label, "status": "missing", "light": "gray", "collection": "—", "detail": None}

    connected = [m for m in matches if m["credential_status"] == "connected"]
    awaiting = [m for m in matches if m["credential_status"] == "awaiting_credentials"]
    discovery = next((r for r in rows if "search discovery" in r["source"].lower()), None)
    discovery_ok = bool(discovery and discovery["credential_status"] == "connected")

    if connected:
        methods = sorted({m["collection_label"] for m in connected})
        if discovery_ok and key in ("instagram", "facebook", "tiktok"):
            return {
                "source": label,
                "status": "Connected",
                "light": "green",
                "collection": "Official + Discovery",
                "detail": ", ".join(methods),
            }
        return {
            "source": label,
            "status": "Connected",
            "light": "green",
            "collection": methods[0],
            "detail": ", ".join(methods),
        }

    if key in ("instagram", "facebook", "tiktok") and discovery_ok:
        return {
            "source": label,
            "status": "Partial",
            "light": "yellow",
            "collection": "Search discovery",
            "detail": awaiting[0].get("detail") if awaiting else "Official API awaiting credentials",
        }

    if awaiting:
        return {
            "source": label,
            "status": "Awaiting credentials",
            "light": "yellow",
            "collection": awaiting[0]["collection_label"],
            "detail": awaiting[0].get("detail"),
        }

    m0 = matches[0]
    return {
        "source": label,
        "status": m0["credential_status"],
        "light": m0.get("light") or "gray",
        "collection": m0["collection_label"],
        "detail": m0.get("detail"),
    }
