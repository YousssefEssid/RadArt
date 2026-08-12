"""Public Apple Music / iTunes charts — songs going mainstream (no API key)."""

from __future__ import annotations

import json
import time
from typing import Any

import requests

from app.core.config import settings
from app.seed_sources import ITUNES_CHARTS
from app.utils.safety import request_headers


def _from_marketing_tools(store: str, chart: str, limit: int = 25) -> list[dict[str, Any]]:
    url = f"https://rss.applemarketingtools.com/api/v2/{store}/music/most-played/{limit}/{chart}.json"
    r = requests.get(url, headers=request_headers(), timeout=10, verify=settings.requests_verify_ssl)
    r.raise_for_status()
    results = ((r.json().get("feed") or {}).get("results") or [])
    out: list[dict[str, Any]] = []
    for i, row in enumerate(results[:limit], start=1):
        title = (row.get("name") or "").strip()
        artist = (row.get("artistName") or "").strip()
        if not title:
            continue
        full = f"{title} — {artist}" if artist else title
        out.append(
            {
                "rank": i,
                "title": full,
                "artist": artist,
                "url": row.get("url") or "",
                "text": f"Chart #{i} · {store.upper()} · {chart} · {artist}",
            }
        )
    return out


def _from_itunes_rss(store: str, kind: str) -> list[dict[str, Any]]:
    url = f"https://itunes.apple.com/{store}/rss/{kind}/limit=25/json"
    r = requests.get(url, headers=request_headers(), timeout=10, verify=settings.requests_verify_ssl)
    r.raise_for_status()
    entries = (r.json().get("feed") or {}).get("entry") or []
    if isinstance(entries, dict):
        entries = [entries]
    out: list[dict[str, Any]] = []
    for i, entry in enumerate(entries[:25], start=1):
        title = ""
        name = entry.get("im:name") or {}
        if isinstance(name, dict):
            title = (name.get("label") or "").strip()
        artist = ""
        art = entry.get("im:artist") or {}
        if isinstance(art, dict):
            artist = (art.get("label") or "").strip()
        if not title:
            continue
        link = ""
        links = entry.get("link")
        if isinstance(links, list) and links:
            link = ((links[0] or {}).get("attributes") or {}).get("href") or ""
        elif isinstance(links, dict):
            link = ((links.get("attributes") or {}).get("href")) or ""
        summary = entry.get("summary") or {}
        text = summary.get("label") if isinstance(summary, dict) else ""
        out.append(
            {
                "rank": i,
                "title": f"{title} — {artist}" if artist else title,
                "artist": artist,
                "url": link,
                "text": (text or f"Chart #{i} · {store.upper()} · {kind} · {artist}").strip(),
            }
        )
    return out


def fetch_itunes_chart_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    status: list[dict[str, str]] = []

    for spec in ITUNES_CHARTS:
        store = spec["store"]
        kind = spec["kind"]
        category = spec.get("category", "culture")
        label = spec.get("label") or f"Apple Music {store} {kind}"
        chart = "songs" if "song" in kind else ("albums" if "album" in kind else "songs")
        try:
            rows = _from_marketing_tools(store, chart)
            if not rows:
                rows = _from_itunes_rss(store, kind)
            count = 0
            for row in rows:
                i = int(row["rank"])
                items.append(
                    {
                        "source": label,
                        "platform": "itunes",
                        "title": str(row["title"])[:500],
                        "text": str(row.get("text") or "")[:2000],
                        "url": row.get("url") or "",
                        "published_at": None,
                        "engagement": max(50, 26000 - i * 900),
                        "category": category,
                        "raw_json": json.dumps(
                            {"store": store, "kind": kind, "rank": i, "artist": row.get("artist")},
                            ensure_ascii=False,
                        ),
                    }
                )
                count += 1
            status.append({"source": label, "status": "ok" if count else "error", "detail": f"{count} tracks"})
        except Exception as e:
            status.append({"source": label, "status": "error", "detail": str(e)[:200]})
        time.sleep(0.25)

    return items, status
