from __future__ import annotations

import json
import sqlite3
from typing import Any

from app.core.database import get_connection


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}
from app.services.llm_service import generate_json
from app.services.scoring_service import urgency_from_trend_score
from app.services.text_service import CATEGORY_KEYWORDS
from app.utils.time_utils import utc_now_iso

SECTOR_TREND_FIT: dict[str, list[str]] = {
    "food/beverage": ["weather", "youth", "economy", "culture", "sport", "lifestyle", "retail", "general"],
    "telecom": ["youth", "sport", "culture", "weather", "economy", "general"],
    "banking/finance": ["economy", "youth", "retail", "culture", "general"],
    "beauty/skincare": ["weather", "lifestyle", "culture", "youth", "general"],
    "retail": ["retail", "economy", "youth", "culture", "general"],
    "tourism": ["culture", "weather", "sport", "economy", "general"],
    "general": list(CATEGORY_KEYWORDS.keys()) + ["general", "lifestyle", "news"],
}


def _overlap_score(brief_text: str, trend_text: str) -> float:
    bw = set(brief_text.lower().split())
    tw = set(trend_text.lower().split())
    if not bw or not tw:
        return 30.0
    inter = len(bw & tw)
    return min(100.0, 20.0 + inter * 12.0)


def _sector_relevance(sector: str, trend_cat: str, trend_kws: list[str]) -> float:
    sector = (sector or "general").lower()
    trend_cat = (trend_cat or "").lower()
    allowed = [x.lower() for x in SECTOR_TREND_FIT.get(sector, SECTOR_TREND_FIT["general"])]
    if trend_cat in allowed:
        base = 85.0
    elif any(k.lower() in allowed for k in trend_kws):
        base = 70.0
    else:
        base = 45.0
    return base


def _target_relevance(target: str, trend_label: str, trend_summary: str) -> float:
    t = (target or "").lower()
    blob = f"{trend_label} {trend_summary}".lower()
    if "student" in t or "gen z" in t:
        if any(x in blob for x in ("étudiant", "student", "exam", "bac", "jeune", "youth")):
            return 90.0
        return 55.0
    return 60.0 + min(40.0, _overlap_score(target, trend_label) * 0.4)


def _timing_relevance(trend_score: float) -> float:
    return min(100.0, trend_score)


def _tone_compat(tone: str, risk: float, trend_cat: str) -> float:
    tone = (tone or "").lower()
    if "humor" in tone or "humour" in tone:
        if trend_cat in ("youth", "culture", "sport", "lifestyle", "weather"):
            return 88.0
        return 60.0
    if risk > 70:
        return 35.0
    return 65.0


def _politics_in_trend(blob: str) -> bool:
    return any(k in blob.lower() for k in CATEGORY_KEYWORDS["politics"])


def _health_sensitive(blob: str) -> bool:
    return any(
        k in blob.lower()
        for k in ("santé", "health", "médical", "maladie", "hôpital", "clinical", "cure")
    )


def brand_fit(
    brief: dict[str, Any],
    trend: dict[str, Any],
    trend_score: float,
    risk: float,
) -> float:
    raw = brief.get("raw_brief") or ""
    sector = brief.get("sector") or ""
    target = brief.get("target") or ""
    tone = brief.get("tone") or ""
    constraints = (brief.get("constraints") or "").lower()
    cat = trend.get("category") or ""
    label = trend.get("label") or ""
    summary = trend.get("summary") or ""
    kws: list[str] = []
    try:
        kws = json.loads(trend.get("keywords") or "[]")
    except json.JSONDecodeError:
        pass
    blob = f"{label} {summary}"

    sr = _sector_relevance(sector, cat, kws)
    tr = _target_relevance(target, label, summary)
    tim = _timing_relevance(trend_score)
    tc = _tone_compat(tone, risk, cat)

    fit = 0.40 * sr + 0.25 * tr + 0.20 * tim + 0.15 * tc

    if "polit" in constraints and _politics_in_trend(blob):
        fit *= 0.35
    if any(x in constraints for x in ("health", "santé", "médical")) and _health_sensitive(blob):
        fit *= 0.45
    if risk > 70:
        fit *= 0.75
    return max(0.0, min(100.0, fit))


def _templates(
    brief: dict[str, Any],
    trend: dict[str, Any],
    brand_fit_score: float,
    risk: float,
    urgency: str,
) -> dict[str, str]:
    client = brief.get("client_name") or "the brand"
    label = trend.get("label") or "this trend"
    tone = brief.get("tone") or "on-brand"
    return {
        "recommendation_text": f"Ride the “{label}” conversation to stay relevant for {client} with a {tone} touch.",
        "campaign_angle_safe": f"Connect lightly to “{label}” without overstating claims—focus on everyday moments.",
        "campaign_angle_bold": f"Own the “{label}” moment with a punchy, shareable POV that feels culturally now.",
        "campaign_angle_local": f"Angle tunisien: parlez comme vos audiences locales autour de « {label} » avec humour et repères du quotidien.",
        "suggested_formats": "TikTok / Reels, stories interactives, micro-sketches UGC",
        "influencer_type": "Micro-influenceurs lifestyle & étudiants en Tunisie",
    }


