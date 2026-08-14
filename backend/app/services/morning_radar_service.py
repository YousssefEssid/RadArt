from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from typing import Any, Literal

from app.repositories.brief import get_latest_brief
from app.repositories import brand as brand_repo
from app.services.competitive_alerts_service import build_competitive_alerts
from app.services.opportunity_card_service import build_opportunity_card, get_full_brief
from app.services.trend_service import get_trends_for_api
from app.utils.text_clean import clean_display_title
from app.utils.time_utils import parse_iso

SignalKind = Literal[
    "emerging",
    "growing",
    "competitor_move",
    "conversation_shift",
    "reputation",
    "brand_opportunity",
    "fading",
]

SIGNAL_META: dict[SignalKind, dict[str, str]] = {
    "emerging": {
        "emoji": "🔥",
        "label_fr": "Émergent",
        "question": "Nouveau sujet / format qui accélère",
    },
    "growing": {
        "emoji": "🚀",
        "label_fr": "En croissance",
        "question": "Forte croissance sur 24–72 h",
    },
    "competitor_move": {
        "emoji": "⚡",
        "label_fr": "Mouvement concurrent",
        "question": "Signal lié à un concurrent du brief",
    },
    "conversation_shift": {
        "emoji": "💬",
        "label_fr": "Basculement de conversation",
        "question": "La conversation catégorie / sources change",
    },
    "reputation": {
        "emoji": "⚠️",
        "label_fr": "Réputation",
        "question": "Conversation sensible ou négative qui monte",
    },
    "brand_opportunity": {
        "emoji": "🎯",
        "label_fr": "Opportunité marque",
        "question": "Tendance bien alignée avec le brief client",
    },
    "fading": {
        "emoji": "💤",
        "label_fr": "En déclin",
        "question": "Sujet déjà saturé ou qui redescend",
    },
}

# Sector keywords for brand-fit without LLM
_SECTOR_HINTS: dict[str, tuple[str, ...]] = {
    "beverage": ("boisson", "drink", "café", "coffee", "youth", "weather", "lifestyle", "sport"),
    "food": ("food", "restaurant", "youth", "lifestyle", "culture", "weather"),
    "telecom": ("youth", "sport", "digital", "tech", "lifestyle", "culture"),
    "banking": ("economy", "retail", "youth", "finance"),
    "beauty": ("lifestyle", "weather", "culture", "youth"),
    "retail": ("retail", "economy", "youth", "lifestyle"),
    "tourism": ("culture", "weather", "tourism", "lifestyle"),
}


def _hours_ago(iso: str | None) -> float | None:
    dt = parse_iso(iso)
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return max(0.0, (datetime.now(timezone.utc) - dt).total_seconds() / 3600.0)


def _blob(trend: dict[str, Any]) -> str:
    parts = [
        str(trend.get("label") or ""),
        str(trend.get("summary") or ""),
        str(trend.get("category") or ""),
        " ".join(str(k) for k in (trend.get("keywords") or [])),
    ]
    for it in trend.get("latest_items") or []:
        parts.append(str(it.get("title") or ""))
        parts.append(str(it.get("source") or ""))
    return " ".join(parts).lower()


def _extra_scores(conn: sqlite3.Connection, cluster_id: int) -> dict[str, float]:
    row = conn.execute(
        "SELECT growth_score, volume_score, diversity_score, recency_score FROM trend_clusters WHERE id = ?",
        (cluster_id,),
    ).fetchone()
    if not row:
        return {"growth_score": 50.0, "volume_score": 0.0, "diversity_score": 0.0, "recency_score": 50.0}
    return {
        "growth_score": float(row[0] or 50.0),
        "volume_score": float(row[1] or 0.0),
        "diversity_score": float(row[2] or 0.0),
        "recency_score": float(row[3] or 50.0),
    }


def _sector_fit(sector: str | None, trend: dict[str, Any]) -> float:
    if not sector:
        return 0.0
    s = sector.lower()
    cat = (trend.get("category") or "").lower()
    blob = _blob(trend)
    score = 0.0
    if cat and cat in s:
        score += 40.0
    for key, hints in _SECTOR_HINTS.items():
        if key in s:
            for h in hints:
                if h in cat or h in blob:
                    score += 18.0
            break
    # generic overlap
    for token in s.replace("/", " ").split():
        if len(token) > 3 and token in blob:
            score += 12.0
    return min(100.0, score)


