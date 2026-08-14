from __future__ import annotations

import asyncio

from app.collectors.base import (
    BaseCollector,
    CollectedItem,
    CollectionContext,
    CollectorHealth,
    SourceMethod,
)
from app.collectors.legacy_adapter import legacy_dict_to_collected
from app.core.config import settings


class FacebookAuthorizedPagesCollector(BaseCollector):
    """Official Graph API for pages the workspace manages/authorizes."""

    source = "Facebook Authorized Pages"
    source_method = SourceMethod.AUTHORIZED_ACCOUNT
    provider = "meta"
    enabled = True

    def credentials_ready(self) -> bool:
        return bool((settings.meta_page_access_token or "").strip()) and bool(
            (settings.meta_page_ids or "").strip()
        )

    async def collect(self, context: CollectionContext) -> list[CollectedItem]:
        if not self.credentials_ready():
            return []
        from app.collectors.meta_graph_collector import fetch_meta_graph_items

        items, _ = await asyncio.to_thread(fetch_meta_graph_items)
        out: list[CollectedItem] = []
        for raw in items:
            c = legacy_dict_to_collected(
                raw,
                source_method=self.source_method.value,
                provider=self.provider,
                source_type="facebook",
                default_platform="facebook",
            )
            if c:
                out.append(c)
        return out

    async def healthcheck(self) -> CollectorHealth:
        ready = self.credentials_ready()
        return CollectorHealth(
            source=self.source,
            enabled=self.enabled,
            credential_status="connected" if ready else "awaiting_credentials",
            source_method=self.source_method.value,
            provider=self.provider,
            detail=None if ready else "META_PAGE_ACCESS_TOKEN + META_PAGE_IDS",
            last_error=None if ready else "WAITING_FOR_CREDENTIALS",
        )
