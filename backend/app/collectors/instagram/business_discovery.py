from __future__ import annotations

from app.collectors.awaiting import AwaitingCredentialsCollector
from app.collectors.base import SourceMethod
from app.core.config import settings


class InstagramBusinessDiscoveryCollector(AwaitingCredentialsCollector):
    """Business Discovery — metadata/metrics on other IG professional accounts."""

    source = "Instagram Business Discovery"
    source_method = SourceMethod.OFFICIAL_PUBLIC_API
    provider = "meta"
    platform = "instagram"
    credential_env = "META_PAGE_ACCESS_TOKEN + business_discovery"
    detail = "WAITING_FOR_CREDENTIALS — Business Discovery requires Meta App Review"

    def credentials_ready(self) -> bool:
        return bool((getattr(settings, "meta_ig_business_discovery_enabled", False))) and bool(
            (settings.meta_page_access_token or "").strip()
        )
