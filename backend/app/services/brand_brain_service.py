from __future__ import annotations

from typing import Any, Literal

Verdict = Literal["chase", "caution", "skip"]

FORBIDDEN_ALIASES: dict[str, tuple[str, ...]] = {
    "politics": ("politic", "politique", "gouvernement", "président", "élection", "parlement"),
    "religion": ("religion", "islam", "église", "mosque", "halal claim", "fatwa"),
    "tragedy": ("mort", "décès", "accident", "attaque", "terror", "massacre"),
    "scandal": ("scandale", "scandal", "corruption"),
    "health claims": ("maladie", "hôpital", "cure", "médical", "santé claim"),
}

INDUSTRY_CATEGORY_FIT: dict[str, tuple[str, ...]] = {
    "beverage": ("weather", "youth", "lifestyle", "sport", "culture", "retail"),
    "food": ("youth", "lifestyle", "culture", "weather", "retail"),
    "telecom": ("youth", "sport", "culture", "lifestyle", "economy"),
    "banking": ("economy", "retail", "youth"),
    "beauty": ("lifestyle", "culture", "weather", "youth"),
    "retail": ("retail", "economy", "youth", "lifestyle"),
    "tourism": ("culture", "weather", "lifestyle", "sport"),
}


def _blob(trend: dict[str, Any]) -> str:
    parts = [
        str(trend.get("label") or ""),
        str(trend.get("summary") or ""),
        str(trend.get("category") or ""),
        " ".join(str(k) for k in (trend.get("keywords") or [])),
    ]
    return " ".join(parts).lower()


def _forbidden_hit(forbidden: list[str], blob: str) -> str | None:
    for topic in forbidden:
        t = topic.strip().lower()
        if not t:
            continue
        if t in blob:
            return topic
        aliases = FORBIDDEN_ALIASES.get(t)
        if aliases and any(a in blob for a in aliases):
            return topic
        # fuzzy: first word
        head = t.split()[0]
        if len(head) > 3 and head in blob:
            return topic
    return None


def _industry_fit(industry: str, category: str) -> float:
    ind = (industry or "").lower()
    cat = (category or "").lower()
    for key, cats in INDUSTRY_CATEGORY_FIT.items():
        if key in ind:
            return 88.0 if cat in cats else 42.0
    if cat and cat in ind:
        return 75.0
    return 55.0


def _audience_fit(audience: str, category: str, blob: str) -> float:
    a = (audience or "").lower()
    score = 50.0
    if any(x in a for x in ("16", "18", "gen z", "jeune", "youth", "étudiant")):
        if category in ("youth", "lifestyle", "culture", "sport") or any(
            x in blob for x in ("étudiant", "jeune", "tiktok", "meme")
        ):
            score = 90.0
        else:
            score = 55.0
    if any(x in a for x in ("famille", "family", "parent")):
        if category in ("retail", "economy", "weather"):
            score = max(score, 80.0)
    return score


def _personality_tone_fit(personality: str, tone: str, blob: str, risk: float) -> float:
    p = f"{personality} {tone}".lower()
    score = 65.0
    if any(x in p for x in ("funny", "humour", "playful", "accessible", "tunisian", "derja")):
        if any(x in blob for x in ("humour", "meme", "tiktok", "été", "summer", "music", "sport")):
            score = 88.0
        if risk >= 65:
            score = 35.0
    if "premium" in p and any(x in blob for x in ("discount", "promo", "cheap")):
        score = 40.0
    return score


