from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.database import get_connection
from app.services.trend_confirmation_service import confirm_topic
from app.services.trend_service import get_trends_for_api

router = APIRouter(tags=["trends"])


@router.get("/trends")
def trends(
    category: str | None = Query(None, description="Comma-separated categories"),
    q: str | None = Query(None, description="Search label, summary, keywords"),
    min_trend_score: float | None = Query(None, ge=0, le=100),
    max_risk: float | None = Query(None, ge=0, le=100),
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        return get_trends_for_api(
            conn,
            category=category,
            q=q,
            min_trend_score=min_trend_score,
            max_risk=max_risk,
        )


@router.get("/trends/confirm")
def trends_confirm(
    topic: str = Query(..., min_length=2),
    hours: int = Query(48, ge=6, le=168),
) -> dict[str, Any]:
    """Cross-source confirmation for a candidate topic (defensible confidence)."""
    with get_connection() as conn:
        try:
            return confirm_topic(conn, topic, hours=hours)
        except ValueError as e:
            raise HTTPException(422, str(e)) from e
