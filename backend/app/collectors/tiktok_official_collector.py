"""TikTok official adapter — token required; never scrape the app."""

from __future__ import annotations

from typing import Any

import requests

from app.core.config import settings
from app.utils.safety import request_headers


def fetch_tiktok_official_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    status: list[dict[str, str]] = []
    token = (settings.tiktok_access_token or "").strip()

    if not token:
        status.append(
            {
                "source": "TikTok Official API",
                "status": "skipped",
                "detail": (
                    "no TIKTOK_ACCESS_TOKEN — use Research/Display API approval or "
                    "customer-owned exports (backend/data/customer_owned/)"
                ),
            }
        )
        return items, status

    # Display API video list for authorized account (shape may vary by product).
    # Docs evolve: https://developers.tiktok.com/
    try:
        r = requests.get(
            "https://open.tiktokapis.com/v2/video/list/",
            headers={
                **request_headers(),
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            params={"max_count": 10},
            timeout=8,
        )
        if r.status_code >= 400:
            status.append(
                {
                    "source": "TikTok Official API",
                    "status": "error",
                    "detail": r.text[:200],
                }
            )
            return items, status
        data = r.json()
        videos = ((data.get("data") or {}).get("videos")) or data.get("videos") or []
        for v in videos:
            title = (v.get("title") or v.get("video_description") or "TikTok video").strip()
            items.append(
                {
                    "source": v.get("username") or "TikTok",
                    "platform": "tiktok",
                    "title": title[:500],
                    "text": (v.get("video_description") or title)[:3000],
                    "url": v.get("share_url") or "",
                    "published_at": v.get("create_time"),
                    "engagement": int(v.get("view_count") or v.get("like_count") or 0),
                    "category": "viral",
                    "raw_json": v,
                }
            )
        status.append({"source": "TikTok Official API", "status": "ok", "detail": f"{len(items)} videos"})
    except Exception as e:
        status.append({"source": "TikTok Official API", "status": "error", "detail": str(e)[:180]})
    return items, status
