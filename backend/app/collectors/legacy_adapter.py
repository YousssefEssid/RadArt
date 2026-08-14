"""Wrap legacy sync fetch_* collectors into BaseCollector without removing them."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Callable
from typing import Any

from app.collectors.base import (
    BaseCollector,
    CollectedItem,
    CollectionContext,
    CollectorHealth,
    SourceMethod,
    confidence_for,
)
from app.utils.time_utils import utc_now_iso

FetchFn = Callable[[], tuple[list[dict[str, Any]], list[dict[str, str]]]]


def legacy_dict_to_collected(
    raw: dict[str, Any],
    *,
    source_method: str,
    provider: str,
    source_type: str | None = None,
    default_platform: str | None = None,
) -> CollectedItem | None:
    title = str(raw.get("title") or "").strip()
    if not title:
        return None
    platform = str(raw.get("platform") or default_platform or "unknown")
    method = str(raw.get("source_method") or source_method)
    conf = raw.get("confidence")
    if conf is None:
        conf = confidence_for(method)

    hashtags = raw.get("hashtags") or []
    mentions = raw.get("mentions") or []
    keywords = raw.get("keywords") or []
    if isinstance(keywords, str):
        try:
            keywords = json.loads(keywords)
        except Exception:
            keywords = [keywords]

    meta = raw.get("raw_metadata_json") or raw.get("raw_json") or {}
    if isinstance(meta, str):
        try:
            meta = json.loads(meta)
        except Exception:
            meta = {"raw": meta}

    return CollectedItem(
        platform=platform,
        source_type=str(raw.get("source_type") or source_type or platform),
        source_method=method,
        provider=str(raw.get("provider") or provider),
        title=title,
        text=str(raw.get("text") or ""),
        url=raw.get("url"),
        external_id=raw.get("external_id"),
        author_name=raw.get("author_name") or raw.get("author"),
        author_external_id=raw.get("author_external_id"),
        published_at=raw.get("published_at"),
        collected_at=raw.get("collected_at") or utc_now_iso(),
        views=raw.get("views"),
        likes=raw.get("likes"),
        comments=raw.get("comments"),
        shares=raw.get("shares"),
        hashtags=list(hashtags) if isinstance(hashtags, list) else [],
        mentions=list(mentions) if isinstance(mentions, list) else [],
        keywords=list(keywords) if isinstance(keywords, list) else [],
        language=raw.get("language"),
        country=raw.get("country") or "TN",
        confidence=float(conf),
        category=raw.get("category"),
        source=str(raw.get("source") or provider),
        raw_metadata_json=meta if isinstance(meta, dict) else {"value": meta},
    )


class LegacyFetchCollector(BaseCollector):
    """Adapter: keep existing fetch_* functions, expose BaseCollector contract."""

    def __init__(
        self,
        *,
        source: str,
        fetch_fn: FetchFn,
        source_method: SourceMethod,
        provider: str,
        platform: str,
        credential_check: Callable[[], tuple[bool, str]] | None = None,
        enabled: bool = True,
    ) -> None:
        self.source = source
        self._fetch_fn = fetch_fn
        self.source_method = source_method
        self.provider = provider
        self._platform = platform
        self._credential_check = credential_check
        self.enabled = enabled
        self._last_error: str | None = None
        self._last_ok = False

    async def collect(self, context: CollectionContext) -> list[CollectedItem]:
        if not self.enabled:
            return []
        items, status = await asyncio.to_thread(self._fetch_fn)
        out: list[CollectedItem] = []
        for raw in items:
            c = legacy_dict_to_collected(
                raw,
                source_method=self.source_method.value,
                provider=self.provider,
                source_type=self._platform,
                default_platform=self._platform,
            )
            if c:
                out.append(c)
        errors = [s for s in status if s.get("status") == "error"]
        skipped = [s for s in status if s.get("status") == "skipped"]
        if errors:
            self._last_error = errors[0].get("detail")
            self._last_ok = False
        elif skipped and not items:
            self._last_error = skipped[0].get("detail")
            self._last_ok = False
        else:
            self._last_error = None
            self._last_ok = True
        return out

    async def healthcheck(self) -> CollectorHealth:
        cred_ok, cred_detail = True, "ok"
        if self._credential_check:
            cred_ok, cred_detail = self._credential_check()
        if not self.enabled:
            status = "disabled"
        elif not cred_ok:
            status = "awaiting_credentials"
        elif self._last_error:
            status = "error"
        elif self._last_ok:
            status = "connected"
        else:
            status = "connected" if cred_ok else "awaiting_credentials"
        return CollectorHealth(
            source=self.source,
            enabled=self.enabled,
            credential_status=status,
            source_method=self.source_method.value,
            provider=self.provider,
            last_error=self._last_error or (None if cred_ok else cred_detail),
            detail=cred_detail,
        )