def _competitor_hit(competitors: list[str], trend: dict[str, Any]) -> str | None:
    blob = _blob(trend)
    for name in competitors:
        n = name.strip().lower()
        if len(n) < 2:
            continue
        if n in blob:
            return name.strip()
    return None


def _why(
    kind: SignalKind,
    trend: dict[str, Any],
    scores: dict[str, float],
    *,
    brand_fit: float = 0.0,
    competitor: str | None = None,
) -> str:
    label = clean_display_title(trend.get("label") or "Tendance", max_len=72)
    ts = float(trend.get("trend_score") or 0)
    risk = float(trend.get("risk_score") or 0)
    g = scores["growth_score"]
    if kind == "emerging":
        return (
            f"«{label}» est jeune (volume encore bas) mais accélère (croissance {g:.0f}). "
            "Fenêtre courte pour se positionner."
        )
    if kind == "growing":
        return (
            f"«{label}» monte fort (pulse {ts:.0f}, croissance {g:.0f}) — "
            "à traiter dans la journée / 48 h."
        )
    if kind == "competitor_move":
        who = competitor or "un concurrent"
        return f"«{label}» mentionne {who}. Vérifier l’angle et riposter ou se différencier."
    if kind == "conversation_shift":
        return (
            f"«{label}» multiplie les sources ({trend.get('source_count')} sources) — "
            "la conversation s’élargit hors du cercle habituel."
        )
    if kind == "reputation":
        return (
            f"«{label}» porte un risque élevé ({risk:.0f}). "
            "Priorité monitoring / angle sûr, pas de jump-in agressif."
        )
    if kind == "brand_opportunity":
        return (
            f"«{label}» matche le brief (fit ~{brand_fit:.0f}). "
            "Transformer en angle campagne exécutable."
        )
    return (
        f"«{label}» faiblit (croissance {g:.0f}, pulse {ts:.0f}) — "
        "éviter d’investir comme si c’était encore émergent."
    )


def _do_next(kind: SignalKind) -> str:
    return {
        "emerging": "Brief créa light + tester 1 format court (Reels/TikTok) dans les 24–48 h.",
        "growing": "Valider fit marque, produire 1 angle safe + 1 angle local, pousser aujourd’hui.",
        "competitor_move": "Comparer leur message vs votre brief ; décider riposte, contournement ou silence.",
        "conversation_shift": "Mettre à jour le messaging catégorie ; briefer social + stratégie.",
        "reputation": "Escalader au responsable marque ; préparer réponse / abstention documentée.",
        "brand_opportunity": "Ouvrir le workflow Brief → recommandations et verrouiller un angle exécutable.",
        "fading": "Archiver comme insight evergreen ou laisser tomber — ne pas brûler le budget.",
    }[kind]


def classify_trend(
    trend: dict[str, Any],
    scores: dict[str, float],
    *,
    competitors: list[str],
    sector: str | None,
) -> list[tuple[SignalKind, float, dict[str, Any]]]:
    """Return ranked (kind, priority, extra) assignments for one trend."""
    ts = float(trend.get("trend_score") or 0)
    risk = float(trend.get("risk_score") or 0)
    g = scores["growth_score"]
    vol = scores["volume_score"]
    div = scores["diversity_score"]
    age_h = _hours_ago(trend.get("first_seen_at"))
    last_h = _hours_ago(trend.get("last_seen_at"))
    brand_fit = _sector_fit(sector, trend)
    competitor = _competitor_hit(competitors, trend)

    hits: list[tuple[SignalKind, float, dict[str, Any]]] = []

    if competitor:
        hits.append(("competitor_move", 95.0 + min(ts, 20) / 10, {"competitor": competitor}))

    if risk >= 65 and (g >= 45 or ts >= 45):
        hits.append(("reputation", 90.0 + risk / 20, {}))

    if brand_fit >= 45 and ts >= 40 and risk < 70:
        hits.append(("brand_opportunity", 80.0 + brand_fit / 10, {"brand_fit": brand_fit}))

    emerging = (
        g >= 62
        and vol < 45
        and ts >= 40
        and (age_h is None or age_h <= 36)
    )
    if emerging:
        hits.append(("emerging", 75.0 + g / 20, {}))

    if g >= 68 and ts >= 55 and not emerging:
        hits.append(("growing", 70.0 + g / 25, {}))
    elif g >= 60 and ts >= 48 and vol >= 40:
        hits.append(("growing", 65.0 + g / 30, {}))

    if div >= 55 and ts >= 42 and g >= 45:
        hits.append(("conversation_shift", 55.0 + div / 20, {}))

    fading = (g <= 40 and ts < 55) or (last_h is not None and last_h > 48 and g < 55)
    if fading and risk < 65:
        hits.append(("fading", 40.0 + (50 - min(g, 50)) / 10, {}))

    if not hits and ts >= 50:
        hits.append(("growing", 50.0 + ts / 50, {}))
    elif not hits:
        hits.append(("fading", 30.0, {}))

    # One primary per trend for the morning board (highest priority)
    hits.sort(key=lambda x: x[1], reverse=True)
    return hits[:1]


