from __future__ import annotations

import sqlite3
from typing import Any, Literal

from app.repositories import brand as brand_repo
from app.repositories.brief import get_latest_brief
from app.services.brand_brain_service import brand_as_brief_proxy
from app.services.llm_service import generate_json
from app.services.opportunity_card_service import build_opportunity_card, get_full_brief
from app.services.trend_service import get_trends_for_api

JumpRec = Literal["YES", "CAUTION", "NO"]


def _maturity_label(lifecycle_key: str) -> str:
    return {
        "early_growth": "Early",
        "acceleration": "Rising",
        "growth": "Mid",
        "late": "Late",
        "sensitive": "Sensitive peak",
    }.get(lifecycle_key, "Mid")


def _sat_label(sat: float) -> str:
    if sat < 40:
        return "Low"
    if sat < 65:
        return "Medium"
    return "High"


def _risk_label_simple(risk: float) -> str:
    if risk < 40:
        return "Low"
    if risk < 65:
        return "Medium"
    return "High"


def _recommendation(
    *,
    rad: float,
    brand_fit: float,
    risk: float,
    verdict: str | None,
    saturation: float,
) -> tuple[JumpRec, str, str]:
    if verdict == "skip" or brand_fit < 35 or risk >= 75:
        return (
            "NO",
            "NO — don’t jump",
            "Trend may be loud, but Brand Brain / risk says this is not your fight.",
        )
    if rad >= 72 and brand_fit >= 70 and risk < 55 and saturation < 70:
        return (
            "YES",
            "YES — move quickly",
            "Strong Trend × Brand alignment: act while the window is still early.",
        )
    if rad >= 55 and brand_fit >= 45 and risk < 70:
        return (
            "CAUTION",
            "CAUTION — only with a sharp angle",
            "Partial fit. Jump only if creative can own a differentiated local POV.",
        )
    return (
        "NO",
        "NO — monitor, don’t jump",
        "RAD / fit / risk don’t justify budget. Keep watching.",
    )


def analyze_jump(conn: sqlite3.Connection, cluster_id: int) -> dict[str, Any]:
    trends = get_trends_for_api(conn)
    trend = next((t for t in trends if int(t["id"]) == cluster_id), None)
    if not trend:
        return {"error": "trend_not_found", "cluster_id": cluster_id}

    brand = brand_repo.get_active_brand(conn)
    latest = get_latest_brief(conn)
    brief = get_full_brief(conn, latest.get("id"))
    card = build_opportunity_card(conn, trend, brief, use_llm=False, brand=brand)

    rad = card.get("rad_score") or {}
    fit = card.get("brand_fit") or {}
    move = card.get("recommended_move") or {}
    life = card.get("lifecycle") or {}
    brand_fit = float(fit.get("fit_percent") or 0)
    audience_fit = float((rad.get("components") or {}).get("audience_overlap") or brand_fit)
    sat = float(move.get("trend_saturation") or (rad.get("components") or {}).get("competitive_saturation") or 50)
    risk = float(move.get("risk_score") or card.get("trend", {}).get("risk_score") or 0)
    rad_score = float(rad.get("score") or 0)
    verdict = fit.get("verdict")

    rec, rec_label, rec_why = _recommendation(
        rad=rad_score,
        brand_fit=brand_fit,
        risk=risk,
        verdict=verdict,
        saturation=sat,
    )

    scores = {
        "brand_fit": round(brand_fit, 1),
        "audience_fit": round(audience_fit, 1),
        "trend_maturity": _maturity_label(str(life.get("key") or "")),
        "trend_maturity_badge": life.get("badge") or "",
        "competitor_saturation": _sat_label(sat),
        "competitor_saturation_score": round(sat, 1),
        "reputational_risk": _risk_label_simple(risk),
        "reputational_risk_score": round(risk, 1),
        "rad_score": rad.get("score_int") or int(round(rad_score)),
    }

    can_generate = rec in ("YES", "CAUTION") and bool(brand or brief.get("id") or brief.get("client_name"))

    return {
        "cluster_id": cluster_id,
        "trend_label": card.get("title") or trend.get("label"),
        "brand": (brand or {}).get("brand_name") or brief.get("client_name") or None,
        "has_brand_brain": bool(brand),
        "recommendation": rec,
        "recommendation_label": rec_label,
        "recommendation_why": rec_why,
        "scores": scores,
        "rad_why": rad.get("why"),
        "can_generate_campaign": can_generate,
        "opportunity": card,
        "cta": "Generate Campaign" if can_generate else "Activate Brand Brain first",
    }


