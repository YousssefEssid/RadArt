from __future__ import annotations

import sqlite3
from collections import Counter, defaultdict
from typing import Any

from app.repositories import brand as brand_repo
from app.services.competitor_intel_service import (
    SECTOR_WATCHLIST,
    _filter_vs_client,
    _media_hits,
    _trend_hits,
    latest_brief_row,
    load_brief_row,
    resolve_competitor_names,
)

# Strategic themes we look for in competitor messaging
THEME_LEXICON: dict[str, tuple[str, ...]] = {
    "price": ("prix", "price", "pas cher", "promo", "discount", "bon plan", "€", "dt", "dinar", "offre"),
    "premium": ("premium", "luxe", "exclusive", "haut de gamme", "qualité", "prestige"),
    "convenience": ("convenience", "facile", "rapide", "pratiqu", "livraison", "instant", "simple", "quotidien"),
    "youth": ("jeune", "gen z", "étudiant", "tiktok", "meme", "campus", "youth"),
    "local": ("tunisie", "tunisia", "derja", "local", "tunisien", "maghreb"),
    "innovation": ("5g", "ia", "ai", "innovation", "tech", "digital", "app", "nouvelle"),
    "family": ("famille", "family", "parent", "enfants", "maison"),
    "sustainability": ("vert", "écologie", "sustainab", "recycl", "environnement"),
    "entertainment": ("musique", "sport", "festival", "série", "divertissement", "fun"),
    "trust": ("confiance", "sécurité", "fiable", "garanti", "service client"),
}

FORMAT_HINTS: dict[str, tuple[str, ...]] = {
    "short_video": ("tiktok", "reel", "reels", "short", "video"),
    "stories": ("story", "stories", "snap"),
    "static_post": ("instagram", "facebook", "post"),
    "news_pr": ("rss", "communiqué", "press", "web"),
    "charts_audio": ("itunes", "music", "chart", "spotify"),
}


def _blob_of(rows: list[dict[str, Any]]) -> str:
    parts: list[str] = []
    for r in rows:
        parts.append(str(r.get("title") or ""))
        parts.append(str(r.get("summary") or ""))
        parts.append(str(r.get("text") or ""))
        parts.append(str(r.get("category") or ""))
        parts.append(str(r.get("platform") or ""))
        parts.append(str(r.get("source") or ""))
    return " ".join(parts).lower()


def _theme_scores(blob: str) -> dict[str, float]:
    scores: dict[str, float] = {}
    for theme, kws in THEME_LEXICON.items():
        hits = sum(1 for k in kws if k in blob)
        if hits:
            scores[theme] = min(100.0, 25.0 + hits * 18.0)
    return scores


def _owned_themes(scores: dict[str, float], threshold: float = 45.0) -> list[str]:
    return [t for t, s in sorted(scores.items(), key=lambda x: -x[1]) if s >= threshold]


def _top_formats(media: list[dict[str, Any]]) -> list[dict[str, Any]]:
    counts: Counter[str] = Counter()
    for m in media:
        plat = str(m.get("platform") or "").lower()
        src = str(m.get("source") or "").lower()
        title = str(m.get("title") or "").lower()
        blob = f"{plat} {src} {title}"
        matched = False
        for fmt, hints in FORMAT_HINTS.items():
            if any(h in blob for h in hints):
                counts[fmt] += 1
                matched = True
                break
        if not matched:
            counts[plat or "other"] += 1
    total = sum(counts.values()) or 1
    return [
        {"format": k, "share": round(100.0 * v / total, 1), "count": v}
        for k, v in counts.most_common(5)
    ]


def _audience_guess(themes: list[str], categories: list[str]) -> str:
    cats = " ".join(categories).lower()
    if "youth" in themes or "youth" in cats:
        return "18–30 · digital / campus / short-form"
    if "family" in themes:
        return "25–45 · familles & foyer"
    if "premium" in themes:
        return "28–45 · aspirational / urban"
    if "price" in themes:
        return "18–40 · value-seekers"
    if "economy" in cats:
        return "25–50 · décideurs & pouvoir d’achat"
    return "18–40 · audience média large"


