from __future__ import annotations

import asyncio
import json
import sqlite3
from typing import Any

from app.collectors.base import CollectedItem, CollectionContext
from app.collectors.registry import build_all_collectors
from app.core.database import get_connection
from app.repositories.watchlist_repository import default_collection_context
from app.services.text_service import enrich_item
from app.services.trend_seed_service import expand_seeds
from app.utils.hashing import stable_hash
from app.utils.time_utils import utc_now_iso


def purge_demo_media(conn: sqlite3.Connection) -> int:
    cur = conn.execute(
        """
        DELETE FROM media_items
        WHERE platform = 'mock_social'
           OR platform = 'curated'
           OR source LIKE 'Mock %'
           OR source = 'Veille RadArt'
           OR IFNULL(url, '') LIKE 'mock://%'
           OR IFNULL(source_method, '') = 'mock'
        """
    )
    return int(cur.rowcount or 0)


def _serialize_list(val: Any) -> str | None:
    if val is None:
        return None
    if isinstance(val, str):
        return val
    return json.dumps(val, ensure_ascii=False)


async def collect_all_normalized(context: CollectionContext | None = None) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    ctx = context or CollectionContext()
    # Trend seed expansions feed discovery / optional query budgets
    seeds = expand_seeds(
        ctx.brands + ctx.competitors + ctx.topics + ctx.keywords + ctx.hashtags[:8],
        max_total=24,
    )
    ctx.seed_queries = seeds
    ctx.extra["seed_queries"] = seeds

    collectors = build_all_collectors()
    all_items: list[dict[str, Any]] = []
    all_status: list[dict[str, str]] = []
    seen_hash: set[str] = set()

    for col in collectors:
        try:
            collected: list[CollectedItem] = await col.collect(ctx)
            health = await col.healthcheck()
            for c in collected:
                d = c.to_ingest_dict()
                h = stable_hash(d.get("platform"), d.get("source_method"), d.get("title"), d.get("url") or d.get("external_id"))
                if h in seen_hash:
                    continue
                seen_hash.add(h)
                all_items.append(d)
            status = "ok" if collected else ("skipped" if health.credential_status == "awaiting_credentials" else "ok")
            all_status.append(
                {
                    "source": col.source,
                    "status": status if health.credential_status != "error" else "error",
                    "detail": health.detail or health.last_error or f"{len(collected)} items",
                }
            )
        except Exception as e:
            all_status.append({"source": getattr(col, "source", "?"), "status": "error", "detail": str(e)[:160]})

    return all_items, all_status


def collect_all_raw() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """Sync entry used by scheduler — runs async registry."""
    with get_connection() as conn:
        ctx = default_collection_context(conn)
    return asyncio.run(collect_all_normalized(ctx))


def insert_items(conn: sqlite3.Connection, items: list[dict[str, Any]]) -> int:
    inserted = 0
    now = utc_now_iso()
    for raw in items:
        item = enrich_item(dict(raw))
        # Preserve structured social fields after enrich
        if raw.get("hashtags") and not item.get("hashtags"):
            item["hashtags"] = raw["hashtags"]
        if raw.get("mentions") and not item.get("mentions"):
            item["mentions"] = raw["mentions"]
        h = stable_hash(
            item.get("platform"),
            item.get("source_method") or item.get("source"),
            item.get("title"),
            item.get("url") or item.get("external_id"),
        )
        try:
            conn.execute(
                """
                INSERT INTO media_items (
                  hash, external_id, source, platform, title, text, url, published_at, collected_at,
                  author, author_name, author_external_id, engagement,
                  views, likes, comments, shares,
                  language, category, keywords, entities, sentiment, raw_json,
                  source_type, source_method, provider, hashtags, mentions, country, confidence,
                  raw_metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    h,
                    item.get("external_id"),
                    item.get("source") or item.get("provider") or item.get("platform"),
                    item["platform"],
                    item["title"],
                    item.get("text"),
                    item.get("url"),
                    item.get("published_at"),
                    item.get("collected_at") or now,
                    item.get("author") or item.get("author_name"),
                    item.get("author_name"),
                    item.get("author_external_id"),
                    int(item.get("engagement") or 0),
                    item.get("views"),
                    item.get("likes"),
                    item.get("comments"),
                    item.get("shares"),
                    item.get("language"),
                    item.get("category"),
                    _serialize_list(item.get("keywords")),
                    item.get("entities"),
                    item.get("sentiment"),
                    (
                        item.get("raw_json")
                        if isinstance(item.get("raw_json"), str)
                        else json.dumps(item.get("raw_json") or item.get("raw_metadata_json") or {})
                    )[:12000],
                    item.get("source_type"),
                    item.get("source_method"),
                    item.get("provider"),
                    _serialize_list(item.get("hashtags")),
                    _serialize_list(item.get("mentions")),
                    item.get("country"),
                    item.get("confidence"),
                    (
                        item.get("raw_metadata_json")
                        if isinstance(item.get("raw_metadata_json"), str)
                        else json.dumps(item.get("raw_metadata_json") or {})
                    )[:12000],
                ),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass
    return inserted


def _ingest_into(conn: sqlite3.Connection, items: list[dict[str, Any]]) -> int:
    purge_demo_media(conn)
    return insert_items(conn, items)


def run_ingestion(conn: sqlite3.Connection | None = None) -> tuple[int, list[dict[str, str]]]:
    if conn is not None:
        ctx = default_collection_context(conn)
        items, status = asyncio.run(collect_all_normalized(ctx))
        return _ingest_into(conn, items), status
    with get_connection() as c:
        ctx = default_collection_context(c)
        items, status = asyncio.run(collect_all_normalized(ctx))
        return _ingest_into(c, items), status
