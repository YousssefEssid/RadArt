"""Veille concurrentielle : brief enregistré + signaux indexés (media_items, trend_clusters)."""
from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from app.core.database import fetch_all, fetch_one
from app.services.brief_service import _extract_competitor_names

SECTOR_WATCHLIST: dict[str, list[str]] = {
    "food/beverage": ["Coca-Cola", "PepsiCo", "Red Bull"],
    "banking/finance": ["BNP Paribas", "Attijari bank", "STB"],
    "telecom": ["Orange Tunisie", "Ooredoo Tunisie", "Orange France"],
    "beauty/skincare": ["L'Oréal", "Unilever", "Nivea"],
    "retail": ["Carrefour", "Aziza", "MG"],
    "tourism": ["Booking.com", "Expedia", "Airbnb"],
    "general": ["Samsung", "Apple"],
}


def _filter_vs_client(names: list[str], client_name: str | None) -> list[str]:
    if not client_name:
        return names
    cn = client_name.strip().lower()
    return [n for n in names if n.strip() and n.strip().lower() not in (cn, "") and cn not in n.lower()]


def _infer_watchlist(sector: str | None, client_name: str | None) -> tuple[list[str], str]:
    key = (sector or "").strip().lower() or "general"
    for sk, brands in SECTOR_WATCHLIST.items():
        if sk == key:
            return _filter_vs_client(brands[:5], client_name), "sector_benchmark"
    return _filter_vs_client(SECTOR_WATCHLIST["general"][:5], client_name), "sector_benchmark"


def load_brief_row(conn: sqlite3.Connection, brief_id: int) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM client_briefs WHERE id = ?", (brief_id,))


def resolve_competitor_names(row: dict[str, Any]) -> tuple[list[str], str]:
    raw = row.get("raw_brief") or ""
    stored = row.get("competitors_json")
    names: list[str] = []
    if stored:
        try:
            names = json.loads(stored)
        except json.JSONDecodeError:
            names = []
    if not isinstance(names, list):
        names = []
    names = [str(x).strip() for x in names if str(x).strip()]
    if not names:
        names = _extract_competitor_names(raw)
    client = row.get("client_name")
    names = _filter_vs_client(names, client)
    if names:
        return names[:10], "brief"
    infer, mode = _infer_watchlist(row.get("sector"), client)
    return infer, mode


def _media_hits(conn: sqlite3.Connection, term: str, limit: int) -> list[dict[str, Any]]:
    like = f"%{term.strip().lower()}%"
    sql = """
        SELECT id, title, source, platform, category, url, published_at, engagement
        FROM media_items
        WHERE lower(title) LIKE ? OR (text IS NOT NULL AND lower(text) LIKE ?)
        ORDER BY id DESC
        LIMIT ?
    """
    return fetch_all(conn, sql, (like, like, limit))


def _trend_hits(conn: sqlite3.Connection, term: str, limit: int) -> list[dict[str, Any]]:
    like = f"%{term.strip().lower()}%"
    sql = """
        SELECT id, label, summary, category, trend_score, risk_score
        FROM trend_clusters
        WHERE lower(label) LIKE ? OR lower(summary) LIKE ? OR lower(keywords) LIKE ?
        ORDER BY trend_score DESC
        LIMIT ?
    """
    return fetch_all(conn, sql, (like, like, like, limit))


def build_competitor_report(conn: sqlite3.Connection, brief_id: int) -> dict[str, Any]:
    row = load_brief_row(conn, brief_id)
    if not row:
        raise ValueError("brief_not_found")

    names, source_mode = resolve_competitor_names(row)
    cards: list[dict[str, Any]] = []

    for name in names:
        media_rows = _media_hits(conn, name, 12)
        if len(media_rows) < 4 and " " in name.strip():
            first = name.split()[0]
            if len(first) >= 4:
                extra = _media_hits(conn, first, 8)
                seen = {m["id"] for m in media_rows}
                for m in extra:
                    if m["id"] not in seen:
                        media_rows.append(m)
                        seen.add(m["id"])
                media_rows = media_rows[:12]

        media_out = [
            {
                "id": m["id"],
                "title": m.get("title"),
                "source": m.get("source"),
                "platform": m.get("platform"),
                "category": m.get("category"),
                "url": m.get("url"),
                "published_at": m.get("published_at"),
                "engagement": m.get("engagement"),
            }
            for m in media_rows
        ]
        trend_rows = _trend_hits(conn, name, 5)
        trend_out = [
            {
                "id": t["id"],
                "label": t.get("label"),
                "summary": (t.get("summary") or "")[:300],
                "category": t.get("category"),
                "trend_score": t.get("trend_score"),
                "risk_score": t.get("risk_score"),
            }
            for t in trend_rows
        ]

        if source_mode == "brief":
            note = (
                "Veille ciblée : signaux indexés à partir des mentions du nom dans les titres et contenus agrégés."
            )
        else:
            note = (
                "Veille sectorielle : focus sur les acteurs majeurs du secteur. "
                "Ajoutez des concurrents nommés dans le brief pour affiner le périmètre."
            )

        cards.append(
            {
                "name": name,
                "source_tag": "brief" if source_mode == "brief" else "benchmark",
                "signal_count": len(media_out),
                "recent_signals": media_out,
                "related_clusters": trend_out,
                "notes": note,
            }
        )

    return {
        "brief_id": brief_id,
        "client_name": row.get("client_name"),
        "sector": row.get("sector"),
        "target": row.get("target"),
        "competitor_source": source_mode,
        "competitors": names,
        "cards": cards,
    }


def latest_brief_row(conn: sqlite3.Connection) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT id, client_name, sector, created_at FROM client_briefs ORDER BY id DESC LIMIT 1")
