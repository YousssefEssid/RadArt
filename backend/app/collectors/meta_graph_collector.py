"""Meta Graph API collector — only authorized pages via official Graph endpoints."""

from __future__ import annotations

from typing import Any

import requests

from app.core.config import settings
from app.utils.safety import request_headers


def fetch_meta_graph_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    status: list[dict[str, str]] = []
    token = (settings.meta_page_access_token or "").strip()
    page_ids = [p.strip() for p in (settings.meta_page_ids or "").split(",") if p.strip()]

    if not token:
        status.append(
            {
                "source": "Meta Graph API",
                "status": "skipped",
                "detail": "no META_PAGE_ACCESS_TOKEN (official pages you manage/authorize only)",
            }
        )
        return items, status
    if not page_ids:
        status.append(
            {
                "source": "Meta Graph API",
                "status": "skipped",
                "detail": "set META_PAGE_IDS (comma-separated page ids)",
            }
        )
        return items, status

    # Official: https://developers.facebook.com/docs/graph-api/
    for page_id in page_ids[:8]:
        try:
            url = f"https://graph.facebook.com/v19.0/{page_id}/posts"
            r = requests.get(
                url,
                params={
                    "access_token": token,
                    "fields": "id,message,created_time,permalink_url",
                    "limit": 10,
                },
                headers=request_headers(),
                timeout=8,
            )
            if r.status_code >= 400:
                status.append(
                    {
                        "source": f"Meta Graph:{page_id}",
                        "status": "error",
                        "detail": r.text[:180],
                    }
                )
                continue
            data = r.json()
            for post in data.get("data") or []:
                msg = (post.get("message") or "").strip()
                if not msg:
                    continue
                title = msg.split("\n", 1)[0][:180]
                items.append(
                    {
                        "source": f"Meta page {page_id}",
                        "platform": "facebook",
                        "title": title,
                        "text": msg[:3000],
                        "url": post.get("permalink_url") or "",
                        "published_at": post.get("created_time"),
                        "engagement": 0,
                        "category": "lifestyle",
                        "raw_json": post,
                    }
                )
            status.append({"source": f"Meta Graph:{page_id}", "status": "ok", "detail": f"{len(data.get('data') or [])} posts"})
        except Exception as e:
            status.append({"source": f"Meta Graph:{page_id}", "status": "error", "detail": str(e)[:180]})

    if not status:
        status.append({"source": "Meta Graph API", "status": "skipped", "detail": "no pages processed"})
    return items, status
