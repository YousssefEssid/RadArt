import json
from typing import Any

import requests
from bs4 import BeautifulSoup

from config import settings
from utils.safety import request_headers

# Sites « page d’accueil » (scraping léger). Laisser vide = désactivé.
CURATED: list[dict[str, str]] = []

MAX_LINKS = 10


def fetch_public_page_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    status: list[dict[str, str]] = []

    for site in CURATED:
        name = site["name"]
        url = site["url"]
        category = site.get("category", "general")
        try:
            r = requests.get(url, headers=request_headers(), timeout=8, verify=settings.requests_verify_ssl)
            r.raise_for_status()
            soup = BeautifulSoup(r.text, "html.parser")
            links = []
            for a in soup.find_all("a", href=True)[:80]:
                href = a["href"].strip()
                text = (a.get_text() or "").strip()
                if not text or len(text) < 12:
                    continue
                if href.startswith("/"):
                    from urllib.parse import urljoin

                    href = urljoin(url, href)
                if not href.startswith("http"):
                    continue
                links.append((href, text))
                if len(links) >= MAX_LINKS:
                    break
            count = 0
            for href, text in links:
                items.append(
                    {
                        "source": name,
                        "platform": "public_page",
                        "title": text[:500],
                        "text": text[:2000],
                        "url": href,
                        "published_at": None,
                        "engagement": 0,
                        "category": category,
                        "raw_json": json.dumps({"page": url, "href": href}, ensure_ascii=False),
                    }
                )
                count += 1
            status.append({"source": f"page:{name}", "status": "ok", "detail": f"{count} links"})
        except Exception as e:
            status.append({"source": f"page:{name}", "status": "error", "detail": str(e)[:120]})

    return items, status
