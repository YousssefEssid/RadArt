"""Social Search Discovery — search-result metadata only, never crawl destination pages."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import requests

from app.collectors.base import (
    BaseCollector,
    CollectedItem,
    CollectionContext,
    CollectorHealth,
    SourceMethod,
    confidence_for,
)
from app.core.config import settings
from app.utils.safety import request_headers
from app.utils.time_utils import utc_now_iso

_SITE_PLATFORMS = (
    ("tiktok.com", "tiktok"),
    ("instagram.com", "instagram"),
    ("facebook.com", "facebook"),
    ("fb.com", "facebook"),
    ("www.facebook.com", "facebook"),
)


def detect_platform_from_url(url: str) -> str | None:
    try:
        host = (urlparse(url).hostname or "").lower().removeprefix("www.")
    except Exception:
        return None
    for domain, platform in _SITE_PLATFORMS:
        d = domain.removeprefix("www.")
        if host == d or host.endswith("." + d):
            return platform
    return None


def build_discovery_queries(context: CollectionContext, *, max_queries: int = 12) -> list[tuple[str, str]]:
    """Return list of (query, platform) from watchlist terms."""
    terms = context.all_terms()[:20]
    if not terms:
        terms = ["Tunisia", "Tunisie"]
    platforms_sites = [
        ("tiktok", "tiktok.com"),
        ("instagram", "instagram.com"),
        ("facebook", "facebook.com"),
    ]
    queries: list[tuple[str, str]] = []
    for term in terms:
        t = term.strip().strip('"')
        if not t:
            continue
        for platform, site in platforms_sites:
            # Prefer Tunisia-local framing for brand/competitor names
            if term in context.brands or term in context.competitors:
                q = f'site:{site} "{t}" Tunisia'
            elif t.startswith("#"):
                q = f"site:{site} {t}"
            else:
                q = f'site:{site} "{t}"'
            queries.append((q, platform))
            if len(queries) >= max_queries:
                return queries
    return queries


def parse_serpapi_organic(data: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for it in data.get("organic_results") or []:
        link = (it.get("link") or it.get("url") or "").strip()
        if not link:
            continue
        rows.append(
            {
                "url": link,
                "title": (it.get("title") or "").strip() or link,
                "snippet": (it.get("snippet") or it.get("snippet_highlighted_words") or "")
                if isinstance(it.get("snippet"), str)
                else " ".join(it.get("snippet_highlighted_words") or []),
                "date": it.get("date"),
            }
        )
    return rows


class SocialSearchDiscoveryCollector(BaseCollector):
    source = "Social Search Discovery"
    source_method = SourceMethod.SEARCH_DISCOVERY
    provider = "search"
    enabled = True

    def credentials_ready(self) -> bool:
        return bool((settings.serpapi_api_key or "").strip()) or bool(
            (getattr(settings, "search_discovery_api_key", "") or "").strip()
        )

    async def collect(self, context: CollectionContext) -> list[CollectedItem]:
        key = (settings.serpapi_api_key or getattr(settings, "search_discovery_api_key", "") or "").strip()
        if not key:
            return []

        max_q = int(getattr(settings, "search_discovery_max_queries_per_run", 6) or 6)
        queries = build_discovery_queries(context, max_queries=max_q)
        seen_urls: set[str] = set()
        out: list[CollectedItem] = []
        now = utc_now_iso()
        conf = confidence_for(self.source_method)

        for query, expected_platform in queries:
            try:
                r = requests.get(
                    "https://serpapi.com/search.json",
                    params={
                        "engine": "google",
                        "q": query,
                        "api_key": key,
                        "num": 8,
                        "hl": context.language or "fr",
                        "gl": (context.country or "tn").lower(),
                    },
                    headers=request_headers(),
                    timeout=12,
                )
                if r.status_code >= 400:
                    continue
                for row in parse_serpapi_organic(r.json()):
                    url = row["url"]
                    # Normalize URL for dedupe
                    norm = re.sub(r"[?#].*$", "", url).rstrip("/").lower()
                    if norm in seen_urls:
                        continue
                    seen_urls.add(norm)
                    platform = detect_platform_from_url(url) or expected_platform
                    # Never fetch destination page — metadata only
                    out.append(
                        CollectedItem(
                            platform=platform,
                            source_type="search_discovery",
                            source_method=self.source_method.value,
                            provider=self.provider,
                            title=row["title"][:500],
                            text=str(row.get("snippet") or "")[:2000],
                            url=url,
                            external_id=norm,
                            published_at=row.get("date"),
                            collected_at=now,
                            confidence=conf,
                            country=context.country or "TN",
                            language=context.language,
                            source=f"Search · {platform}",
                            category="discovery",
                            keywords=[query],
                            raw_metadata_json={
                                "query": query,
                                "expected_platform": expected_platform,
                                "snippet": row.get("snippet"),
                                "note": "Indexed search hit — not authoritative platform analytics",
                            },
                        )
                    )
                    if len(out) >= context.max_items_per_source:
                        return out
            except Exception:
                continue
        return out

    async def healthcheck(self) -> CollectorHealth:
        ready = self.credentials_ready()
        return CollectorHealth(
            source=self.source,
            enabled=self.enabled,
            credential_status="connected" if ready else "awaiting_credentials",
            source_method=self.source_method.value,
            provider=self.provider,
            detail=(
                None
                if ready
                else "Needs SERPAPI_API_KEY (Google search) — ingest titles/snippets/URLs only"
            ),
            last_error=None if ready else "SERPAPI_API_KEY",
        )
