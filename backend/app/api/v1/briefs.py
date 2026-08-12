from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.core.database import get_connection
from app.repositories import brief as brief_repo
from app.schemas.brief import BriefAnalyzeIn, BriefAnalyzeOut, ParsedBriefOut
from app.services.brief_file_extract import extract_text_from_filename_and_bytes
from app.services.brief_service import analyze_and_store
from app.services.recommendation_service import generate_recommendations_for_brief, list_recommendations

router = APIRouter(prefix="/briefs", tags=["briefs"])


@router.post("/extract-text")
async def extract_brief_text(file: UploadFile = File(...)) -> dict[str, str]:
    raw = await file.read()
    if len(raw) > 12 * 1024 * 1024:
        raise HTTPException(413, "Fichier trop volumineux (max 12 Mo).")
    if not raw:
        raise HTTPException(422, "Fichier vide.")
    try:
        text = extract_text_from_filename_and_bytes(file.filename or "brief", raw)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    return {"text": text, "filename": file.filename or ""}


@router.post("/analyze", response_model=BriefAnalyzeOut)
def analyze_brief(body: BriefAnalyzeIn) -> BriefAnalyzeOut:
    bid, parsed = analyze_and_store(body.client_name, body.raw_brief)
    recs = generate_recommendations_for_brief(bid)
    pb = ParsedBriefOut(
        sector=parsed.get("sector"),
        target=parsed.get("target"),
        objective=parsed.get("objective"),
        tone=parsed.get("tone"),
        constraints=parsed.get("constraints"),
        competitors=list(parsed.get("competitors") or []),
    )
    return BriefAnalyzeOut(brief_id=bid, parsed_brief=pb, recommendations=recs)


@router.get("/latest")
def brief_latest() -> dict[str, Any]:
    with get_connection() as conn:
        return brief_repo.get_latest_brief(conn)


@router.get("/{brief_id}/recommendations")
def recommendations(brief_id: int) -> list[dict[str, Any]]:
    rows = list_recommendations(brief_id)
    if not rows:
        with get_connection() as conn:
            if not brief_repo.brief_exists(conn, brief_id):
                raise HTTPException(404, "brief not found")
    return rows
