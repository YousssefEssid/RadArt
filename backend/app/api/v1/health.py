from __future__ import annotations

from fastapi import APIRouter

from app.core.database import get_connection

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        db = "connected"
    except Exception:
        db = "error"
    return {"status": "ok", "db": db, "scheduler": "running"}
