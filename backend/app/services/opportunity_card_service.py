from __future__ import annotations

import json
import sqlite3
from typing import Any

from app.repositories.brief import get_latest_brief
from app.repositories import brand as brand_repo
from app.services.brand_brain_service import brand_as_brief_proxy, score_trend_for_brand
from app.services.llm_service import generate_json
from app.services.rad_score_service import compute_rad_score
from app.services.recommendation_service import brand_fit
from app.services.trend_service import get_trends_for_api
from app.utils.time_utils import parse_iso

PLATFORM_LABELS: dict[str, str] = {
    "rss": "local media",
    "google_news": "Google News",
    "reddit": "Reddit",
    "itunes": "music charts",
    "apple_music": "music charts",
    "youtube": "YouTube",
    "gdelt": "GDELT",
    "serpapi": "Google Trends",
    "google_trends": "Google Trends",
    "mock_social": "TikTok / Instagram signal",
    "tiktok": "TikTok signal",
    "instagram": "Instagram signal",
    "facebook": "Facebook signal",
}

AUDIENCE_BY_CATEGORY: dict[str, dict[str, str]] = {
    "youth": {"ages": "18–30", "profile": "étudiants / Gen Z, lifestyle & digital"},
    "lifestyle": {"ages": "18–35", "profile": "lifestyle / musique / mode"},
    "culture": {"ages": "20–40", "profile": "culture, entertainment, local pride"},
    "sport": {"ages": "16–40", "profile": "fans sport & conversation sociale"},
    "weather": {"ages": "18–45", "profile": "quotidien, outdoor, consommation saisonnière"},
    "economy": {"ages": "25–45", "profile": "pouvoir d’achat, familles, décideurs"},
    "retail": {"ages": "20–45", "profile": "shoppers promo-sensibles"},
    "politics": {"ages": "25–55", "profile": "opinion / news — prudence marque"},
    "general": {"ages": "18–40", "profile": "audience média large"},
}

TN_HINTS = (
    "tunis",
    "tunisie",
    "tunisia",
    "sfax",
    "sousse",
    "djerba",
    "maghreb",
    "derja",
    "arabizi",
    "ramadan",
    "été",
    "summer",
    "canicule",
    "bac",
    "étudiant",
)


def _cluster_scores(conn: sqlite3.Connection, cluster_id: int) -> dict[str, float]:
    row = conn.execute(
        """
        SELECT growth_score, volume_score, diversity_score, recency_score,
               trend_score, risk_score, engagement_score
        FROM trend_clusters WHERE id = ?
        """,
        (cluster_id,),
    ).fetchone()
    if not row:
        return {
            "growth_score": 50.0,
            "volume_score": 0.0,
            "diversity_score": 0.0,
            "recency_score": 50.0,
            "trend_score": 0.0,
            "risk_score": 20.0,
            "engagement_score": 0.0,
        }
    keys = (
        "growth_score",
        "volume_score",
        "diversity_score",
        "recency_score",
        "trend_score",
        "risk_score",
        "engagement_score",
    )
    return {k: float(row[i] or 0) for i, k in enumerate(keys)}


def get_full_brief(conn: sqlite3.Connection, brief_id: int | None) -> dict[str, Any]:
    if not brief_id:
        return {}
    row = conn.execute("SELECT * FROM client_briefs WHERE id = ?", (brief_id,)).fetchone()
    if not row:
        return {}
    d = {k: row[k] for k in row.keys()}
    comps: list[str] = []
    raw = d.get("competitors_json")
    if raw:
        try:
            loaded = json.loads(raw)
            if isinstance(loaded, list):
                comps = [str(x) for x in loaded if str(x).strip()]
        except json.JSONDecodeError:
            pass
    d["competitors"] = comps
    return d


def _full_brief(conn: sqlite3.Connection, brief_id: int | None) -> dict[str, Any]:
    """Alias kept for internal callers."""
    return get_full_brief(conn, brief_id)