def _silent_themes(all_themes: list[str], owned: list[str]) -> list[str]:
    return [t for t in all_themes if t not in owned]


def _early_adoptions(trends: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out = []
    for t in trends[:4]:
        out.append(
            {
                "label": t.get("label"),
                "trend_score": t.get("trend_score"),
                "note": "Signal déjà lié à ce concurrent dans les clusters — possible early adopt.",
            }
        )
    return out


def _build_dossier(
    name: str,
    media: list[dict[str, Any]],
    trends: list[dict[str, Any]],
    source_tag: str,
) -> dict[str, Any]:
    blob = _blob_of(media + trends)
    theme_scores = _theme_scores(blob)
    owned = _owned_themes(theme_scores)
    cats = [str(m.get("category") or "") for m in media if m.get("category")]
    formats = _top_formats(media)
    talking = [str(m.get("title") or "")[:120] for m in media[:5] if m.get("title")]
    campaigns = [
        {
            "title": m.get("title"),
            "platform": m.get("platform"),
            "engagement": m.get("engagement") or 0,
            "url": m.get("url"),
        }
        for m in sorted(media, key=lambda x: int(x.get("engagement") or 0), reverse=True)[:4]
    ]
    all_theme_keys = list(THEME_LEXICON.keys())
    silent = _silent_themes(all_theme_keys, owned)[:5]

    return {
        "name": name,
        "source_tag": source_tag,
        "signal_count": len(media),
        "talking_about": talking,
        "campaigns_gaining_traction": campaigns,
        "themes_owned": owned[:5],
        "theme_scores": {k: round(v, 1) for k, v in sorted(theme_scores.items(), key=lambda x: -x[1])[:8]},
        "audience_attracted": _audience_guess(owned, cats),
        "content_formats": formats,
        "where_silent": silent,
        "trends_adopted_before_us": _early_adoptions(trends),
        "related_clusters": trends[:5],
        "recent_signals": media[:8],
        "notes": (
            "War Room dossier from indexed signals — themes inferred from language & formats."
            if media or trends
            else "Peu de signaux indexés pour ce nom — élargir la collecte ou vérifier l’orthographe."
        ),
    }


def _opportunity_gaps(
    dossiers: list[dict[str, Any]],
    brand_name: str | None,
) -> list[dict[str, Any]]:
    """
    Find themes nobody (or almost nobody) owns → strategic white space.
    Classic example: A owns price, B owns premium, nobody owns convenience.
    """
    ownership: dict[str, list[str]] = defaultdict(list)
    for d in dossiers:
        for theme in d.get("themes_owned") or []:
            ownership[theme].append(d["name"])

    gaps: list[dict[str, Any]] = []
    for theme in THEME_LEXICON:
        owners = ownership.get(theme, [])
        if len(owners) == 0:
            gaps.append(
                {
                    "theme": theme,
                    "owned_by": [],
                    "gap_type": "white_space",
                    "headline": f"Nobody owns “{theme}”",
                    "opportunity": (
                        f"Opportunity detected → {theme.capitalize()} positioning"
                        + (f" for {brand_name}" if brand_name else "")
                        + "."
                    ),
                    "why": "No tracked competitor is communicating strongly on this theme in current signals.",
                    "priority": 95,
                }
            )
        elif len(owners) == 1 and len(dossiers) >= 2:
            gaps.append(
                {
                    "theme": theme,
                    "owned_by": owners,
                    "gap_type": "contested_opening",
                    "headline": f"Only {owners[0]} leans on “{theme}”",
                    "opportunity": (
                        f"Flank or differentiate: claim a sharper {theme} angle"
                        + (f" for {brand_name}" if brand_name else "")
                        + " before the category piles on."
                    ),
                    "why": f"Single-player ownership by {owners[0]} — room for a counter-narrative.",
                    "priority": 70,
                }
            )

    # Narrative summary like the user's example
    price_owners = ownership.get("price", [])
    premium_owners = ownership.get("premium", [])
    convenience_owners = ownership.get("convenience", [])
    if price_owners and premium_owners and not convenience_owners:
        gaps.insert(
            0,
            {
                "theme": "convenience",
                "owned_by": [],
                "gap_type": "classic_gap",
                "headline": "Price vs Premium — Convenience is open",
                "opportunity": "Opportunity detected → Convenience positioning.",
                "why": (
                    f"{', '.join(price_owners)} lean on “price”; "
                    f"{', '.join(premium_owners)} lean on “premium”; "
                    "neither is communicating around “convenience”."
                ),
                "priority": 100,
            },
        )

    # de-dupe by theme keeping highest priority
    best: dict[str, dict[str, Any]] = {}
    for g in gaps:
        t = g["theme"]
        if t not in best or g["priority"] > best[t]["priority"]:
            best[t] = g
    return sorted(best.values(), key=lambda x: -x["priority"])[:8]


def _map_theme_board(dossiers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    board = []
    for theme in THEME_LEXICON:
        owners = [d["name"] for d in dossiers if theme in (d.get("themes_owned") or [])]
        board.append(
            {
                "theme": theme,
                "owners": owners,
                "status": "owned" if owners else "open",
            }
        )
    return board


def build_war_room(conn: sqlite3.Connection) -> dict[str, Any]:
    brand = brand_repo.get_active_brand(conn)
    brief_row = latest_brief_row(conn)
    brief_full = load_brief_row(conn, int(brief_row["id"])) if brief_row else None

    names: list[str] = []
    source_mode = "none"
    client_name = None
    sector = None

    if brand:
        names = list(brand.get("competitors") or [])
        client_name = brand.get("brand_name")
        sector = brand.get("industry")
        source_mode = "brand_brain"
        if not names and sector:
            key = (sector or "").strip().lower()
            for sk, brands in SECTOR_WATCHLIST.items():
                if sk in key or key in sk:
                    names = _filter_vs_client(brands[:5], client_name)
                    source_mode = "brand_brain_sector"
                    break

    if not names and brief_full:
        names, source_mode = resolve_competitor_names(brief_full)
        client_name = client_name or brief_full.get("client_name")
        sector = sector or brief_full.get("sector")

    if not names:
        return {
            "title": "Competitor War Room",
            "subtitle": "Strategic intelligence — not just monitoring",
            "brand": client_name,
            "sector": sector,
            "competitor_source": "none",
            "brief_id": brief_row["id"] if brief_row else None,
            "competitors": [],
            "theme_board": [],
            "opportunity_gaps": [],
            "dossiers": [],
            "summary": {
                "competitor_count": 0,
                "open_themes": 0,
                "gap_count": 0,
                "signals_indexed": 0,
            },
            "playbook": "Add competitors in Brand Brain (or a client brief) to open the War Room.",
        }

    dossiers: list[dict[str, Any]] = []
    for name in names[:8]:
        media = _media_hits(conn, name, 14)
        if len(media) < 3 and " " in name:
            first = name.split()[0]
            if len(first) >= 4:
                media = (media + _media_hits(conn, first, 10))[:14]
        trends = _trend_hits(conn, name, 6)
        dossiers.append(_build_dossier(name, media, trends, source_mode))

    gaps = _opportunity_gaps(dossiers, client_name)
    board = _map_theme_board(dossiers)

    return {
        "title": "Competitor War Room",
        "subtitle": "Strategic intelligence — not just monitoring",
        "brand": client_name,
        "sector": sector,
        "competitor_source": source_mode,
        "brief_id": brief_row["id"] if brief_row else None,
        "competitors": names,
        "theme_board": board,
        "opportunity_gaps": gaps,
        "dossiers": dossiers,
        "summary": {
            "competitor_count": len(dossiers),
            "open_themes": sum(1 for t in board if t["status"] == "open"),
            "gap_count": len(gaps),
            "signals_indexed": sum(d["signal_count"] for d in dossiers),
        },
        "playbook": (
            gaps[0]["opportunity"]
            if gaps
            else "Keep collecting — theme ownership will sharpen as signals accumulate."
        ),
    }
