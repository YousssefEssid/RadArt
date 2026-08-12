from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.database import get_connection
from app.services.competitor_demo_static import tunisia_telecom_study_report
from app.services.competitor_intel_service import build_competitor_report, latest_brief_row

router = APIRouter(prefix="/competitors", tags=["competitors"])


@router.get("/telecom-study")
def competitors_telecom_study() -> dict[str, Any]:
    return tunisia_telecom_study_report()


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
