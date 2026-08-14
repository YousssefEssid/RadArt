"""Cross-source trend confirmation — defensible confidence, not fake volume."""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from app.collectors.base import SOURCE_CONFIDENCE, confidence_for
from app.core.database import fetch_all

# Independent source categories for diversity scoring
_CATEGORY_OF_PLATFORM = {
    "tiktok": "tiktok",
    "instagram": "instagram",
    "facebook": "facebook",
    "youtube": "youtube",
    "google_trends": "google_trends",
    "google_trends_serpapi": "google_trends",
    "google_news_rss": "news",
    "rss": "news",
    "gdelt": "news",
    "reddit": "reddit",
    "itunes": "music",
    "public_page": "web",
    "customer_owned": "customer",
    "search_discovery": "search_discovery",
}

_WEIGHTS = {
    "tiktok": 1,
    "instagram": 1,
    "facebook": 1,
    "google_trends": 2,
    "youtube": 2,
    "news": 1,
    "reddit": 1,
    "search_discovery": 1,
    "music": 1,
    "web": 1,
    "customer": 1,
}


def _parse_dt(val: str | None) -> datetime | None:
    if not val:
        return None
    try:
        return datetime.fromisoformat(str(val).replace("Z", "+00:00"))
    except Exception:
        return None


def confirm_topic(conn: sqlite3.Connection, topic: str, *, hours: int = 48) -> dict[str, Any]:
    """Scan media_items for a topic and compute cross-source confirmation."""
    needle = (topic or "").strip()
    if len(needle) < 2:
        raise ValueError("topic required")

    like = f"%{needle}%"
    rows = fetch_all(
        conn,
        """
        SELECT id, platform, source, source_method, provider, confidence, title, text, url,
               published_at, collected_at, engagement, country
        FROM media_items
        WHERE title LIKE ? OR IFNULL(text,'') LIKE ? OR IFNULL(keywords,'') LIKE ?
        ORDER BY collected_at DESC
        LIMIT 200
        """,
        (like, like, like),
    )

    now = datetime.now(timezone.utc)
    cut = now - timedelta(hours=hours)
    cats: dict[str, list[dict[str, Any]]] = defaultdict(list)
    first_seen: datetime | None = None
    last_seen: datetime | None = None
    confidences: list[float] = []
    methods: set[str] = set()

    for r in rows:
        dt = _parse_dt(r.get("published_at")) or _parse_dt(r.get("collected_at"))
        if dt and dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        if dt:
            first_seen = dt if first_seen is None or dt < first_seen else first_seen
            last_seen = dt if last_seen is None or dt > last_seen else last_seen
        if dt and dt < cut:
            # still count for first_seen but velocity uses recent
            pass
        plat = str(r.get("platform") or "unknown")
        method = str(r.get("source_method") or "")
        if method == "search_discovery" or plat == "search_discovery":
            # attribute to detected platform when possible from source label
            src = str(r.get("source") or "").lower()
            for p in ("tiktok", "instagram", "facebook"):
                if p in src or p in plat:
                    plat = p
                    break
            else:
                plat = plat if plat != "search_discovery" else "tiktok"
        cat = _CATEGORY_OF_PLATFORM.get(plat, plat)
        # recent bucket
        recent = bool(dt and dt >= cut) or dt is None
        if recent:
            cats[cat].append(r)
        methods.add(method or "unknown")
        conf = r.get("confidence")
        if conf is None:
            conf = confidence_for(method)
        confidences.append(float(conf))

    score = 0
    evidence: list[dict[str, Any]] = []
    for cat, items in cats.items():
        w = _WEIGHTS.get(cat, 1)
        score += w
        evidence.append(
            {
                "category": cat,
                "weight": w,
                "mentions": len(items),
                "sample_titles": [i.get("title") for i in items[:3]],
            }
        )

    diversity = len(cats)
    avg_conf = sum(confidences) / len(confidences) if confidences else 0.0
    # Tunisia relevance heuristic
    blob = " ".join(
        f"{r.get('title')} {r.get('text')} {r.get('country')}" for r in rows[:40]
    ).lower()
    local = 0.0
    for tok in ("tunisia", "tunisie", "tunis", "تونس", "tn"):
        if tok in blob:
            local = 1.0
            break

    # Confidence tier
    if score >= 6 and diversity >= 3 and avg_conf >= 0.6:
        tier = "HIGH"
    elif score >= 3 and diversity >= 2:
        tier = "MEDIUM"
    elif score >= 1:
        tier = "LOW"
    else:
        tier = "NONE"

    return {
        "topic": needle,
        "window_hours": hours,
        "confirmation_score": score,
        "tier": tier,
        "label": f"Emerging trend — {tier} CONFIDENCE" if tier != "NONE" else "No confirmation yet",
        "independent_source_categories": diversity,
        "categories": sorted(cats.keys()),
        "evidence": sorted(evidence, key=lambda e: -e["weight"]),
        "first_seen": first_seen.isoformat() if first_seen else None,
        "last_seen": last_seen.isoformat() if last_seen else None,
        "mention_count": len(rows),
        "mention_velocity_48h": sum(len(v) for v in cats.values()),
        "avg_source_confidence": round(avg_conf, 3),
        "source_methods": sorted(m for m in methods if m),
        "tunisia_relevance": local,
        "narrative": _narrative(needle, tier, cats, score),
        "source_confidence_table": SOURCE_CONFIDENCE,
    }


def _narrative(topic: str, tier: str, cats: dict[str, list], score: int) -> str:
    if tier == "NONE":
        return f"No cross-source signal yet for «{topic}»."
    names = ", ".join(sorted(cats.keys()))
    return (
        f"Seen across {names}. Confirmation score {score}. "
        f"Acceleration assessed over the last 48h — not a claim of exact platform volume."
    )