def _campaign_fallback(
    *,
    brand: dict[str, Any] | None,
    brief: dict[str, Any],
    card: dict[str, Any],
    jump: dict[str, Any],
) -> dict[str, Any]:
    brand_name = (brand or {}).get("brand_name") or brief.get("client_name") or "la marque"
    label = card.get("title") or "cette tendance"
    industry = (brand or {}).get("industry") or brief.get("sector") or "lifestyle"
    tone = (brand or {}).get("tone") or (brand or {}).get("personality") or brief.get("tone") or "local & accessible"
    langs = (brand or {}).get("languages") or ["French", "derja"]
    channels = (brand or {}).get("channels") or ["TikTok", "Instagram"]
    move = card.get("recommended_move") or {}
    campaign_name = move.get("campaign") or f"Moment {brand_name}"

    return {
        "big_idea": f"{brand_name} owns the cultural moment around «{label}» without forcing it — we join the conversation as a local companion, not a billboard.",
        "consumer_insight": (
            f"Les audiences {jump['scores'].get('audience_fit', 70)}% alignées vivent déjà «{label}» "
            "dans leur feed ; elles veulent une marque qui parle leur langue (derja/FR) et leur humour, pas un slogan corporate."
        ),
        "campaign_concept": move.get("concept")
        or f"Série de formats courts : scènes quotidiennes tunisiennes liées à «{label}», punchline {tone}, produit {brand_name} en cameo naturel.",
        "key_message": f"{brand_name} — présent quand le moment compte.",
        "tiktok_reel_concepts": [
            f"POV: tu sens «{label}» partout — cut rapide + son local + packshot soft {brand_name}.",
            f"Duet / stitch trend : on reprend le format viral avec un twist {industry} tunisien.",
            f"Before/after énergie : quotidien stress → moment {brand_name} lié à «{label}».",
        ],
        "caption_ideas": [
            f"Chnowa el vibe tawa? {brand_name} m3ak. #Tunisie",
            f"Quand «{label}» tape le feed — on répond avec le sourire.",
            f"{campaign_name} · tag un.e pote qui vit ça aussi.",
        ],
        "visual_direction": (
            "Lumière naturelle, textures locales, faces réelles (UGC-style), couleurs marque en accent, "
            "pas de gloss pub luxe sauf si brand premium."
        ),
        "influencer_profile": (
            f"Micro-créateurs Tunisie 5k–80k, {tone}, bilingual {' / '.join(langs[:2])}, "
            f"niche {industry} / lifestyle — pas célébrités globales."
        ),
        "hashtags": [
            "#Tunisie",
            f"#{brand_name.replace(' ', '')}",
            "#TendanceTN",
            "#Reels",
            "#TikTokTunisie",
        ],
        "timing": move.get("timing") or "Launch within 5–7 days",
        "kpis": [
            "View-through rate / completion sur 3 créas",
            "Engagement rate (likes+comments+shares)/reach",
            "Saves + profile visits",
            "Hashtag / branded mention volume 7 jours",
            "Qualitative: % commentaires on-brand vs risk",
        ],
        "channels": " + ".join(channels[:3]),
        "campaign_name": campaign_name,
    }


def generate_campaign(conn: sqlite3.Connection, cluster_id: int) -> dict[str, Any]:
    jump = analyze_jump(conn, cluster_id)
    if jump.get("error"):
        return jump
    if jump.get("recommendation") == "NO":
        return {
            **jump,
            "campaign": None,
            "blocked": True,
            "blocked_reason": "Recommendation is NO — RadArt won’t generate a campaign you shouldn’t jump on.",
        }

    brand = brand_repo.get_active_brand(conn)
    latest = get_latest_brief(conn)
    brief = get_full_brief(conn, latest.get("id")) or {}
    if brand and not brief:
        brief = brand_as_brief_proxy(brand)
    card = jump.get("opportunity") or {}

    fallback = _campaign_fallback(brand=brand, brief=brief, card=card, jump=jump)
    enriched = generate_json(
        f"""You are a Tunisia/MENA creative strategist. Return JSON campaign pack with keys:
big_idea, consumer_insight, campaign_concept, key_message,
tiktok_reel_concepts (array of 3 strings), caption_ideas (array of 3, mix French/derja ok),
visual_direction, influencer_profile, hashtags (array), timing, kpis (array of 4-6),
channels, campaign_name.
Brand: {(brand or {}).get('brand_name') or brief.get('client_name')} industry={(brand or {}).get('industry')} 
audience={(brand or {}).get('audience')} tone={(brand or {}).get('tone') or (brand or {}).get('personality')}
forbidden={(brand or {}).get('forbidden_topics')} languages={(brand or {}).get('languages')}
Trend: {jump.get('trend_label')} recommendation={jump.get('recommendation')}
RAD={jump['scores'].get('rad_score')} brand_fit={jump['scores'].get('brand_fit')}
Keep it executable for TikTok/Reels agencies. Short punchy copy.
""",
        fallback,
    )

    # Normalize arrays
    for key in ("tiktok_reel_concepts", "caption_ideas", "hashtags", "kpis"):
        val = enriched.get(key)
        if isinstance(val, str):
            enriched[key] = [v.strip() for v in val.split("\n") if v.strip()]
        elif not isinstance(val, list):
            enriched[key] = fallback.get(key, [])

    return {
        "cluster_id": cluster_id,
        "recommendation": jump["recommendation"],
        "recommendation_label": jump["recommendation_label"],
        "scores": jump["scores"],
        "brand": jump.get("brand"),
        "trend_label": jump.get("trend_label"),
        "campaign": {**fallback, **{k: enriched[k] for k in fallback if k in enriched}},
        "blocked": False,
        "pipeline": "social listening → jump decision → marketing execution",
    }
