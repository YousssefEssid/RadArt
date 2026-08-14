from __future__ import annotations

from typing import Any

from app.core.config import settings

# Market context (order-of-magnitude public estimates for Tunisia — for product honesty, not a claim of crawl coverage)
TUNISIA_MARKET = {
    "as_of": "2025–2026 public estimates",
    "facebook_users_m": 9.2,
    "instagram_users_m": 4.45,
    "tiktok_adults_reachable_m": 6.0,
    "note": (
        "Cultural intelligence for Tunisia eventually needs Facebook, Instagram, TikTok, YouTube, "
        "local news, Google, and public web — obtained legally."
    ),
}


def _has(key: str) -> bool:
    return bool((getattr(settings, key, "") or "").strip())


def build_signal_coverage() -> dict[str, Any]:
    """Honest map of what RadArt can collect today vs next — compliance first."""
    layers = [
        {
            "id": "public_feeds",
            "title": "Public feeds (live now)",
            "tier": "live",
            "compliance": "RSS / public charts / curated pages — ToS-friendly",
            "sources": [
                {"name": "Tunisian + regional RSS press", "status": "live", "needs_key": False},
                {"name": "Google News RSS (TN/FR/US queries)", "status": "live", "needs_key": False},
                {"name": "Reddit public RSS", "status": "live", "needs_key": False},
                {"name": "Apple Music / iTunes charts", "status": "live", "needs_key": False},
                {"name": "GDELT public API", "status": "live", "needs_key": False},
                {"name": "Curated public pages", "status": "live", "needs_key": False},
                {
                    "name": "Social search discovery (site:tiktok/ig/fb)",
                    "status": "live" if _has("serpapi_api_key") else "needs_key",
                    "needs_key": True,
                    "env": "SERPAPI_API_KEY",
                    "detail": "Metadata only — never crawls destination pages",
                },
            ],
        },
        {
            "id": "official_apis",
            "title": "Official APIs (when keys exist)",
            "tier": "optional_key",
            "compliance": "Vendor ToS + quotas — no unofficial scrape",
            "sources": [
                {
                    "name": "YouTube Data API",
                    "status": "live" if _has("youtube_api_key") else "needs_key",
                    "needs_key": True,
                    "env": "YOUTUBE_API_KEY",
                },
                {
                    "name": "Google Trends via SerpApi",
                    "status": "live" if _has("serpapi_api_key") else "needs_key",
                    "needs_key": True,
                    "env": "SERPAPI_API_KEY",
                },
                {
                    "name": "Meta Graph (Facebook/Instagram pages you manage or authorized)",
                    "status": "live" if _has("meta_page_access_token") else "needs_key",
                    "needs_key": True,
                    "env": "META_PAGE_ACCESS_TOKEN + META_PAGE_IDS",
                },
                {
                    "name": "TikTok official / research (when approved)",
                    "status": "live" if _has("tiktok_access_token") else "needs_key",
                    "needs_key": True,
                    "env": "TIKTOK_ACCESS_TOKEN",
                },
            ],
        },
        {
            "id": "customer_owned",
            "title": "Customer-owned data (trusted path)",
            "tier": "customer_owned",
            "compliance": "Agency/brand exports & licensed dumps they have rights to use",
            "sources": [
                {
                    "name": "Customer social / campaign exports (JSON)",
                    "status": "live",
                    "needs_key": False,
                    "path": "backend/data/customer_owned/",
                    "detail": "Upload via /api/sources/customer-owned or drop JSON files",
                },
            ],
        },
        {
            "id": "licensed_next",
            "title": "Licensed / partner coverage (roadmap)",
            "tier": "planned",
            "compliance": "Commercial data providers — required for dense Meta/TikTok firehose",
            "sources": [
                {"name": "Licensed social listening firehose (TN geo)", "status": "planned", "needs_key": False},
                {"name": "Brand-authorized Meta Business / TikTok Business integrations", "status": "planned", "needs_key": False},
                {"name": "Publisher partnerships (local media full text)", "status": "planned", "needs_key": False},
            ],
        },
        {
            "id": "never",
            "title": "Out of bounds",
            "tier": "forbidden",
            "compliance": "Do not build — breaks trust with enterprise buyers",
            "sources": [
                {"name": "Unofficial Facebook/Instagram/TikTok scrapers", "status": "forbidden", "needs_key": False},
                {"name": "Login / paywall bypass", "status": "forbidden", "needs_key": False},
                {"name": "Private inbox / non-consensual personal data", "status": "forbidden", "needs_key": False},
            ],
        },
    ]

    live = sum(1 for layer in layers for s in layer["sources"] if s["status"] == "live")
    needs = sum(1 for layer in layers for s in layer["sources"] if s["status"] == "needs_key")
    planned = sum(1 for layer in layers for s in layer["sources"] if s["status"] == "planned")

    return {
        "principle": "Don't sacrifice compliance for coverage. Official APIs, licensed providers, customer-owned data, compliant public sources.",
        "tunisia_market": TUNISIA_MARKET,
        "mvp_strength": (
            "RSS + Reddit + Google News + iTunes + optional YouTube/Trends is excellent for an MVP — "
            "not enough alone for serious Tunisian cultural intelligence."
        ),
        "next_priority": [
            "Widen Tunisian public news/culture feeds (done continuously)",
            "Turn on YouTube + SerpApi keys in production",
            "Ingest customer-owned Meta/TikTok exports (legal today)",
            "Connect Meta Graph for pages the customer authorizes",
            "Seek licensed social firehose / TikTok research partnership for dense TN reach",
        ],
        "summary": {"live": live, "needs_key": needs, "planned": planned},
        "layers": layers,
    }