def score_trend_for_brand(
    brand: dict[str, Any],
    trend: dict[str, Any],
    *,
    trend_score: float,
    risk_score: float,
) -> dict[str, Any]:
    """Interpret a trend through Brand DNA — including when NOT to chase."""
    blob = _blob(trend)
    cat = str(trend.get("category") or "")
    brand_name = brand.get("brand_name") or "your brand"
    forbidden = list(brand.get("forbidden_topics") or [])

    reasons: list[str] = []
    skip_reasons: list[str] = []

    hit = _forbidden_hit(forbidden, blob)
    if hit:
        skip_reasons.append(f"Forbidden topic for {brand_name}: {hit}")

    if risk_score >= 75 and any(x in forbidden for x in ("politics", "religion", "tragedy", "scandal")):
        skip_reasons.append("High risk signal clashes with brand safety rules")

    ind = _industry_fit(str(brand.get("industry") or ""), cat)
    aud = _audience_fit(str(brand.get("audience") or ""), cat, blob)
    pers = _personality_tone_fit(
        str(brand.get("personality") or ""),
        str(brand.get("tone") or ""),
        blob,
        risk_score,
    )
    timing = min(100.0, float(trend_score))

    # Channel affinity soft boost
    channels = [c.lower() for c in (brand.get("channels") or [])]
    channel_boost = 0.0
    if any("tiktok" in c for c in channels) and any(x in blob for x in ("tiktok", "meme", "sound", "music")):
        channel_boost = 8.0
        reasons.append("Aligné canaux courts (TikTok / Reels)")

    fit = 0.34 * ind + 0.26 * aud + 0.22 * pers + 0.18 * timing + channel_boost

    # Celebrity / global pop culture with weak local brand relevance → penalize hard
    global_pop = any(
        x in blob
        for x in (
            "taylor swift",
            "beyoncé",
            "beyonce",
            "oscar",
            "grammy",
            "netflix us",
            "hollywood",
            "eras tour",
            "kardashian",
            "met gala",
        )
    )
    local_anchor = any(
        x in blob
        for x in ("tunis", "tunisie", "tunisia", "derja", "maghreb", "sfax", "sousse")
    )
    if global_pop and not local_anchor:
        fit = min(fit, 28.0) * 0.85
        skip_reasons.append(
            f"Trending globally, but only {fit:.0f}% fit for {brand_name} — don’t chase by default"
        )

    if hit:
        fit = min(fit, 22.0)

    fit = max(0.0, min(100.0, fit))

    if ind >= 70:
        reasons.append(f"Industry fit ({brand.get('industry') or 'n/a'} ↔ {cat or 'general'})")
    if aud >= 75:
        reasons.append(f"Audience overlap ({brand.get('audience') or 'n/a'})")
    if pers >= 75:
        reasons.append(f"Tone/personality match ({brand.get('personality') or brand.get('tone') or 'on-brand'})")
    if brand.get("country") and str(brand.get("country")).lower() in ("tunisia", "tunisie"):
        reasons.append("Local market lens (Tunisia / MENA)")

    langs = brand.get("languages") or []
    if any("derja" in str(l).lower() or "arabizi" in str(l).lower() for l in langs):
        reasons.append("Languages: derja / arabizi ready")

    if fit < 35 and not skip_reasons:
        skip_reasons.append("Low Brand DNA fit — trend is loud but not for you")

    if fit >= 70 and not hit:
        verdict: Verdict = "chase"
        verdict_label = "Chase — strong Brand DNA fit"
        action = "Build an Opportunity Card angle and brief creative this week."
    elif fit >= 40 and not hit:
        verdict = "caution"
        verdict_label = "Caution — partial fit"
        action = "Only if you have a sharp local angle; otherwise skip."
    else:
        verdict = "skip"
        verdict_label = "Don’t chase"
        action = (
            f"{brand_name}: fit {fit:.0f}% — do not burn budget on this moment."
        )

    return {
        "brand": brand_name,
        "fit_percent": round(fit, 1),
        "fit_label": f"{round(fit):.0f}% fit",
        "verdict": verdict,
        "verdict_label": verdict_label,
        "action": action,
        "reasons": (reasons[:5] if verdict != "skip" else reasons[:2]),
        "skip_reasons": skip_reasons[:4],
        "industry": brand.get("industry"),
        "audience": brand.get("audience"),
        "forbidden_hit": hit,
    }


def brand_as_brief_proxy(brand: dict[str, Any]) -> dict[str, Any]:
    """Map Brand DNA into the older brief-shaped dict for shared helpers."""
    return {
        "id": brand.get("id"),
        "client_name": brand.get("brand_name"),
        "sector": brand.get("industry"),
        "target": brand.get("audience"),
        "objective": ", ".join(brand.get("objectives") or []),
        "tone": brand.get("tone") or brand.get("personality"),
        "constraints": ", ".join(brand.get("forbidden_topics") or []),
        "competitors": list(brand.get("competitors") or []),
        "raw_brief": (
            f"Brand {brand.get('brand_name')}. Industry {brand.get('industry')}. "
            f"Audience {brand.get('audience')}. Personality {brand.get('personality')}. "
            f"Tone {brand.get('tone')}. Languages {', '.join(brand.get('languages') or [])}. "
            f"Channels {', '.join(brand.get('channels') or [])}. "
            f"Forbidden {', '.join(brand.get('forbidden_topics') or [])}."
        ),
    }
