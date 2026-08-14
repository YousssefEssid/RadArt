"""Watchlists — brands, competitors, topics, hashtags, creators, keywords."""

from __future__ import annotations

import sqlite3
from typing import Any

from app.core.database import fetch_all, fetch_one
from app.utils.time_utils import utc_now_iso

TERM_TYPES = ("brand", "competitor", "topic", "keyword", "hashtag", "creator")


def ensure_default_watchlist(conn: sqlite3.Connection, workspace_id: int = 1) -> dict[str, Any]:
    row = fetch_one(
        conn,
        "SELECT * FROM watchlists WHERE workspace_id = ? AND is_default = 1 ORDER BY id LIMIT 1",
        (workspace_id,),
    )
    if row:
        return row
    now = utc_now_iso()
    cur = conn.execute(
        """
        INSERT INTO watchlists (workspace_id, name, is_default, created_at, updated_at)
        VALUES (?, ?, 1, ?, ?)
        """,
        (workspace_id, "Default", now, now),
    )
    wid = int(cur.lastrowid)
    # Seed Tunisia-relevant starter terms (editable) — not fake media
    seeds = [
        ("brand", "Boga"),
        ("competitor", "Coca-Cola"),
        ("competitor", "Pepsi"),
        ("topic", "Ramadan"),
        ("topic", "football"),
        ("topic", "summer"),
        ("topic", "music"),
        ("hashtag", "tunisia"),
        ("hashtag", "tunisie"),
        ("hashtag", "tunis"),
        ("keyword", "Tunisia"),
        ("keyword", "Tunisie"),
    ]
    for ttype, value in seeds:
        conn.execute(
            """
            INSERT INTO watchlist_terms (watchlist_id, term_type, value, lang, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (wid, ttype, value, "mixed", now),
        )
    return fetch_one(conn, "SELECT * FROM watchlists WHERE id = ?", (wid,)) or {
        "id": wid,
        "workspace_id": workspace_id,
        "name": "Default",
        "is_default": 1,
    }


def list_watchlists(conn: sqlite3.Connection, workspace_id: int = 1) -> list[dict[str, Any]]:
    ensure_default_watchlist(conn, workspace_id)
    return fetch_all(
        conn,
        "SELECT * FROM watchlists WHERE workspace_id = ? ORDER BY is_default DESC, id",
        (workspace_id,),
    )


def get_watchlist(conn: sqlite3.Connection, watchlist_id: int) -> dict[str, Any] | None:
    return fetch_one(conn, "SELECT * FROM watchlists WHERE id = ?", (watchlist_id,))


def create_watchlist(conn: sqlite3.Connection, name: str, workspace_id: int = 1) -> dict[str, Any]:
    now = utc_now_iso()
    cur = conn.execute(
        """
        INSERT INTO watchlists (workspace_id, name, is_default, created_at, updated_at)
        VALUES (?, ?, 0, ?, ?)
        """,
        (workspace_id, name.strip() or "Watchlist", now, now),
    )
    return fetch_one(conn, "SELECT * FROM watchlists WHERE id = ?", (int(cur.lastrowid),))  # type: ignore


def delete_watchlist(conn: sqlite3.Connection, watchlist_id: int) -> bool:
    row = get_watchlist(conn, watchlist_id)
    if not row or int(row.get("is_default") or 0) == 1:
        return False
    conn.execute("DELETE FROM watchlist_accounts WHERE watchlist_id = ?", (watchlist_id,))
    conn.execute("DELETE FROM watchlist_terms WHERE watchlist_id = ?", (watchlist_id,))
    conn.execute("DELETE FROM watchlists WHERE id = ?", (watchlist_id,))
    return True


def list_terms(conn: sqlite3.Connection, watchlist_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "SELECT * FROM watchlist_terms WHERE watchlist_id = ? ORDER BY term_type, value",
        (watchlist_id,),
    )


def add_term(
    conn: sqlite3.Connection,
    watchlist_id: int,
    term_type: str,
    value: str,
    lang: str = "mixed",
) -> dict[str, Any]:
    ttype = term_type.strip().lower()
    if ttype not in TERM_TYPES:
        raise ValueError(f"term_type must be one of {TERM_TYPES}")
    val = value.strip().lstrip("#@")
    if not val:
        raise ValueError("value required")
    if ttype == "hashtag":
        val = val.lstrip("#")
    now = utc_now_iso()
    try:
        cur = conn.execute(
            """
            INSERT INTO watchlist_terms (watchlist_id, term_type, value, lang, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (watchlist_id, ttype, val, lang, now),
        )
    except sqlite3.IntegrityError as e:
        raise ValueError("term already exists") from e
    return fetch_one(conn, "SELECT * FROM watchlist_terms WHERE id = ?", (int(cur.lastrowid),))  # type: ignore


def delete_term(conn: sqlite3.Connection, term_id: int) -> bool:
    cur = conn.execute("DELETE FROM watchlist_terms WHERE id = ?", (term_id,))
    return int(cur.rowcount or 0) > 0


def list_accounts(conn: sqlite3.Connection, watchlist_id: int) -> list[dict[str, Any]]:
    return fetch_all(
        conn,
        "SELECT * FROM watchlist_accounts WHERE watchlist_id = ? ORDER BY platform, handle",
        (watchlist_id,),
    )


def add_account(
    conn: sqlite3.Connection,
    watchlist_id: int,
    platform: str,
    handle: str,
    external_id: str | None = None,
    role: str = "creator",
) -> dict[str, Any]:
    h = handle.strip().lstrip("@")
    if not h:
        raise ValueError("handle required")
    now = utc_now_iso()
    try:
        cur = conn.execute(
            """
            INSERT INTO watchlist_accounts
              (watchlist_id, platform, handle, external_id, role, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (watchlist_id, platform.strip().lower(), h, external_id, role, now),
        )
    except sqlite3.IntegrityError as e:
        raise ValueError("account already exists") from e
    return fetch_one(conn, "SELECT * FROM watchlist_accounts WHERE id = ?", (int(cur.lastrowid),))  # type: ignore


def delete_account(conn: sqlite3.Connection, account_id: int) -> bool:
    cur = conn.execute("DELETE FROM watchlist_accounts WHERE id = ?", (account_id,))
    return int(cur.rowcount or 0) > 0


def watchlist_bundle(conn: sqlite3.Connection, watchlist_id: int) -> dict[str, Any]:
    wl = get_watchlist(conn, watchlist_id)
    if not wl:
        raise ValueError("watchlist not found")
    terms = list_terms(conn, watchlist_id)
    accounts = list_accounts(conn, watchlist_id)
    by_type: dict[str, list[str]] = {t: [] for t in TERM_TYPES}
    for t in terms:
        by_type.setdefault(t["term_type"], []).append(t["value"])
    return {
        "watchlist": wl,
        "terms": terms,
        "accounts": accounts,
        "by_type": by_type,
        "creators": [a["handle"] for a in accounts] + by_type.get("creator", []),
    }


def default_collection_context(conn: sqlite3.Connection, workspace_id: int = 1):
    from app.collectors.base import CollectionContext

    wl = ensure_default_watchlist(conn, workspace_id)
    bundle = watchlist_bundle(conn, int(wl["id"]))
    bt = bundle["by_type"]
    return CollectionContext(
        workspace_id=workspace_id,
        brands=bt.get("brand", []),
        competitors=bt.get("competitor", []),
        topics=bt.get("topic", []),
        keywords=bt.get("keyword", []),
        hashtags=bt.get("hashtag", []),
        creators=bundle.get("creators") or [],
        country="TN",
        language="fr",
    )
