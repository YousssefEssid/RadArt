from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.core.database import get_connection
from app.repositories import brand as brand_repo
from app.repositories.brief import get_latest_brief
from app.services.jump_decision_service import analyze_jump, generate_campaign
from app.services.opportunity_card_service import build_opportunity_card, get_full_brief, list_opportunity_cards
from app.services.trend_service import get_trends_for_api

router = APIRouter(tags=["opportunities"])


@router.get("/opportunities")
def opportunities(
    limit: int = Query(12, ge=1, le=30),
    enrich: bool = Query(False, description="Use LLM when keys exist (slower)"),
) -> dict[str, Any]:
    with get_connection() as conn:
        return list_opportunity_cards(conn, limit=limit, use_llm=enrich)


@router.get("/opportunities/{cluster_id}")
def opportunity_detail(
    cluster_id: int,
    enrich: bool = Query(True, description="Prefer richer copy when LLM keys exist"),
) -> dict[str, Any]:
    with get_connection() as conn:
        trends = get_trends_for_api(conn)
        trend = next((t for t in trends if int(t["id"]) == cluster_id), None)
        if not trend:
            raise HTTPException(status_code=404, detail="trend_not_found")
        latest = get_latest_brief(conn)
        brief = get_full_brief(conn, latest.get("id"))
        brand = brand_repo.get_active_brand(conn)
        return build_opportunity_card(conn, trend, brief, use_llm=enrich, brand=brand)


@router.post("/opportunities/{cluster_id}/jump")
def jump_analysis(cluster_id: int) -> dict[str, Any]:
    """Should we jump on this? — Trend × Brand decision."""
    with get_connection() as conn:
        result = analyze_jump(conn, cluster_id)
        if result.get("error") == "trend_not_found":
            raise HTTPException(status_code=404, detail="trend_not_found")
        return result


@router.post("/opportunities/{cluster_id}/campaign")
def campaign_pack(cluster_id: int) -> dict[str, Any]:
    """Generate Campaign — listening → execution pack."""
    with get_connection() as conn:
        result = generate_campaign(conn, cluster_id)
        if result.get("error") == "trend_not_found":
            raise HTTPException(status_code=404, detail="trend_not_found")
        return result
