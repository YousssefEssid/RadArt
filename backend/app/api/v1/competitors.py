from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.database import get_connection
from app.services.competitor_intel_service import build_competitor_report, latest_brief_row
from app.services.competitive_alerts_service import build_competitive_alerts
from app.services.war_room_service import build_war_room

router = APIRouter(prefix="/competitors", tags=["competitors"])


@router.get("/war-room")
def competitor_war_room() -> dict[str, Any]:
    """Competitor War Room — theme ownership + opportunity gaps."""
    with get_connection() as conn:
        return build_war_room(conn)


@router.get("/alerts")
def competitive_alerts() -> dict[str, Any]:
    """Competitor movement alerts — what moved, how fast, how to respond differently."""
    with get_connection() as conn:
        return build_competitive_alerts(conn)


@router.get("/report")
def competitors_report(
    brief_id: int | None = Query(None, description="Brief id; defaults to latest"),
) -> dict[str, Any]:
    with get_connection() as conn:
        bid = brief_id
        if bid is None:
            lb = latest_brief_row(conn)
            if not lb:
                raise HTTPException(
                    404,
                    "Aucun brief enregistré. Analysez un brief dans l’onglet Brief client.",
                )
            bid = int(lb["id"])
        try:
            return build_competitor_report(conn, int(bid))
        except ValueError:
            raise HTTPException(404, "Brief introuvable") from None
