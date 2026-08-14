"""TikTok discovery via search_discovery only — never scrapes tiktok.com pages."""

from __future__ import annotations

from app.collectors.awaiting import AwaitingCredentialsCollector
from app.collectors.base import SourceMethod


class TikTokDiscoveryCollector(AwaitingCredentialsCollector):
    """
    Placeholder for licensed / official discovery.
    Commercial SaaS must not depend on Research Tools or unofficial scrapers.
    Social search discovery (site:tiktok.com) is the MVP path — see search/social_discovery.py
    """

    source = "TikTok Discovery (licensed/official)"
    source_method = SourceMethod.LICENSED_PROVIDER
    provider = "tiktok"
    platform = "tiktok"
    credential_env = "licensed TikTok / partner firehose"
    detail = "WAITING_FOR_CREDENTIALS — use Search Discovery until licensed partner"

    def credentials_ready(self) -> bool:
        return False
