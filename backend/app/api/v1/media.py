from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.core.database import get_connection
from app.repositories import media as media_repo

router = APIRouter(tags=["media"])


@router.get("/media-items")
def media_items(
    limit: int = 80,
    category: str | None = None,
    platform: str | None = None,
    q: str | None = None,
    min_engagement: int | None = Query(None, ge=0),
    per_platform: int | None = Query(6, ge=1, le=30, description="Top N signals per platform"),
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        return media_repo.list_media_items(
            conn,
            limit=limit,
            category=category,
            platform=platform,
            q=q,
            min_engagement=min_engagement,
            per_platform=per_platform,
        )
