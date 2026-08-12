from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.core.database import get_connection
from app.repositories import media as media_repo

router = APIRouter(tags=["media"])


@router.get("/media-items")
def media_items(
    limit: int = 50,
    category: str | None = None,
    platform: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        return media_repo.list_media_items(
            conn,
            limit=limit,
            category=category,
            platform=platform,
            q=q,
        )
