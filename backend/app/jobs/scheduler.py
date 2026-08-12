from __future__ import annotations

import json
import sqlite3
import threading
import traceback
from typing import Any

from apscheduler.schedulers.background import BackgroundScheduler

from app.core.config import settings
from app.core.database import get_connection, init_db
from app.services.ingestion_service import run_ingestion
from app.services.trend_service import run_trend_detection
from app.utils.time_utils import utc_now_iso

_lock = threading.Lock()
_scheduler: BackgroundScheduler | None = None

_last_source_status: list[dict[str, str]] = []
_last_run_summary: dict[str, Any] = {}


def get_last_collection_meta() -> dict[str, Any]:
    return {"source_status": list(_last_source_status), "summary": dict(_last_run_summary)}


def collect_and_process() -> None:
    global _last_source_status, _last_run_summary
    if not _lock.acquire(blocking=False):
        return
    started = utc_now_iso()
    n = 0
    try:
        with get_connection() as conn:
            n, src = run_ingestion(conn)
            _last_source_status = src
            k = run_trend_detection(conn)
            _last_run_summary = {"items_inserted": n, "clusters": k}
            ended = utc_now_iso()
            conn.execute(
                """
                INSERT INTO collection_runs (started_at, ended_at, status, items_collected, errors)
                VALUES (?, ?, ?, ?, ?)
                """,
                (started, ended, "ok", n, json.dumps(src, ensure_ascii=False)[:4000]),
            )
    except Exception:
        err_msg = traceback.format_exc()[:4000]
        try:
            with get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO collection_runs (started_at, ended_at, status, items_collected, errors)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (started, utc_now_iso(), "error", n, err_msg),
                )
        except Exception:
            pass
    finally:
        _lock.release()


def start_scheduler() -> BackgroundScheduler:
    global _scheduler
    init_db()
    threading.Thread(target=collect_and_process, daemon=True).start()
    if _scheduler and _scheduler.running:
        return _scheduler
    sched = BackgroundScheduler()
    interval = max(1, int(settings.collection_interval_minutes or 15))
    sched.add_job(
        collect_and_process,
        "interval",
        minutes=interval,
        id="collect_and_process",
        replace_existing=True,
        max_instances=1,
    )
    sched.start()
    _scheduler = sched
    return sched


def shutdown_scheduler() -> None:
    global _scheduler
    if _scheduler:
        _scheduler.shutdown(wait=False)
        _scheduler = None
