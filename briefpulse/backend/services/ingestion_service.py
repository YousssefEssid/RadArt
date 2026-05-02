from __future__ import annotations

import json
import sqlite3
from typing import Any

from collectors import (
    fetch_gdelt_items,
    fetch_google_news_rss_items,
    fetch_mock_social_items,
    fetch_public_page_items,
    fetch_rss_items,
    fetch_serpapi_google_trends_items,
    fetch_youtube_items,
)
from db import get_connection
from services.text_service import enrich_item
from utils.hashing import stable_hash
from utils.time_utils import utc_now_iso

RADAR_SEED_ITEMS: list[dict[str, Any]] = [
    {
        "source": "Veille RADJ",
        "platform": "curated",
        "title": "Canicule: Tunisiens cherchent fraîcheur et boissons",
        "text": "Vague de chaleur: discussions sur boissons fraîches, climatisation et transport.",
        "url": "",
        "published_at": None,
        "engagement": 300,
        "category": "weather",
    },
    {
        "source": "Veille RADJ",
        "platform": "curated",
        "title": "Étudiants: blagues sur examens et café",
        "text": "Humour étudiant autour des examens, nuits blanches et café pour réviser.",
        "url": "",
        "published_at": None,
        "engagement": 450,
        "category": "youth",
    },
    {
        "source": "Veille RADJ",
        "platform": "curated",
        "title": "Prix et promotions: sensibilité au budget",
        "text": "Inflation et promotions dans les supermarchés tunisiens.",
        "url": "",
        "published_at": None,
        "engagement": 280,
        "category": "economy",
    },
    {
        "source": "Veille RADJ",
        "platform": "curated",
        "title": "Derby football: ambiance avant le match",
        "text": "Supporters et médias parlent du derby et de l'ambiance au stade.",
        "url": "",
        "published_at": None,
        "engagement": 900,
        "category": "sport",
    },
    {
        "source": "Veille RADJ",
        "platform": "curated",
        "title": "Tourisme: saison estivale sur la côte",
        "text": "Hôtels et activités pour les visiteurs en Tunisie cet été.",
        "url": "",
        "published_at": None,
        "engagement": 320,
        "category": "culture",
    },
    {
        "source": "Veille RADJ",
        "platform": "curated",
        "title": "Festival culturel annoncé en ville",
        "text": "Programme musical et artistes pour le festival local.",
        "url": "",
        "published_at": None,
        "engagement": 210,
        "category": "culture",
    },
    {
        "source": "Veille RADJ",
        "platform": "curated",
        "title": "Soins été: routines beauté sous chaleur",
        "text": "Conseils skincare et protection solaire pour l'été.",
        "url": "",
        "published_at": None,
        "engagement": 190,
        "category": "lifestyle",
    },
    {
        "source": "Veille RADJ",
        "platform": "curated",
        "title": "Retards transports: usagers frustrés",
        "text": "Files et retards sur certaines lignes; discussions sur les trajets quotidiens.",
        "url": "",
        "published_at": None,
        "engagement": 160,
        "category": "economy",
    },
]


def collect_all_raw() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    all_items: list[dict[str, Any]] = []
    all_status: list[dict[str, str]] = []

    for fn in (
        fetch_mock_social_items,
        fetch_rss_items,
        fetch_google_news_rss_items,
        fetch_serpapi_google_trends_items,
        fetch_youtube_items,
        fetch_gdelt_items,
        fetch_public_page_items,
    ):
        items, status = fn()
        all_items.extend(items)
        all_status.extend(status)

    return all_items, all_status


def insert_items(conn: sqlite3.Connection, items: list[dict[str, Any]]) -> int:
    inserted = 0
    now = utc_now_iso()
    for raw in items:
        item = enrich_item(raw)
        h = stable_hash(item.get("platform"), item.get("source"), item.get("title"), item.get("url"))
        try:
            conn.execute(
                """
                INSERT INTO media_items (
                  hash, source, platform, title, text, url, published_at, collected_at,
                  engagement, language, category, keywords, entities, sentiment, raw_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    h,
                    item["source"],
                    item["platform"],
                    item["title"],
                    item.get("text"),
                    item.get("url"),
                    item.get("published_at"),
                    now,
                    int(item.get("engagement") or 0),
                    item.get("language"),
                    item.get("category"),
                    item.get("keywords"),
                    item.get("entities"),
                    item.get("sentiment"),
                    (item.get("raw_json") if isinstance(item.get("raw_json"), str) else json.dumps(item.get("raw_json") or {}))[:12000],
                ),
            )
            inserted += 1
        except sqlite3.IntegrityError:
            pass
    return inserted


def _ingest_into(conn: sqlite3.Connection, items: list[dict[str, Any]]) -> int:
    n = insert_items(conn, items)
    total = int(conn.execute("SELECT COUNT(*) AS c FROM media_items").fetchone()[0])
    if total == 0:
        n += insert_items(conn, RADAR_SEED_ITEMS)
    return n


def run_ingestion(conn: sqlite3.Connection | None = None) -> tuple[int, list[dict[str, str]]]:
    items, status = collect_all_raw()
    if conn is not None:
        return _ingest_into(conn, items), status
    with get_connection() as c:
        return _ingest_into(c, items), status
