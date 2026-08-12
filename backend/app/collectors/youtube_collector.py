import json
from typing import Any

import requests

from app.core.config import settings
from app.seed_sources import YOUTUBE_QUERIES
from app.utils.safety import request_headers


def fetch_youtube_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    status: list[dict[str, str]] = []
    key = (settings.youtube_api_key or "").strip()
    max_q = max(0, int(settings.youtube_max_search_queries_per_run or 0))
    queries = YOUTUBE_QUERIES[:max_q] if max_q else []

    if not key:
        status.append({"source": "YouTube API", "status": "skipped", "detail": "no API key"})
        return items, status
    if not queries:
        status.append(
            {
                "source": "YouTube API",
                "status": "skipped",
                "detail": "youtube_max_search_queries_per_run is 0",
            }
        )
        return items, status

    # Official API: https://developers.google.com/youtube/v3/docs/search/list
    base = "https://www.googleapis.com/youtube/v3/search"
    for q in queries:
        try:
            params = {
                "part": "snippet",
                "q": q,
                "type": "video",
                "maxResults": 5,
                "key": key,
                # Smaller payloads; see https://developers.google.com/youtube/v3/getting-started#partial
                "fields": "items(id/videoId,snippet(title,description,publishedAt,channelTitle))",
            }
            r = requests.get(base, params=params, headers=request_headers(), timeout=8)
            r.raise_for_status()
            data = r.json()
            for it in data.get("items", []):
                sn = it.get("snippet") or {}
                vid = (it.get("id") or {}).get("videoId")
                if not vid:
                    continue
                title = (sn.get("title") or "").strip() or "Video"
                desc = (sn.get("description") or "")[:2000]
                channel = sn.get("channelTitle") or "YouTube"
                pub = sn.get("publishedAt")
                url = f"https://www.youtube.com/watch?v={vid}"
                raw = {"query": q, "videoId": vid, "snippet": sn}
                items.append(
                    {
                        "source": channel,
                        "platform": "youtube",
                        "title": title,
                        "text": desc,
                        "url": url,
                        "published_at": pub,
                        "engagement": 0,
                        "category": "youtube",
                        "raw_json": json.dumps(raw, ensure_ascii=False),
                    }
                )
            status.append({"source": f"YouTube:{q[:20]}", "status": "ok", "detail": "fetched"})
        except Exception as e:
            status.append({"source": f"YouTube:{q[:20]}", "status": "error", "detail": str(e)[:120]})

    return items, status
