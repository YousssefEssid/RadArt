from __future__ import annotations

import json
import re
import sqlite3
from typing import Any

from db import get_connection
from services.llm_service import generate_json
from utils.time_utils import utc_now_iso


def _extract_competitor_names(raw: str) -> list[str]:
    """Tente d'extraire des noms de marques / concurrents mentionnés dans le brief (règles, pas d'API)."""
    found: list[str] = []
    for m in re.finditer(
        r"(?:^|\n)\s*[-*•]?\s*(?:concurrent|concurrente|concurrents|concurrentes|competitor|competitors|vs\.?|versus)\s*[:#-]?\s*(.+?)(?=\n|$)",
        raw,
        re.I | re.MULTILINE,
    ):
        chunk = m.group(1).strip()
        for part in re.split(r"[,;]|\s+et\s+|\s+and\s+|\n", chunk):
            p = re.sub(r"^[-*•\s]+", "", part).strip()
            if 2 <= len(p) <= 100 and not p.lower().startswith("http"):
                found.append(p)
    for m in re.finditer(
        r"(?:concurrents?|competitors?)\s*(?:\(|:)\s*([^\n)]+)\)?",
        raw,
        re.I,
    ):
        chunk = m.group(1).strip()
        for part in re.split(r"[,;]", chunk):
            p = part.strip()
            if 2 <= len(p) <= 100:
                found.append(p)
    seen: set[str] = set()
    out: list[str] = []
    for n in found:
        k = n.lower()
        if k in seen:
            continue
        seen.add(k)
        out.append(n)
    return out[:12]


def _rule_parse(raw: str, client_name: str | None) -> dict[str, Any]:
    low = raw.lower()
    sector = "general"
    if any(x in low for x in ("drink", "beverage", "boisson", "café", "juice")):
        sector = "food/beverage"
    elif any(x in low for x in ("bank", "banque", "finance", "financement")):
        sector = "banking/finance"
    elif any(x in low for x in ("telecom", "télécom", "mobile", "operator")):
        sector = "telecom"
    elif any(x in low for x in ("beauty", "skincare", "cosmetic")):
        sector = "beauty/skincare"
    elif any(x in low for x in ("retail", "magasin", "shop")):
        sector = "retail"
    elif any(x in low for x in ("tourism", "tourisme", "hotel", "travel")):
        sector = "tourism"

    target = "general audience"
    if any(x in low for x in ("student", "étudiant", "gen z", "young adult", "jeunes")):
        target = "students / Gen Z"

    objective = "awareness"
    if "engagement" in low:
        objective = "engagement"
    if any(x in low for x in ("sales", "conversion", "vente")):
        objective = "conversion"

    tone = "balanced"
    if any(x in low for x in ("humor", "humour", "funny", "drôle")):
        tone = "humorous"
    if "premium" in low:
        tone = "premium"

    constraints = ""
    m = re.search(r"(?:avoid|éviter)\s+(.+?)(?:\.|$)", raw, re.I | re.S)
    if m:
        constraints = m.group(1).strip()[:500]
    elif "avoid" in low or "éviter" in low:
        constraints = "see brief"

    return {
        "client_name": client_name,
        "sector": sector,
        "target": target,
        "objective": objective,
        "tone": tone,
        "constraints": constraints,
        "period": "",
        "competitors": _extract_competitor_names(raw),
    }


def parse_brief_llm(raw: str, client_name: str | None) -> dict[str, Any]:
    fb = _rule_parse(raw, client_name)
    from config import settings

    if not (settings.openai_api_key or "").strip() and not (settings.gemini_api_key or "").strip():
        return fb
    prompt = f"""Extract fields as JSON keys: sector, target, objective, tone, constraints, period, competitors.
competitors: array of strings, brand/company names of competitors or comparators named in the brief; if none, [].
Client name: {client_name or ""}
Brief:
{raw[:4000]}
Use short strings. Constraints: merge avoidance phrases."""
    out = generate_json(prompt, fb)
    out["client_name"] = client_name or out.get("client_name")
    for k in ("sector", "target", "objective", "tone", "constraints"):
        if not out.get(k):
            out[k] = fb.get(k, "")
    out["competitors"] = _normalize_competitors_list(out.get("competitors"), fb.get("competitors", []))
    return out


def _normalize_competitors_list(val: Any, fallback: list[str]) -> list[str]:
    if isinstance(val, str):
        val = [x.strip() for x in re.split(r"[,;\n]", val) if x.strip()]
    if not isinstance(val, list):
        val = list(fallback) if fallback else []
    out: list[str] = []
    seen: set[str] = set()
    for x in val:
        if not isinstance(x, str):
            continue
        s = x.strip()[:120]
        if not s or s.lower() in seen:
            continue
        seen.add(s.lower())
        out.append(s)
    if not out and fallback:
        for s in fallback:
            if s.lower() not in seen:
                seen.add(s.lower())
                out.append(s)
    return out[:15]


def save_brief(conn: sqlite3.Connection, parsed: dict[str, Any], raw_brief: str) -> int:
    ts = utc_now_iso()
    comp = json.dumps(parsed.get("competitors") or [], ensure_ascii=False)
    cur = conn.execute(
        """
        INSERT INTO client_briefs (
          client_name, sector, target, objective, tone, constraints, raw_brief, created_at, competitors_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            parsed.get("client_name"),
            parsed.get("sector"),
            parsed.get("target"),
            parsed.get("objective"),
            parsed.get("tone"),
            parsed.get("constraints"),
            raw_brief,
            ts,
            comp,
        ),
    )
    return int(cur.lastrowid)


def analyze_and_store(client_name: str | None, raw_brief: str) -> tuple[int, dict[str, Any]]:
    parsed = parse_brief_llm(raw_brief, client_name)
    with get_connection() as conn:
        bid = save_brief(conn, parsed, raw_brief)
    return bid, parsed
