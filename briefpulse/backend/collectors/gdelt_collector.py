import json
import time
from typing import Any

import requests

from seed_sources import GDELT_KEYWORDS
from utils.safety import request_headers


def _combined_query(keywords: list[str]) -> str:
    parts: list[str] = []
    for kw in keywords:
        s = kw.strip()
        if not s:
            continue
        if any(x in s for x in (" ", '"', "(", ")")):
            parts.append(f'"{s}"')
        else:
            parts.append(s)
    return " OR ".join(parts[:8])


def fetch_gdelt_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    """
    GDELT doc API — use ONE combined query per run to avoid 429 (Too Many Requests)
    from firing sequential keyword searches.
    """
    items: list[dict[str, Any]] = []
    status: list[dict[str, str]] = []
    url = "https://api.gdeltproject.org/api/v2/doc/doc"
    query = _combined_query(GDELT_KEYWORDS)
    if not query:
        status.append({"source": "GDELT", "status": "skipped", "detail": "no keywords"})
        return items, status

    params = {"query": query, "mode": "artlist", "maxrecords": 25, "format": "json"}
    last_err: str | None = None
    for attempt in range(2):
        try:
            r = requests.get(url, params=params, headers=request_headers(), timeout=15)
            if r.status_code == 429:
                last_err = r.text[:120]
                time.sleep(4.0 * (attempt + 1))
                continue
            r.raise_for_status()
            data = r.json()
            arts = data.get("articles", data.get("artlist", []))
            if isinstance(arts, dict):
                arts = arts.get("results", [])
            count = 0
            for art in arts[:25]:
                if not isinstance(art, dict):
                    continue
                title = (art.get("title") or art.get("Title") or "").strip() or "GDELT"
                u = art.get("url") or art.get("urlsocial") or ""
                seen = art.get("seendate") or art.get("datetime")
                domain = art.get("domain") or "GDELT"
                raw = art
                items.append(
                    {
                        "source": domain,
                        "platform": "gdelt",
                        "title": title,
                        "text": title[:2000],
                        "url": u,
                        "published_at": seen,
                        "engagement": 0,
                        "category": "news",
                        "raw_json": json.dumps(raw, ensure_ascii=False)[:8000],
                    }
                )
                count += 1
            status.append(
                {
                    "source": "GDELT (combined)",
                    "status": "ok",
                    "detail": f"{count} items · q={query[:80]}",
                }
            )
            return items, status
        except Exception as e:
            last_err = str(e)[:200]
            time.sleep(2.0 * (attempt + 1))

    status.append({"source": "GDELT (combined)", "status": "error", "detail": last_err or "failed"})
    return items, status
