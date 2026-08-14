from __future__ import annotations

from app.collectors.awaiting import AwaitingCredentialsCollector
from app.collectors.base import SourceMethod
from app.core.config import settings


class InstagramHashtagCollector(AwaitingCredentialsCollector):
    """Meta Hashtag Search — requires App Review / advanced access."""

    source = "Instagram Hashtag Search"
    source_method = SourceMethod.OFFICIAL_PUBLIC_API
    provider = "meta"
    platform = "instagram"
    credential_env = "META_PAGE_ACCESS_TOKEN + IG hashtag permissions"
    detail = "WAITING_FOR_CREDENTIALS — Meta Hashtag Search needs reviewed permissions"

    def credentials_ready(self) -> bool:
        return bool((getattr(settings, "meta_ig_hashtag_enabled", False))) and bool(
            (settings.meta_page_access_token or "").strip()
        )
