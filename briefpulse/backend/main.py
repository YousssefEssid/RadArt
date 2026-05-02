from __future__ import annotations

import json
import threading
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from db import fetch_all, fetch_one, get_connection, init_db
from models.schemas import BriefAnalyzeIn, BriefAnalyzeOut, ParsedBriefOut
from scheduler import collect_and_process, get_last_collection_meta, shutdown_scheduler, start_scheduler
from services.brief_service import analyze_and_store
from services.recommendation_service import generate_recommendations_for_brief, list_recommendations
from services.trend_service import get_trends_for_api


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    start_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(title="RADJ API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict[str, str]:
    try:
        with get_connection() as conn:
            conn.execute("SELECT 1")
        db = "connected"
    except Exception:
        db = "error"
    sched = "running"
    return {"status": "ok", "db": db, "scheduler": sched}


@app.post("/api/collect/run")
def collect_run() -> dict[str, str]:
    threading.Thread(target=collect_and_process, daemon=True).start()
    return {"message": "collection started"}


@app.get("/api/collect/status")
def collect_status() -> dict[str, Any]:
    meta = get_last_collection_meta()
    with get_connection() as conn:
        runs = fetch_all(
            conn,
            "SELECT * FROM collection_runs ORDER BY id DESC LIMIT 10",
        )
        n_media = conn.execute("SELECT COUNT(*) FROM media_items").fetchone()[0]
        n_trends = conn.execute("SELECT COUNT(*) FROM trend_clusters").fetchone()[0]
    return {
        "last_runs": runs,
        "media_items_count": int(n_media),
        "trend_clusters_count": int(n_trends),
        "source_status": meta.get("source_status", []),
        "last_summary": meta.get("summary", {}),
    }


@app.get("/api/meta/filters")
def meta_filters() -> dict[str, Any]:
    """Distinct categories and platforms in the DB for UI filters (varied agency clients)."""
    with get_connection() as conn:
        cats_m = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT category FROM media_items WHERE category IS NOT NULL AND trim(category) != '' ORDER BY category COLLATE NOCASE"
            ).fetchall()
        ]
        cats_t = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT category FROM trend_clusters WHERE category IS NOT NULL AND trim(category) != '' ORDER BY category COLLATE NOCASE"
            ).fetchall()
        ]
        plats = [
            r[0]
            for r in conn.execute(
                "SELECT DISTINCT platform FROM media_items WHERE platform IS NOT NULL ORDER BY platform COLLATE NOCASE"
            ).fetchall()
        ]
    cats = sorted(set(cats_m + cats_t), key=str.lower)
    return {"categories": cats, "platforms": plats}


@app.get("/api/media-items")
def media_items(
    limit: int = 50,
    category: str | None = None,
    platform: str | None = None,
    q: str | None = None,
) -> list[dict[str, Any]]:
    lim = max(1, min(200, limit))
    conditions: list[str] = []
    params: list[Any] = []
    if category and category.strip():
        cats = [c.strip().lower() for c in category.split(",") if c.strip()]
        if cats:
            placeholders = ",".join("?" * len(cats))
            conditions.append(f"lower(category) IN ({placeholders})")
            params.extend(cats)
    if platform and platform.strip():
        plats = [p.strip().lower() for p in platform.split(",") if p.strip()]
        if plats:
            placeholders = ",".join("?" * len(plats))
            conditions.append(f"lower(platform) IN ({placeholders})")
            params.extend(plats)
    if q and q.strip():
        like = f"%{q.strip()}%"
        conditions.append("(title LIKE ? OR text LIKE ?)")
        params.extend([like, like])
    where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
    sql = f"""SELECT id, source, platform, title, text, url, published_at, collected_at,
              engagement, category, cluster_id, entities FROM media_items{where}
              ORDER BY id DESC LIMIT ?"""
    params.append(lim)
    with get_connection() as conn:
        rows = fetch_all(conn, sql, tuple(params))
    return rows


@app.get("/api/trends")
def trends(
    category: str | None = Query(None, description="Comma-separated categories (e.g. sport,youth)"),
    q: str | None = Query(None, description="Search label, summary, keywords"),
    min_trend_score: float | None = Query(None, ge=0, le=100),
    max_risk: float | None = Query(None, ge=0, le=100),
) -> list[dict[str, Any]]:
    with get_connection() as conn:
        return get_trends_for_api(
            conn,
            category=category,
            q=q,
            min_trend_score=min_trend_score,
            max_risk=max_risk,
        )


@app.post("/api/briefs/extract-text")
async def extract_brief_text(file: UploadFile = File(...)) -> dict[str, str]:
    """Extrait le texte d’un brief importé (.pptx, .docx, .pdf, .txt) pour remplir le formulaire."""
    from services.brief_file_extract import extract_text_from_filename_and_bytes

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


@app.post("/api/briefs/analyze", response_model=BriefAnalyzeOut)
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


@app.get("/api/briefs/latest")
def brief_latest() -> dict[str, Any]:
    with get_connection() as conn:
        row = fetch_one(
            conn,
            """SELECT id, client_name, sector, target, competitors_json, created_at
               FROM client_briefs ORDER BY id DESC LIMIT 1""",
        )
    if not row:
        return {}
    comps: list[str] = []
    raw = row.get("competitors_json")
    if raw:
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, list):
                comps = [str(x) for x in loaded if str(x).strip()]
        except json.JSONDecodeError:
            comps = []
    return {
        "id": row["id"],
        "client_name": row.get("client_name"),
        "sector": row.get("sector"),
        "target": row.get("target"),
        "competitors": comps,
        "created_at": row.get("created_at"),
    }


@app.get("/api/competitors/demo")
def competitors_demo() -> dict[str, Any]:
    """Rapport illustratif (Tunisie Telecom vs Orange / Ooredoo) — sans base ni brief."""
    from services.competitor_demo_static import tunisia_telecom_demo_report

    return tunisia_telecom_demo_report()


@app.get("/api/competitors/report")
def competitors_report(
    brief_id: int | None = Query(None, description="Identifiant du brief ; sinon le dernier brief analysé"),
) -> dict[str, Any]:
    from services.competitor_intel_service import build_competitor_report, latest_brief_row

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


@app.get("/api/briefs/{brief_id}/recommendations")
def recommendations(brief_id: int) -> list[dict[str, Any]]:
    rows = list_recommendations(brief_id)
    if not rows:
        with get_connection() as conn:
            b = conn.execute("SELECT id FROM client_briefs WHERE id = ?", (brief_id,)).fetchone()
        if not b:
            raise HTTPException(404, "brief not found")
    return rows
