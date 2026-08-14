"""Awaiting-credentials collectors — real official endpoints only when keys exist."""

from __future__ import annotations

from app.collectors.base import (
    BaseCollector,
    CollectedItem,
    CollectionContext,
    CollectorHealth,
    SourceMethod,
)


class AwaitingCredentialsCollector(BaseCollector):
    """Official adapter shell: never pretends success without credentials."""

    source: str = "awaiting"
    source_method: SourceMethod = SourceMethod.AUTHORIZED_ACCOUNT
    provider: str = "meta"
    platform: str = "instagram"
    credential_env: str = ""
    detail: str = "WAITING_FOR_CREDENTIALS"

    def credentials_ready(self) -> bool:
        return False

    async def collect(self, context: CollectionContext) -> list[CollectedItem]:
        return []

    async def healthcheck(self) -> CollectorHealth:
        ready = self.credentials_ready()
        return CollectorHealth(
            source=self.source,
            enabled=self.enabled,
            credential_status="connected" if ready else "awaiting_credentials",
            source_method=self.source_method.value,
            provider=self.provider,
            detail=None if ready else self.detail,
            last_error=None if ready else self.credential_env or self.detail,
        )
