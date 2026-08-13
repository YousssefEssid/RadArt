from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.core.database import get_connection
from app.services.morning_radar_service import build_morning_radar

router = APIRouter(tags=["radar"])


@router.get("/radar/morning")
def morning_radar() -> dict[str, Any]:
    """Workflow « Morning Radar » : ce qui a changé, pourquoi ça compte, que faire."""
    with get_connection() as conn:
        return build_morning_radar(conn)
