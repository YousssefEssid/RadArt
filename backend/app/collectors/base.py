"""Normalized collector contract — services never depend on Meta/TikTok SDKs."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class SourceMethod(str, Enum):
    OFFICIAL_API = "official_api"
    AUTHORIZED_ACCOUNT = "authorized_account"
    OFFICIAL_PUBLIC_API = "official_public_api"
    LICENSED_PROVIDER = "licensed_provider"
    SEARCH_DISCOVERY = "search_discovery"
    RSS = "rss"
    PUBLIC_FEED = "public_feed"
    MANUAL = "manual"
    MOCK = "mock"


SOURCE_CONFIDENCE: dict[str, float] = {
    SourceMethod.OFFICIAL_API.value: 1.00,
    SourceMethod.AUTHORIZED_ACCOUNT.value: 1.00,
    SourceMethod.OFFICIAL_PUBLIC_API.value: 0.95,
    SourceMethod.LICENSED_PROVIDER.value: 0.90,
    SourceMethod.RSS.value: 0.80,
    SourceMethod.PUBLIC_FEED.value: 0.75,
    SourceMethod.SEARCH_DISCOVERY.value: 0.55,
    SourceMethod.MANUAL.value: 0.70,
    SourceMethod.MOCK.value: 0.20,
}


def confidence_for(source_method: str | SourceMethod | None) -> float:
    if source_method is None:
        return 0.5
    key = source_method.value if isinstance(source_method, SourceMethod) else str(source_method)
    return float(SOURCE_CONFIDENCE.get(key, 0.5))


@dataclass
class CollectionContext:
    """Workspace-scoped collection inputs (watchlists, budgets, geo)."""

    workspace_id: int = 1
    brands: list[str] = field(default_factory=list)
    competitors: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    creators: list[str] = field(default_factory=list)
    country: str = "TN"
    language: str = "fr"
    max_items_per_source: int = 40
    seed_queries: list[str] = field(default_factory=list)
    extra: dict[str, Any] = field(default_factory=dict)

    def all_terms(self, *, include_hashtag_hash: bool = True) -> list[str]:
        terms: list[str] = []
        for bucket in (
            self.brands,
            self.competitors,
            self.topics,
            self.keywords,
            self.creators,
        ):
            terms.extend(t.strip() for t in bucket if t and str(t).strip())
        for h in self.hashtags:
            raw = str(h).strip()
            if not raw:
                continue
            if include_hashtag_hash and not raw.startswith("#"):
                terms.append(f"#{raw}")
            terms.append(raw.lstrip("#"))
        # stable unique, preserve order
        seen: set[str] = set()
        out: list[str] = []
        for t in terms:
            k = t.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(t)
        return out


@dataclass
class CollectorHealth:
    source: str
    enabled: bool
    credential_status: str  # connected | awaiting_credentials | disabled | error | partial
    source_method: str
    provider: str
    last_success_at: str | None = None
    last_failure_at: str | None = None
    last_error: str | None = None
    items_collected_24h: int = 0
    detail: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CollectedItem:
    """Universal MediaItem — every collector must emit this shape."""

    platform: str
    source_type: str
    source_method: str
    provider: str
    title: str
    text: str = ""
    url: str | None = None
    external_id: str | None = None
    author_name: str | None = None
    author_external_id: str | None = None
    published_at: str | None = None
    collected_at: str | None = None
    views: int | None = None
    likes: int | None = None
    comments: int | None = None
    shares: int | None = None
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)
    keywords: list[str] = field(default_factory=list)
    language: str | None = None
    country: str | None = None
    confidence: float = 0.5
    category: str | None = None
    source: str | None = None  # human-readable feed/channel name
    raw_metadata_json: dict[str, Any] = field(default_factory=dict)

    def engagement_total(self) -> int:
        parts = [self.views, self.likes, self.comments, self.shares]
        vals = [int(v) for v in parts if v is not None]
        if vals:
            # Prefer likes+comments+shares; views alone is not engagement
            social = sum(int(v or 0) for v in (self.likes, self.comments, self.shares))
            return social if social else int(self.views or 0)
        return 0

    def to_ingest_dict(self) -> dict[str, Any]:
        """Dict compatible with ingestion + extended media_items columns."""
        conf = self.confidence if self.confidence is not None else confidence_for(self.source_method)
        return {
            "platform": self.platform,
            "source_type": self.source_type,
            "source_method": self.source_method,
            "provider": self.provider,
            "source": self.source or self.provider or self.platform,
            "title": self.title,
            "text": self.text or "",
            "url": self.url,
            "external_id": self.external_id,
            "author_name": self.author_name,
            "author_external_id": self.author_external_id,
            "author": self.author_name,
            "published_at": self.published_at,
            "collected_at": self.collected_at,
            "views": self.views,
            "likes": self.likes,
            "comments": self.comments,
            "shares": self.shares,
            "engagement": self.engagement_total(),
            "hashtags": self.hashtags,
            "mentions": self.mentions,
            "keywords": self.keywords,
            "language": self.language,
            "country": self.country or "TN",
            "confidence": conf,
            "category": self.category,
            "raw_json": self.raw_metadata_json,
            "raw_metadata_json": self.raw_metadata_json,
        }


class BaseCollector(ABC):
    source: str
    source_method: SourceMethod = SourceMethod.PUBLIC_FEED
    provider: str = "unknown"
    enabled: bool = True

    @abstractmethod
    async def collect(self, context: CollectionContext) -> list[CollectedItem]:
        ...

    @abstractmethod
    async def healthcheck(self) -> CollectorHealth:
        ...

    def default_confidence(self) -> float:
        return confidence_for(self.source_method)