def build_morning_radar(conn: sqlite3.Connection) -> dict[str, Any]:
    brief_meta = get_latest_brief(conn)
    brief = get_full_brief(conn, brief_meta.get("id"))
    brand = brand_repo.get_active_brand(conn)
    competitors = list((brand or {}).get("competitors") or brief.get("competitors") or [])
    sector = (brand or {}).get("industry") or (brief.get("sector") if brief else None)
    client = (brand or {}).get("brand_name") or (brief.get("client_name") if brief else None)

    trends = get_trends_for_api(conn)
    buckets: dict[SignalKind, list[dict[str, Any]]] = {k: [] for k in SIGNAL_META}

    for trend in trends:
        cid = int(trend["id"])
        scores = _extra_scores(conn, cid)
        enriched = {
            **trend,
            "growth_score": round(scores["growth_score"], 1),
            "volume_score": round(scores["volume_score"], 1),
            "diversity_score": round(scores["diversity_score"], 1),
            "recency_score": round(scores["recency_score"], 1),
        }
        opportunity = build_opportunity_card(conn, enriched, brief, use_llm=False, brand=brand)
        assignments = classify_trend(
            enriched,
            scores,
            competitors=competitors,
            sector=sector,
        )
        for kind, priority, extra in assignments:
            brand_fit_hint = float(extra.get("brand_fit") or _sector_fit(sector, enriched))
            competitor = extra.get("competitor")
            # Prefer Brand Brain fit when present
            if opportunity.get("brand_fit"):
                brand_fit_hint = float(opportunity["brand_fit"].get("fit_percent") or brand_fit_hint)
            item = {
                **enriched,
                "signal_kind": kind,
                "priority": round(priority, 1),
                "why_it_matters": _why(
                    kind,
                    enriched,
                    scores,
                    brand_fit=brand_fit_hint,
                    competitor=competitor,
                ),
                "what_to_do": _do_next(kind),
                "brand_fit_hint": round(brand_fit_hint, 1) if brand_fit_hint else None,
                "competitor_matched": competitor,
                "meta": SIGNAL_META[kind],
                "opportunity": opportunity,
            }
            buckets[kind].append(item)

    for kind in buckets:
        buckets[kind].sort(key=lambda x: float(x.get("priority") or 0), reverse=True)

    sections = []
    for kind, meta in SIGNAL_META.items():
        items = buckets[kind]
        sections.append(
            {
                "kind": kind,
                "emoji": meta["emoji"],
                "label_fr": meta["label_fr"],
                "question": meta["question"],
                "count": len(items),
                "items": items[:8],
            }
        )

    actionable = sum(
        1
        for s in sections
        if s["kind"] in ("emerging", "growing", "brand_opportunity", "competitor_move", "reputation")
        and s["count"] > 0
    )
    headline_bits = []
    for s in sections:
        if s["count"] and s["kind"] in ("emerging", "growing", "brand_opportunity", "reputation", "competitor_move"):
            headline_bits.append(f"{s['emoji']} {s['count']} {s['label_fr'].lower()}")
    changed_line = (
        " · ".join(headline_bits[:4])
        if headline_bits
        else "Peu de mouvements nets depuis la dernière fenêtre — surveiller la prochaine collecte."
    )

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "headline": f"Ce qui a changé : {changed_line}",
        "question": "Qu’est-ce qui se passe maintenant, qu’est-ce qui compte pour la marque, et que faire ?",
        "brief_context": {
            "brief_id": brief.get("id"),
            "client_name": client,
            "sector": sector,
            "competitors": competitors,
            "has_brief": bool(brief.get("id")),
            "has_brand_brain": bool(brand),
            "brand_name": (brand or {}).get("brand_name"),
        },
        "summary": {
            "trends_scanned": len(trends),
            "actionable_buckets": actionable,
            "total_signals": sum(s["count"] for s in sections),
        },
        "competitive_alerts": build_competitive_alerts(conn),
        "sections": sections,
    }
