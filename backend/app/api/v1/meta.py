from __future__ import annotations

from typing import Any

from fastapi import APIRouter

from app.core.database import get_connection
from app.repositories import meta as meta_repo

router = APIRouter(prefix="/meta", tags=["meta"])


@router.get("/filters")
def meta_filters() -> dict[str, Any]:
    with get_connection() as conn:
        return meta_repo.get_filter_options(conn)
