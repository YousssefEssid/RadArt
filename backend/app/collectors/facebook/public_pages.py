from __future__ import annotations

from app.collectors.awaiting import AwaitingCredentialsCollector
from app.collectors.base import SourceMethod
from app.core.config import settings


class FacebookPublicPagesCollector(AwaitingCredentialsCollector):
    """Page Public Content Access — subject to Meta permissions/review."""

    source = "Facebook Public Page Content"
    source_method = SourceMethod.OFFICIAL_PUBLIC_API
    provider = "meta"
    platform = "facebook"
    credential_env = "META_PAGE_PUBLIC_CONTENT_ACCESS"
    detail = "WAITING_FOR_CREDENTIALS — Page Public Content Access requires Meta review"

    def credentials_ready(self) -> bool:
        return bool(getattr(settings, "meta_page_public_content_enabled", False)) and bool(
            (settings.meta_page_access_token or "").strip()
        )
