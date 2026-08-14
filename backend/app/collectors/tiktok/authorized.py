from __future__ import annotations

import json
from typing import Any

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


class TikTokAuthorizedCollector(BaseCollector):
    """
    TikTok Display API — authorized user's profile/videos only.
    Endpoints: /v2/user/info/, /v2/video/list/, /v2/video/query/
    Not a global For You Page. Research Tools are non-commercial — not used here.
    """

    source = "TikTok Display (authorized)"
    source_method = SourceMethod.AUTHORIZED_ACCOUNT
    provider = "tiktok"
    enabled = True

    def credentials_ready(self) -> bool:
        return bool((settings.tiktok_access_token or "").strip())

    async def collect(self, context: CollectionContext) -> list[CollectedItem]:
        token = (settings.tiktok_access_token or "").strip()
        if not token:
            return []
        # Thin official call — fail soft
        try:
            r = requests.post(
                "https://open.tiktokapis.com/v2/video/list/",
                headers={
                    **request_headers(),
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"max_count": min(20, context.max_items_per_source)},
                params={"fields": "id,title,create_time,share_url,video_description"},
                timeout=12,
            )
            if r.status_code >= 400:
                return []
            data = r.json()
            videos = ((data.get("data") or {}).get("videos") or [])[: context.max_items_per_source]
            out: list[CollectedItem] = []
            now = utc_now_iso()
            for v in videos:
                title = (v.get("title") or v.get("video_description") or "TikTok video").strip()
                out.append(
                    CollectedItem(
                        platform="tiktok",
                        source_type="tiktok",
                        source_method=self.source_method.value,
                        provider=self.provider,
                        title=title[:500],
                        text=str(v.get("video_description") or "")[:4000],
                        url=v.get("share_url"),
                        external_id=str(v.get("id")) if v.get("id") else None,
                        published_at=str(v.get("create_time")) if v.get("create_time") else None,
                        collected_at=now,
                        confidence=confidence_for(self.source_method),
                        source="TikTok authorized",
                        country=context.country,
                        raw_metadata_json={"video": v},
                    )
                )
            return out
        except Exception:
            return []

    async def healthcheck(self) -> CollectorHealth:
        ready = self.credentials_ready()
        return CollectorHealth(
            source=self.source,
            enabled=self.enabled,
            credential_status="connected" if ready else "awaiting_credentials",
            source_method=self.source_method.value,
            provider=self.provider,
            detail=None if ready else "WAITING_FOR_CREDENTIALS — TikTok Display API OAuth token",
            last_error=None if ready else "TIKTOK_ACCESS_TOKEN",
        )
