import json
from datetime import datetime
from typing import Any

import feedparser
import requests

from config import settings
from seed_sources import RSS_SOURCES
from utils.safety import request_headers
from utils.time_utils import utc_now_iso


def _published(entry: dict) -> str | None:
    if getattr(entry, "published_parsed", None):
        try:
            t = entry.published_parsed
            return datetime(*t[:6]).isoformat() + "Z"
        except (TypeError, ValueError):
            pass
    if getattr(entry, "updated_parsed", None):
        try:
            t = entry.updated_parsed
            return datetime(*t[:6]).isoformat() + "Z"
        except (TypeError, ValueError):
            pass
    return None


def fetch_rss_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    source_status: list[dict[str, str]] = []

    verify = settings.requests_verify_ssl

    for src in RSS_SOURCES:
        name = src["name"]
        primary = src["url"]
        fallbacks = list(src.get("fallback_urls") or [])
        urls_to_try = [primary] + fallbacks
        category = src.get("category", "general")
        last_err: Exception | None = None
        parsed = None
        used_url = primary
        for url in urls_to_try:
            try:
                resp = requests.get(url, headers=request_headers(), timeout=8, verify=verify)
                resp.raise_for_status()
                parsed = feedparser.parse(resp.content)
                if getattr(parsed, "entries", None):
                    used_url = url
                    break
            except Exception as e:
                last_err = e
                parsed = None
        try:
            if parsed is None or not getattr(parsed, "entries", None):
                raise last_err or RuntimeError("empty feed")
            count = 0
            for entry in parsed.entries[:40]:
                title = (entry.get("title") or "").strip() or "Untitled"
                link = entry.get("link") or ""
                summary = (entry.get("summary") or entry.get("description") or "")[:2000]
                pub = _published(entry)
                raw = {
                    "feed_url": used_url,
                    "title": title,
                    "link": link,
                    "summary": summary,
                    "published": pub,
                }
                items.append(
                    {
                        "source": name,
                        "platform": "rss",
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
            src_detail = f"{count} items"
            if used_url != primary:
                src_detail += f" ({used_url})"
            source_status.append({"source": name, "status": "ok", "detail": src_detail})
        except Exception as e:
            source_status.append({"source": name, "status": "error", "detail": str(e)[:200]})

    return items, source_status
