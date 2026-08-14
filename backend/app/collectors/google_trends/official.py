from __future__ import annotations

from app.collectors.awaiting import AwaitingCredentialsCollector
from app.collectors.base import SourceMethod
from app.core.config import settings


class GoogleTrendsOfficialCollector(AwaitingCredentialsCollector):
    """Google's official Trends API (alpha / limited testers). SerpApi remains the live path."""

    source = "Google Trends (Official API)"
    source_method = SourceMethod.OFFICIAL_API
    provider = "google_trends_official"
    platform = "google_trends"
    credential_env = "GOOGLE_TRENDS_API_KEY"
    detail = "WAITING_FOR_CREDENTIALS — official Trends API is alpha / invite-only"

    def credentials_ready(self) -> bool:
        return bool((getattr(settings, "google_trends_api_key", "") or "").strip())