def _platforms_for_cluster(conn: sqlite3.Connection, cluster_id: int) -> list[str]:
    rows = conn.execute(
        """
        SELECT DISTINCT platform, source FROM media_items
        WHERE cluster_id = ? ORDER BY platform
        """,
        (cluster_id,),
    ).fetchall()
    labels: list[str] = []
    seen: set[str] = set()
    for platform, source in rows:
        p = (platform or "").lower()
        s = (source or "").lower()
        label = PLATFORM_LABELS.get(p)
        if not label:
            if "tiktok" in s:
                label = "TikTok signal"
            elif "instagram" in s or "insta" in s:
                label = "Instagram signal"
            elif "trend" in s or "serpapi" in p:
                label = "Google Trends"
            elif "music" in s or "itunes" in p or "apple" in s:
                label = "music charts"
            elif "news" in s or "google" in p:
                label = "Google News"
            else:
                label = "local media" if p in ("rss", "") else p or "signal"
        if label not in seen:
            seen.add(label)
            labels.append(label)
    return labels[:8]


def _tunisia_relevance(trend: dict[str, Any], scores: dict[str, float], sources: list[str]) -> float:
    blob = f"{trend.get('label')} {trend.get('summary')} {' '.join(trend.get('keywords') or [])}".lower()
    score = 35.0
    hits = sum(1 for h in TN_HINTS if h in blob)
    score += min(40.0, hits * 12.0)
    if any("local" in s.lower() or "media" in s.lower() for s in sources):
        score += 8.0
    if any("TikTok" in s or "Instagram" in s for s in sources):
        score += 6.0
    # Recency + diversity help local actionability
    score += scores["recency_score"] * 0.12
    score += scores["diversity_score"] * 0.08
    return round(min(100.0, score), 1)


def _momentum(scores: dict[str, float]) -> dict[str, Any]:
    g = scores["growth_score"]
    t = scores["trend_score"]
    value = round(min(100.0, 0.55 * t + 0.45 * g), 1)
    if g >= 72:
        direction = "↑ rapidly"
        arrow = "up_fast"
    elif g >= 58:
        direction = "↑ rising"
        arrow = "up"
    elif g <= 40:
        direction = "↓ cooling"
        arrow = "down"
    else:
        direction = "→ steady"
        arrow = "steady"
    return {"score": value, "direction": direction, "arrow": arrow, "growth_score": round(g, 1)}


def _lifecycle(scores: dict[str, float], first_seen: str | None) -> dict[str, str]:
    g = scores["growth_score"]
    vol = scores["volume_score"]
    age = None
    dt = parse_iso(first_seen)
    if dt:
        from datetime import datetime, timezone

        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0

    if g >= 65 and vol < 45 and (age is None or age <= 48):
        return {"key": "early_growth", "label": "Early Growth", "badge": "🟡"}
    if g >= 70 and vol >= 45:
        return {"key": "acceleration", "label": "Acceleration", "badge": "🟢"}
    if g <= 40 or (age is not None and age > 72 and g < 55):
        return {"key": "late", "label": "Late / Fading", "badge": "⚪"}
    if scores["risk_score"] >= 70:
        return {"key": "sensitive", "label": "Sensitive peak", "badge": "🔴"}
    return {"key": "growth", "label": "Growth", "badge": "🟢"}


def _audience(category: str, target: str | None) -> dict[str, str]:
    base = AUDIENCE_BY_CATEGORY.get((category or "general").lower(), AUDIENCE_BY_CATEGORY["general"])
    if target and target.strip():
        return {
            "ages": base["ages"],
            "profile": f"{base['profile']} · brief: {target.strip()[:80]}",
            "label": f"{base['ages']}, {base['profile']}",
        }
    return {
        "ages": base["ages"],
        "profile": base["profile"],
        "label": f"{base['ages']}, {base['profile']}",
    }


