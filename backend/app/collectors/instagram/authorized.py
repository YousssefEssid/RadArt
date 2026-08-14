from __future__ import annotations

from app.collectors.awaiting import AwaitingCredentialsCollector
from app.collectors.base import SourceMethod
from app.core.config import settings


class InstagramAuthorizedCollector(AwaitingCredentialsCollector):
    source = "Instagram Authorized"
    source_method = SourceMethod.AUTHORIZED_ACCOUNT
    provider = "meta"
    platform = "instagram"
    credential_env = "META_PAGE_ACCESS_TOKEN (Instagram professional)"
    detail = "WAITING_FOR_CREDENTIALS — connect IG professional + Graph permissions"

    def credentials_ready(self) -> bool:
        # Same Meta token path; IG authorized content needs dedicated scopes later
        return bool((settings.meta_page_access_token or "").strip()) and bool(
            (getattr(settings, "instagram_business_account_id", "") or "").strip()
        )