def generate_recommendations_for_brief(brief_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        conn.execute("DELETE FROM recommendations WHERE brief_id = ?", (brief_id,))
        brief_row = conn.execute(
            "SELECT * FROM client_briefs WHERE id = ?",
            (brief_id,),
        ).fetchone()
        if not brief_row:
            return []
        brief = _row_dict(brief_row)
        trends = conn.execute("SELECT * FROM trend_clusters ORDER BY trend_score DESC").fetchall()
        recs: list[tuple[float, dict[str, Any], dict[str, Any]]] = []

        for trow in trends:
            tr = _row_dict(trow)
            tscore = float(tr.get("trend_score") or 0)
            risk = float(tr.get("risk_score") or 0)
            bf = brand_fit(brief, tr, tscore, risk)
            urgency = urgency_from_trend_score(tscore)
            recs.append((bf, tr, {"urgency": urgency, "risk": risk}))

        recs.sort(key=lambda x: (-x[0], x[2]["risk"]))

        out: list[dict[str, Any]] = []
        ts = utc_now_iso()
        for bf, tr, meta in recs[:12]:
            if bf < 15:
                continue
            tpl = _templates(brief, tr, bf, meta["risk"], meta["urgency"])
            payload = {
                "brief_id": brief_id,
                "cluster_id": tr["id"],
                "brand_fit_score": bf,
                "risk_score": meta["risk"],
                **tpl,
                "urgency": meta["urgency"],
            }
            llm_payload = generate_json(
                f"""Given JSON brief and trend, return JSON with keys recommendation_text, campaign_angle_safe, campaign_angle_bold, campaign_angle_local, suggested_formats, influencer_type. Short, in English/French mix ok.
Brief: {json.dumps({k: brief.get(k) for k in ('sector','target','objective','tone','constraints')}, ensure_ascii=False)}
Trend: {json.dumps({k: tr.get(k) for k in ('label','summary','category')}, ensure_ascii=False)}
Scores brand_fit={bf:.0f} risk={meta['risk']:.0f}""",
                tpl,
            )
            cur = conn.execute(
                """
                INSERT INTO recommendations (
                  brief_id, cluster_id, brand_fit_score, risk_score, recommendation_text,
                  campaign_angle_safe, campaign_angle_bold, campaign_angle_local,
                  suggested_formats, influencer_type, urgency, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    brief_id,
                    tr["id"],
                    bf,
                    meta["risk"],
                    llm_payload.get("recommendation_text"),
                    llm_payload.get("campaign_angle_safe"),
                    llm_payload.get("campaign_angle_bold"),
                    llm_payload.get("campaign_angle_local"),
                    llm_payload.get("suggested_formats"),
                    llm_payload.get("influencer_type"),
                    meta["urgency"],
                    ts,
                ),
            )
            rid = int(cur.lastrowid)
            out.append(
                {
                    "id": rid,
                    "cluster_id": tr["id"],
                    "trend_label": tr.get("label"),
                    "brand_fit_score": round(bf, 1),
                    "risk_score": round(meta["risk"], 1),
                    "recommendation_text": llm_payload.get("recommendation_text"),
                    "campaign_angle_safe": llm_payload.get("campaign_angle_safe"),
                    "campaign_angle_bold": llm_payload.get("campaign_angle_bold"),
                    "campaign_angle_local": llm_payload.get("campaign_angle_local"),
                    "suggested_formats": llm_payload.get("suggested_formats"),
                    "influencer_type": llm_payload.get("influencer_type"),
                    "urgency": meta["urgency"],
                }
            )
        return out


def list_recommendations(brief_id: int) -> list[dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT r.*, c.label AS trend_label
            FROM recommendations r
            JOIN trend_clusters c ON c.id = r.cluster_id
            WHERE r.brief_id = ?
            ORDER BY r.brand_fit_score DESC, r.risk_score ASC
            """,
            (brief_id,),
        ).fetchall()
        return [
            {
                "id": r["id"],
                "cluster_id": r["cluster_id"],
                "trend_label": r["trend_label"],
                "brand_fit_score": round(float(r["brand_fit_score"] or 0), 1),
                "risk_score": round(float(r["risk_score"] or 0), 1),
                "recommendation_text": r["recommendation_text"],
                "campaign_angle_safe": r["campaign_angle_safe"],
                "campaign_angle_bold": r["campaign_angle_bold"],
                "campaign_angle_local": r["campaign_angle_local"],
                "suggested_formats": r["suggested_formats"],
                "influencer_type": r["influencer_type"],
                "urgency": r["urgency"],
            }
            for r in rows
        ]