def _fit_reasons(brief: dict[str, Any], trend: dict[str, Any], fit: float) -> list[str]:
    reasons: list[str] = []
    sector = (brief.get("sector") or "").lower()
    target = (brief.get("target") or "").lower()
    cat = (trend.get("category") or "").lower()
    blob = f"{trend.get('label')} {trend.get('summary')}".lower()

    if any(x in sector for x in ("beverage", "drink", "food", "boisson")):
        if cat in ("weather", "youth", "lifestyle", "sport", "culture"):
            reasons.append("summer / occasion de consommation")
        if "youth" in cat or "étudiant" in blob or "student" in target:
            reasons.append("audience jeune")
        if "music" in blob or "musique" in blob or cat == "culture":
            reasons.append("association musique / culture")
        reasons.append("contexte outdoor / social")
    if any(x in sector for x in ("telecom", "telco")):
        reasons.append("usage digital & moments de conversation")
        if cat in ("youth", "sport", "culture"):
            reasons.append("affinité jeunesse / divertissement")
    if any(x in sector for x in ("bank", "finance")):
        reasons.append("lien pouvoir d’achat / moments quotidiens")
    if "student" in target or "gen z" in target or "jeune" in target:
        reasons.append("cible brief alignée Gen Z / étudiants")
    if cat == "weather":
        reasons.append("saisonnalité forte (météo / été)")
    if not reasons:
        if fit >= 70:
            reasons = ["catégorie compatible avec le secteur", "timing culturel favorable", "risque encore gérable"]
        elif fit >= 45:
            reasons = ["overlap partiel avec le brief", "fenêtre encore jouable avec un angle prudent"]
        else:
            reasons = ["fit faible — utile surtout comme veille, pas comme push marque"]
    # unique preserve order
    out: list[str] = []
    for r in reasons:
        if r not in out:
            out.append(r)
    return out[:5]


def _clamp_aud(v: float) -> float:
    return max(0.0, min(100.0, v))


def _saturation(scores: dict[str, float]) -> float:
    # High volume + low growth ≈ saturated
    sat = 0.55 * scores["volume_score"] + 0.25 * (100 - scores["growth_score"]) + 0.20 * (
        100 - scores["recency_score"]
    )
    return round(min(100.0, max(0.0, sat)), 1)


def _risk_label(risk: float) -> str:
    if risk >= 70:
        return "high"
    if risk >= 45:
        return "medium"
    return "low"


def _timing_days(lifecycle_key: str, trend_score: float) -> str:
    if lifecycle_key in ("early_growth", "acceleration") or trend_score >= 75:
        return "launch within 5–7 days"
    if trend_score >= 55:
        return "act this week (7–10 days)"
    return "monitor; evergreen only if strategic"


def _campaign_name(label: str, brief: dict[str, Any]) -> str:
    sector = (brief.get("sector") or "").lower()
    low = label.lower()
    if any(x in low for x in ("summer", "été", "canicule", "heat", "nostalg")):
        return "رجعنا للصيف"
    if any(x in low for x in ("exam", "bac", "étudiant", "student")):
        return "Mode examen, mode survie"
    if "sport" in low or "derby" in low or "football" in low:
        return "Match day energy"
    if any(x in sector for x in ("beverage", "drink", "boisson")):
        return f"Moment {brief.get('client_name') or 'marque'}"
    short = label.strip()
    if len(short) > 42:
        short = short[:40] + "…"
    return f"Hop on: {short}"


def _why_growing_fallback(trend: dict[str, Any], scores: dict[str, float], sources: list[str]) -> str:
    label = trend.get("label") or "Ce sujet"
    cat = trend.get("category") or "général"
    summary = (trend.get("summary") or "").strip()
    src = ", ".join(sources[:4]) if sources else "plusieurs sources publiques"
    g = scores["growth_score"]
    parts = [
        f"«{label}» monte dans la conversation {cat} (croissance {g:.0f}/100), visible sur {src}.",
        summary[:180] + ("…" if len(summary) > 180 else "")
        if summary
        else "Les signaux agrégés montrent une accélération récente du volume et de la diversité des sources.",
        "En Tunisie / MENA, ce type de moment se propage vite entre presse locale, charts et formats courts — la fenêtre créative est courte.",
        "RadArt le classe comme opportunité actionnable tant que la saturation reste gérable et le risque sous contrôle.",
    ]
    return " ".join(p for p in parts if p)


