"""Public Reddit RSS (Atom) — no login.

Unauthenticated .json is blocked (403). .rss still works; keep request count low to avoid 429.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any

import feedparser
import requests

from app.core.config import settings
from app.seed_sources import REDDIT_FEEDS
from app.utils.safety import request_headers


def _published(entry: Any) -> str | None:
    parsed = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
    if not parsed:
        return None
    try:
        return datetime(*parsed[:6]).isoformat() + "Z"
    except (TypeError, ValueError):
        return None


def fetch_reddit_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    status: list[dict[str, str]] = []
    verify = settings.requests_verify_ssl

    for spec in REDDIT_FEEDS:
        name = spec["name"]
        path = spec["path"]
        category = spec.get("category", "viral")
        url = f"https://www.reddit.com/r/{path}/.rss"
        try:
            r = requests.get(url, headers=request_headers(), timeout=15, verify=verify)
            r.raise_for_status()
            parsed = feedparser.parse(r.content)
            count = 0
            for i, entry in enumerate(parsed.entries[:25]):
                title = (entry.get("title") or "").strip()
                if not title:
                    continue
                link = entry.get("link") or ""
                summary = (entry.get("summary") or entry.get("description") or "")[:2000]
                items.append(
                    {
                        "source": name,
                        "platform": "reddit",
                        "title": title[:500],
                        "text": summary or title,
                        "url": link,
                        "published_at": _published(entry),
                        "engagement": max(20, 5000 - i * 140),
                        "category": category,
                        "raw_json": json.dumps({"feed": url, "path": path}, ensure_ascii=False),
                    }
                )
                count += 1
            status.append(
                {
                    "source": f"Reddit:{name}",
                    "status": "ok" if count else "error",
                    "detail": f"{count} posts" if count else "empty feed",
                }
            )
        except Exception as e:
            status.append({"source": f"Reddit:{name}", "status": "error", "detail": str(e)[:200]})
        time.sleep(1.5)

    return items, status
