from __future__ import annotations

import threading
from typing import Any

from fastapi import APIRouter

from app.core.database import get_connection
from app.jobs.scheduler import collect_and_process, get_last_collection_meta
from app.repositories import collection as collection_repo
from app.repositories import media as media_repo

router = APIRouter(prefix="/collect", tags=["collect"])


@router.post("/run")
def collect_run() -> dict[str, str]:
    threading.Thread(target=collect_and_process, daemon=True).start()
    return {"message": "collection started"}


@router.get("/status")
def collect_status() -> dict[str, Any]:
    meta = get_last_collection_meta()
    with get_connection() as conn:
        runs = collection_repo.list_recent_runs(conn)
        n_media = media_repo.count_media_items(conn)
        n_trends = collection_repo.count_trend_clusters(conn)
    return {
        "last_runs": runs,
        "media_items_count": n_media,
        "trend_clusters_count": n_trends,
        "source_status": meta.get("source_status", []),
        "last_summary": meta.get("summary", {}),
    }
