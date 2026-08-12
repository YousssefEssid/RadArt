from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Query

from app.core.database import get_connection
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
