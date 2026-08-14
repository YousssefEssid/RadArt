from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.collectors.customer_owned_collector import save_customer_owned_payload
from app.core.database import get_connection
from app.services.data_coverage_service import build_signal_coverage
from app.services.source_health_service import build_source_health

router = APIRouter(prefix="/sources", tags=["sources"])


class CustomerOwnedIn(BaseModel):
    items: list[dict[str, Any]] = Field(default_factory=list)
    filename: str = "upload.json"


@router.get("/coverage")
def signal_coverage() -> dict[str, Any]:
    """Honest Tunisia signal coverage map — live vs keys vs licensed roadmap vs forbidden."""
    return build_signal_coverage()


@router.get("/health")
def sources_health() -> dict[str, Any]:
    """Per-collector health + compact REAL vs PARTIAL coverage matrix."""
    with get_connection() as conn:
        return build_source_health(conn)


@router.post("/customer-owned")
def ingest_customer_owned(body: CustomerOwnedIn) -> dict[str, Any]:
    """Store customer-owned social/campaign exports for the next collection cycle."""
    if not body.items:
        raise HTTPException(422, "items required")
    try:
        n = save_customer_owned_payload(body.items, body.filename)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    return {
        "saved": n,
        "message": "Stored for next collection. Run POST /api/collect/run to ingest.",
        "path": "backend/data/customer_owned/",
    }


@router.post("/customer-owned/upload")
async def upload_customer_owned_file(file: UploadFile = File(...)) -> dict[str, Any]:
    raw = await file.read()
    if len(raw) > 8 * 1024 * 1024:
        raise HTTPException(413, "Max 8 Mo")
    try:
        import json

        payload = json.loads(raw.decode("utf-8"))
    except Exception as e:
        raise HTTPException(422, f"JSON invalide: {e}") from e
    rows = payload if isinstance(payload, list) else payload.get("items") or payload.get("posts") or []
    if not isinstance(rows, list) or not rows:
        raise HTTPException(422, "Attendu: liste d'items ou {items:[...]}")
    n = save_customer_owned_payload(rows, file.filename or "upload.json")
    return {"saved": n, "filename": file.filename, "message": "OK — lancez une collecte pour ingérer."}