def _recommended_move(
    brief: dict[str, Any],
    trend: dict[str, Any],
    *,
    lifecycle_key: str,
    trend_score: float,
    risk: float,
    saturation: float,
    local_angle: str | None = None,
    verdict: str | None = None,
) -> dict[str, Any]:
    label = trend.get("label") or "cette tendance"
    client = brief.get("client_name") or "la marque"
    if verdict == "skip":
        return {
            "campaign": "Ne pas chase",
            "concept": (
                f"«{label}» est bruyant mais mal aligné avec {client}. "
                "Garder en veille ; ne pas engager budget créatif."
            ),
            "channels": "—",
            "timing": "skip this wave",
            "risk": _risk_label(risk),
            "risk_score": round(risk, 1),
            "trend_saturation": saturation,
            "trend_saturation_label": f"{saturation:.0f}%",
        }
    campaign = _campaign_name(label, brief)
    concept = local_angle or (
        f"Concept → formats courts qui relient «{label}» au quotidien de {client}, "
        "avec son / image nostalgique ou locale et un CTA léger."
    )
    channels = "TikTok + Reels"
    return {
        "campaign": campaign,
        "concept": concept,
        "channels": channels,
        "timing": _timing_days(lifecycle_key, trend_score),
        "risk": _risk_label(risk),
        "risk_score": round(risk, 1),
        "trend_saturation": saturation,
        "trend_saturation_label": f"{saturation:.0f}%",
    }


