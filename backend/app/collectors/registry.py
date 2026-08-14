"""Collector registry — provider-agnostic entry point for ingestion."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.collectors.base import BaseCollector, SourceMethod
from app.collectors.legacy_adapter import LegacyFetchCollector
from app.core.config import settings

if TYPE_CHECKING:
    pass


def _has(key: str) -> bool:
    return bool((getattr(settings, key, "") or "").strip())


def _youtube_creds() -> tuple[bool, str]:
    return (_has("youtube_api_key"), "YOUTUBE_API_KEY" if not _has("youtube_api_key") else "ok")


def _serpapi_creds() -> tuple[bool, str]:
    return (_has("serpapi_api_key"), "SERPAPI_API_KEY" if not _has("serpapi_api_key") else "ok")


def build_legacy_collectors() -> list[BaseCollector]:
    """Existing sync collectors wrapped — behavior preserved."""
    from app.collectors.customer_owned_collector import fetch_customer_owned_items
    from app.collectors.gdelt_collector import fetch_gdelt_items
    from app.collectors.google_news_rss_collector import fetch_google_news_rss_items
    from app.collectors.itunes_charts_collector import fetch_itunes_chart_items
    from app.collectors.public_page_collector import fetch_public_page_items
    from app.collectors.reddit_collector import fetch_reddit_items
    from app.collectors.rss_collector import fetch_rss_items
    from app.collectors.serpapi_google_trends_collector import fetch_serpapi_google_trends_items
    from app.collectors.youtube_collector import fetch_youtube_items

    return [
        LegacyFetchCollector(
            source="Customer-owned exports",
            fetch_fn=fetch_customer_owned_items,
            source_method=SourceMethod.MANUAL,
            provider="customer_owned",
            platform="customer_owned",
        ),
        LegacyFetchCollector(
            source="Tunisian media RSS",
            fetch_fn=fetch_rss_items,
            source_method=SourceMethod.RSS,
            provider="rss",
            platform="rss",
        ),
        LegacyFetchCollector(
            source="Google News",
            fetch_fn=fetch_google_news_rss_items,
            source_method=SourceMethod.RSS,
            provider="google_news",
            platform="google_news_rss",
        ),
        LegacyFetchCollector(
            source="Reddit",
            fetch_fn=fetch_reddit_items,
            source_method=SourceMethod.PUBLIC_FEED,
            provider="reddit",
            platform="reddit",
        ),
        LegacyFetchCollector(
            source="Apple Music charts",
            fetch_fn=fetch_itunes_chart_items,
            source_method=SourceMethod.OFFICIAL_PUBLIC_API,
            provider="itunes",
            platform="itunes",
        ),
        LegacyFetchCollector(
            source="Google Trends (SerpApi)",
            fetch_fn=fetch_serpapi_google_trends_items,
            source_method=SourceMethod.OFFICIAL_API,
            provider="serpapi",
            platform="google_trends",
            credential_check=_serpapi_creds,
        ),
        LegacyFetchCollector(
            source="YouTube",
            fetch_fn=fetch_youtube_items,
            source_method=SourceMethod.OFFICIAL_API,
            provider="youtube",
            platform="youtube",
            credential_check=_youtube_creds,
        ),
        # Meta / TikTok official paths live in facebook/ + tiktok/ packages (no double fetch)
        LegacyFetchCollector(
            source="GDELT",
            fetch_fn=fetch_gdelt_items,
            source_method=SourceMethod.PUBLIC_FEED,
            provider="gdelt",
            platform="gdelt",
        ),
        LegacyFetchCollector(
            source="Curated public pages",
            fetch_fn=fetch_public_page_items,
            source_method=SourceMethod.PUBLIC_FEED,
            provider="public_page",
            platform="public_page",
        ),
    ]


def build_all_collectors() -> list[BaseCollector]:
    """Full registry: legacy + new adapters (discovery, IG/FB/TT stubs, Trends official)."""
    collectors = build_legacy_collectors()

    from app.collectors.facebook.authorized_pages import FacebookAuthorizedPagesCollector
    from app.collectors.facebook.public_pages import FacebookPublicPagesCollector
    from app.collectors.google_trends.official import GoogleTrendsOfficialCollector
    from app.collectors.instagram.authorized import InstagramAuthorizedCollector
    from app.collectors.instagram.business_discovery import InstagramBusinessDiscoveryCollector
    from app.collectors.instagram.hashtag import InstagramHashtagCollector
    from app.collectors.search.social_discovery import SocialSearchDiscoveryCollector
    from app.collectors.tiktok.authorized import TikTokAuthorizedCollector
    from app.collectors.tiktok.discovery import TikTokDiscoveryCollector

    # Prefer new TikTok authorized over thin legacy when both present — skip duplicate
    # by source name uniqueness: new adapters are distinct sources.
    collectors.extend(
        [
            SocialSearchDiscoveryCollector(),
            InstagramAuthorizedCollector(),
            InstagramHashtagCollector(),
            InstagramBusinessDiscoveryCollector(),
            FacebookAuthorizedPagesCollector(),
            FacebookPublicPagesCollector(),
            TikTokAuthorizedCollector(),
            TikTokDiscoveryCollector(),
            GoogleTrendsOfficialCollector(),
        ]
    )
    return collectors
