from __future__ import annotations

import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from app.repositories import brand as brand_repo
from app.services.competitor_intel_service import (
    SECTOR_WATCHLIST,
    _filter_vs_client,
    _media_hits,
    latest_brief_row,
    load_brief_row,
    resolve_competitor_names,
)
from app.services.war_room_service import THEME_LEXICON, _theme_scores
from app.utils.time_utils import parse_iso

# Extra campaign / seasonal themes for alerts
ALERT_THEME_LEXICON: dict[str, tuple[str, ...]] = {
    **THEME_LEXICON,
    "back_to_school": (
        "back to school",
        "rentrée",
        "rentree",
        "école",
        "ecole",
        "étudiant",
        "etudiant",
        "bac",
        "fourniture",
        "cartable",
        "campus",
        "school",
    ),
    "ramadan": ("ramadan", "ftour", "iftar", "souhour"),
    "summer": ("summer", "été", "ete", "canicule", "plage", "vacances"),
}

DIFF_ANGLES: dict[str, str] = {
    "back_to_school": (
        "Respond with a differentiated “Parents vs Students” angle rather than "
        "competing directly on promotions."
    ),
    "price": (
        "Don’t race on discounts — own convenience / everyday ease, or a sharper local humor angle."
    ),
    "premium": (
        "Avoid copycat prestige. Differentiate with accessible Tunisian warmth or Gen Z wit."
    ),
    "youth": (
        "Don’t mirror their meme spam — lead with a community / creator POV unique to your Brand DNA."
    ),
    "summer": (
        "Skip generic heatwave promos — own a ritual moment (after work, beach bag, night drive)."
    ),
    "innovation": (
        "Don’t chase feature lists — humanize the benefit in derja-friendly proof moments."
    ),
    "convenience": (
        "Double down: competitors are quiet here — own “moins de friction, plus de quotidien”."
    ),
}


def _item_dt(row: dict[str, Any]) -> datetime | None:
    for key in ("published_at", "collected_at"):
        dt = parse_iso(row.get(key))
        if dt:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    return None


def _resolve_competitors(conn: sqlite3.Connection) -> tuple[list[str], str | None, str | None]:
    brand = brand_repo.get_active_brand(conn)
    client = None
    sector = None
    names: list[str] = []
    if brand:
        client = brand.get("brand_name")
        sector = brand.get("industry")
        names = list(brand.get("competitors") or [])
        if not names and sector:
            key = (sector or "").lower()
            for sk, brands in SECTOR_WATCHLIST.items():
                if sk in key or key in sk:
                    names = _filter_vs_client(brands[:4], client)
                    break
    if not names:
        brief_row = latest_brief_row(conn)
        if brief_row:
            full = load_brief_row(conn, int(brief_row["id"]))
            if full:
                names, _ = resolve_competitor_names(full)
                client = client or full.get("client_name")
                sector = sector or full.get("sector")
    if not names:
        names = ["Coca-Cola", "Fanta", "Apla"]
        client = client or "Your brand"
    return names[:6], client, sector


def _dominant_theme(blob: str) -> str | None:
    scores = {}
    for theme, kws in ALERT_THEME_LEXICON.items():
        hits = sum(1 for k in kws if k in blob)
        if hits:
            scores[theme] = hits
    if not scores:
        return None
    return max(scores.items(), key=lambda x: x[1])[0]


def _theme_label(theme: str) -> str:
    return {
        "back_to_school": "Back to School",
        "price": "Price / promos",
        "premium": "Premium",
        "youth": "Youth / Gen Z",
        "summer": "Summer",
        "convenience": "Convenience",
        "innovation": "Innovation",
        "family": "Family",
        "local": "Local / Tunisia",
        "entertainment": "Entertainment",
        "ramadan": "Ramadan",
        "trust": "Trust",
        "sustainability": "Sustainability",
    }.get(theme, theme.replace("_", " ").title())


def _response_angle(theme: str, brand_name: str | None) -> str:
    base = DIFF_ANGLES.get(theme) or (
        f"Respond with a differentiated angle on “{_theme_label(theme)}” — "
        "don’t copy their creative; own a white-space POV from your Brand DNA."
    )
    if brand_name:
        return f"For {brand_name}: {base}"
    return base


def _acceleration_pct(recent: int, previous: int) -> float:
    if previous <= 0:
        return 100.0 if recent >= 3 else float(recent * 25)
    return round(100.0 * (recent - previous) / previous, 1)