def build_opportunity_card(
    conn: sqlite3.Connection,
    trend: dict[str, Any],
    brief: dict[str, Any] | None = None,
    *,
    use_llm: bool = True,
    brand: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cid = int(trend["id"])
    scores = _cluster_scores(conn, cid)
    sources = _platforms_for_cluster(conn, cid)
    brand = brand if brand is not None else brand_repo.get_active_brand(conn)
    brief = brief or {}
    if brand and not (brief.get("id") or brief.get("raw_brief") or brief.get("sector")):
        brief = brand_as_brief_proxy(brand)
    elif brand and brief:
        # Prefer Brand DNA name/industry when present
        brief = {
            **brief,
            "client_name": brand.get("brand_name") or brief.get("client_name"),
            "sector": brand.get("industry") or brief.get("sector"),
            "target": brand.get("audience") or brief.get("target"),
            "tone": brand.get("tone") or brand.get("personality") or brief.get("tone"),
            "constraints": ", ".join(brand.get("forbidden_topics") or [])
            or brief.get("constraints"),
            "competitors": brand.get("competitors") or brief.get("competitors") or [],
        }

    momentum = _momentum(scores)
    lifecycle = _lifecycle(scores, trend.get("first_seen_at"))
    audience = _audience(
        str(trend.get("category") or ""),
        (brand or {}).get("audience") or brief.get("target"),
    )
    tn = _tunisia_relevance(trend, scores, sources)
    saturation = _saturation(scores)
    risk = float(scores["risk_score"] or trend.get("risk_score") or 0)

    dna_score = None
    fit = 0.0
    reasons: list[str] = []
    verdict = None
    if brand:
        dna_score = score_trend_for_brand(
            brand,
            trend,
            trend_score=float(scores["trend_score"]),
            risk_score=risk,
        )
        fit = float(dna_score["fit_percent"])
        reasons = list(dna_score.get("reasons") or [])
        if dna_score.get("verdict") == "skip":
            reasons = list(dna_score.get("skip_reasons") or reasons)
        verdict = dna_score.get("verdict")
    elif brief.get("id") or brief.get("raw_brief") or brief.get("sector"):
        tr_for_fit = {
            "category": trend.get("category"),
            "label": trend.get("label"),
            "summary": trend.get("summary"),
            "keywords": json.dumps(trend.get("keywords") or [], ensure_ascii=False)
            if not isinstance(trend.get("keywords"), str)
            else trend.get("keywords"),
        }
        fit = brand_fit(brief, tr_for_fit, float(scores["trend_score"]), risk)
        reasons = _fit_reasons(brief, trend, fit)
        verdict = "chase" if fit >= 70 else ("caution" if fit >= 40 else "skip")

    why = _why_growing_fallback(trend, scores, sources)
    # Prefer brand channels in recommended move when chasing
    move = _recommended_move(
        brief,
        trend,
        lifecycle_key=lifecycle["key"],
        trend_score=float(scores["trend_score"]),
        risk=risk,
        saturation=saturation,
        verdict=verdict,
    )
    if brand and verdict != "skip" and brand.get("channels"):
        move["channels"] = " + ".join(brand["channels"][:3])

    fallback_llm = {
        "title": trend.get("label") or "Opportunity",
        "why_growing": why,
        "campaign": move["campaign"],
        "concept": move["concept"],
        "channels": move["channels"],
        "fit_reasons": reasons,
    }

    if use_llm and (brief or brand) and verdict != "skip":
        enriched = generate_json(
            f"""Build a marketing Opportunity Card JSON for Tunisia/MENA agencies.
Return keys: title (catchy English or FR), why_growing (3-4 sentences cultural context),
campaign (short campaign name, Derja/FR ok), concept (1 sentence), channels (short),
fit_reasons (array of 3-5 short reasons).
Brand DNA: {brand.get('brand_name') if brand else brief.get('client_name')} industry={brand.get('industry') if brand else brief.get('sector')} audience={brand.get('audience') if brand else brief.get('target')} personality={brand.get('personality') if brand else ''} tone={brand.get('tone') if brand else brief.get('tone')} forbidden={brand.get('forbidden_topics') if brand else []}
Trend label={trend.get('label')} summary={trend.get('summary')} category={trend.get('category')}
Scores momentum={momentum['score']} tunisia={tn} fit={fit:.0f} risk={risk:.0f} saturation={saturation} verdict={verdict}
""",
            fallback_llm,
        )
        title = str(enriched.get("title") or trend.get("label"))
        why = str(enriched.get("why_growing") or why)
        move["campaign"] = str(enriched.get("campaign") or move["campaign"])
        move["concept"] = str(enriched.get("concept") or move["concept"])
        move["channels"] = str(enriched.get("channels") or move["channels"])
        fr = enriched.get("fit_reasons")
        if isinstance(fr, list) and fr and verdict != "skip":
            reasons = [str(x) for x in fr][:5]
    else:
        title = str(trend.get("label") or "Opportunity")

    brand_block = None
    if brand or brief.get("id") or brief.get("client_name") or brief.get("sector"):
        brand_block = {
            "brand": (brand or {}).get("brand_name") or brief.get("client_name") or "Votre marque",
            "fit_percent": round(fit, 1),
            "fit_label": f"{round(fit):.0f}% fit",
            "reasons": reasons,
            "verdict": verdict or ("chase" if fit >= 70 else "caution"),
            "verdict_label": (dna_score or {}).get("verdict_label")
            if dna_score
            else ("Chase" if fit >= 70 else ("Caution" if fit >= 40 else "Don’t chase")),
            "action": (dna_score or {}).get("action")
            if dna_score
            else (
                f"Fit {fit:.0f}% — {'push' if fit >= 70 else 'prudence' if fit >= 40 else 'ne pas chase'}."
            ),
            "from_brand_brain": bool(brand),
        }

    status = "opportunity"
    if verdict == "skip":
        status = "dont_chase"
    elif risk >= 70:
        status = "watch_risk"
    elif lifecycle["key"] == "late":
        status = "fading"
    elif fit >= 70:
        status = "strong_fit"

    status_dot = {
        "strong_fit": "🟢",
        "watch_risk": "🔴",
        "dont_chase": "⛔",
        "fading": "⚪",
    }.get(status, "🟡")

    # Audience overlap: prefer Brand Brain audience dimension when available
    audience_overlap = float(fit) if brand or brief else 50.0
    if brand and dna_score:
        # Blend overall DNA fit with category audience heuristic
        aud_profile = _audience(str(trend.get("category") or ""), brand.get("audience"))
        audience_overlap = _clamp_aud(
            0.65 * float(dna_score["fit_percent"]) + 0.35 * (75.0 if "18" in aud_profile["ages"] else 55.0)
        )

    rad = compute_rad_score(
        momentum=float(momentum["score"]),
        freshness=float(scores.get("recency_score") or 50.0),
        tunisia_relevance=float(tn),
        audience_overlap=float(audience_overlap),
        brand_fit=float(fit) if (brand or brief) else 0.0,
        source_diversity=float(scores.get("diversity_score") or 0.0),
        competitive_saturation=float(saturation),
        brand_safety_risk=float(risk),
        brand_name=(brand or {}).get("brand_name") or brief.get("client_name"),
        verdict=verdict,
    )

    # Status can follow RAD when no hard skip
    if verdict != "skip" and rad["score_int"] >= 80:
        status = "strong_fit"
        status_dot = "🟢"
    elif verdict != "skip" and rad["score_int"] < 35 and status == "opportunity":
        status = "fading"
        status_dot = "⚪"

    return {
        "cluster_id": cid,
        "title": title,
        "status": status,
        "status_dot": status_dot,
        "rad_score": rad,
        "momentum": momentum,
        "tunisia_relevance": tn,
        "audience": audience,
        "lifecycle": lifecycle,
        "sources": sources,
        "why_growing": why,
        "brand_fit": brand_block,
        "recommended_move": move,
        "brand_brain": {
            "active": bool(brand),
            "brand_name": (brand or {}).get("brand_name"),
            "industry": (brand or {}).get("industry"),
        }
        if brand
        else None,
        "trend": {
            "id": cid,
            "label": trend.get("label"),
            "summary": trend.get("summary"),
            "category": trend.get("category"),
            "keywords": trend.get("keywords") or [],
            "trend_score": round(float(scores["trend_score"]), 1),
            "risk_score": round(risk, 1),
            "item_count": trend.get("item_count"),
            "source_count": trend.get("source_count"),
        },
        "value_prop": "RAD Score = Trend × Brand — what to chase, and why.",
    }


def list_opportunity_cards(
    conn: sqlite3.Connection,
    *,
    limit: int = 12,
    use_llm: bool = False,
) -> dict[str, Any]:
    brand = brand_repo.get_active_brand(conn)
    latest = get_latest_brief(conn)
    brief = get_full_brief(conn, latest.get("id"))
    trends = get_trends_for_api(conn)
    cards = [
        build_opportunity_card(conn, t, brief, use_llm=use_llm, brand=brand)
        for t in trends[: max(1, min(limit, 20))]
    ]
    cards.sort(
        key=lambda c: (
            0 if (c.get("brand_fit") or {}).get("verdict") == "chase" else 1,
            -float((c.get("rad_score") or {}).get("score") or 0),
            -float((c.get("brand_fit") or {}).get("fit_percent") or c["momentum"]["score"]),
            -c["momentum"]["score"],
        )
    )
    return {
        "brief_context": {
            "brief_id": brief.get("id"),
            "client_name": (brand or {}).get("brand_name") or brief.get("client_name"),
            "sector": (brand or {}).get("industry") or brief.get("sector"),
            "has_brief": bool(brief.get("id")),
            "has_brand_brain": bool(brand),
        },
        "count": len(cards),
        "cards": cards,
    }
