"""
Google News topic RSS (public URLs). Complements trend signals; not the same as trends.google.com charts.

There is no official Google Trends REST API with API keys. For interest-over-time style data,
options are unofficial libraries (e.g. pytrends) or third-party providers — use at your own risk.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from typing import Any
from urllib.parse import quote_plus

import feedparser
import requests

from config import settings
from seed_sources import GOOGLE_NEWS_RSS_QUERIES
from utils.safety import request_headers


def _rss_url(query: str) -> str:
    # French / Tunisia-centric discovery; hl/gl/ceid follow Google News RSS conventions.
    q = quote_plus(query)
    return f"https://news.google.com/rss/search?q={q}&hl=fr&gl=TN&ceid=TN:fr"


def _published(entry: Any) -> str | None:
    if getattr(entry, "published_parsed", None):
        try:
            t = entry.published_parsed
            return datetime(*t[:6]).isoformat() + "Z"
        except (TypeError, ValueError):
            pass
    return None


def fetch_google_news_rss_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    status: list[dict[str, str]] = []

    verify = settings.requests_verify_ssl
    for spec in GOOGLE_NEWS_RSS_QUERIES:
        q = spec["q"]
        category = spec.get("category", "general")
        url = _rss_url(q)
        try:
            resp = requests.get(url, headers=request_headers(), timeout=10, verify=verify)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
            count = 0
            for entry in parsed.entries[:20]:
                title = (getattr(entry, "title", None) or "").strip() or "News"
                link = getattr(entry, "link", None) or ""
                summary = (getattr(entry, "summary", None) or getattr(entry, "description", None) or "")[
                    :2000
                ]
                pub = _published(entry)
                raw = {"query": q, "title": title, "link": link, "published": pub}
                items.append(
                    {
                        "source": "Google News",
                        "platform": "google_news_rss",
                        "title": title,
                        "text": summary,
                        "url": link,
                        "published_at": pub,
                        "engagement": 0,
                        "category": category,
                        "raw_json": json.dumps(raw, ensure_ascii=False),
                    }
                )
                count += 1
            status.append({"source": f"Google News:{q[:24]}", "status": "ok", "detail": f"{count} items"})
        except Exception as e:
            status.append(
                {"source": f"Google News:{q[:24]}", "status": "error", "detail": str(e)[:200]}
            )
        time.sleep(0.4)

    return items, status