def _build_alert(
    *,
    competitor: str,
    theme: str,
    recent_count: int,
    previous_count: int,
    window_hours: int,
    brand_name: str | None,
    sample_titles: list[str],
) -> dict[str, Any]:
    accel = _acceleration_pct(recent_count, previous_count)
    label = _theme_label(theme)
    severity = "high" if recent_count >= 8 or accel >= 40 else "medium"
    return {
        "id": f"{competitor.lower().replace(' ', '-')}-{theme}",
        "type": "competitor_movement",
        "severity": severity,
        "emoji": "🚨",
        "headline": "Competitor movement detected",
        "competitor": competitor,
        "theme": theme,
        "theme_label": label,
        "content_count": recent_count,
        "window_hours": window_hours,
        "acceleration_pct": accel,
        "summary": (
            f"Your competitor launched {recent_count} pieces of content around “{label}” "
            f"over the past {window_hours} hours."
        ),
        "acceleration_line": (
            f"Conversation around the theme is accelerating {accel:+.0f}%."
            if accel != 0
            else "Conversation volume is building on this theme."
        ),
        "recommendation": _response_angle(theme, brand_name),
        "sample_titles": sample_titles[:4],
        "cta": "Open War Room",
        "cta_path": "/concurrents",
    }


def _demo_alerts(competitors: list[str], brand_name: str | None, sector: str | None) -> list[dict[str, Any]]:
    """When live signals are thin, still show dependency-grade alert UX."""
    if not competitors:
        return []
    lead = competitors[0]
    sector_l = (sector or "").lower()
    theme = "back_to_school"
    if any(x in sector_l for x in ("beverage", "drink", "food")):
        theme = "back_to_school"
    elif "telecom" in sector_l:
        theme = "youth"
    return [
        _build_alert(
            competitor=lead,
            theme=theme,
            recent_count=12,
            previous_count=9,
            window_hours=48,
            brand_name=brand_name,
            sample_titles=[
                f"{lead} — push “{_theme_label(theme)}” wave (demo signal)",
                f"{lead} — short-form pack around {_theme_label(theme)}",
            ],
        )
    ]


def build_competitive_alerts(
    conn: sqlite3.Connection,
    *,
    window_hours: int = 48,
) -> dict[str, Any]:
    names, brand_name, sector = _resolve_competitors(conn)
    now = datetime.now(timezone.utc)
    recent_cut = now - timedelta(hours=window_hours)
    prev_cut = now - timedelta(hours=window_hours * 2)

    # competitor -> theme -> {recent: [rows], previous: [rows]}
    buckets: dict[str, dict[str, dict[str, list[dict[str, Any]]]]] = defaultdict(
        lambda: defaultdict(lambda: {"recent": [], "previous": []})
    )

    for name in names:
        rows = _media_hits(conn, name, 80)
        # also pull text field if available via broader query
        for row in rows:
            dt = _item_dt(row)
            if not dt:
                # undated → treat as recent-ish for demo density
                bucket = "recent"
            elif dt >= recent_cut:
                bucket = "recent"
            elif dt >= prev_cut:
                bucket = "previous"
            else:
                continue
            blob = (
                f"{row.get('title') or ''} {row.get('text') or ''} "
                f"{row.get('category') or ''} {row.get('source') or ''}"
            ).lower()
            theme = _dominant_theme(blob) or (row.get("category") or "general")
            if theme == "general":
                # try war-room scores
                scored = _theme_scores(blob)
                theme = max(scored, key=scored.get) if scored else "youth"
            buckets[name][theme][bucket].append(row)

    alerts: list[dict[str, Any]] = []
    for competitor, themes in buckets.items():
        for theme, parts in themes.items():
            recent = parts["recent"]
            previous = parts["previous"]
            if len(recent) < 3:
                continue
            accel = _acceleration_pct(len(recent), len(previous))
            if len(recent) < 5 and accel < 15:
                continue
            alerts.append(
                _build_alert(
                    competitor=competitor,
                    theme=theme,
                    recent_count=len(recent),
                    previous_count=len(previous),
                    window_hours=window_hours,
                    brand_name=brand_name,
                    sample_titles=[str(r.get("title") or "") for r in recent if r.get("title")],
                )
            )

    alerts.sort(
        key=lambda a: (0 if a["severity"] == "high" else 1, -a["content_count"], -a["acceleration_pct"])
    )

    sourced = "live_signals"
    if not alerts:
        alerts = _demo_alerts(names, brand_name, sector)
        sourced = "demo_seed"

    return {
        "generated_at": now.isoformat(),
        "brand": brand_name,
        "competitors_watched": names,
        "window_hours": window_hours,
        "count": len(alerts),
        "source": sourced,
        "alerts": alerts[:10],
        "dependency_line": (
            "RadArt watches competitors so your team doesn’t have to — "
            "move differently, not louder."
        ),
    }
