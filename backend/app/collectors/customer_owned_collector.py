"""Customer-owned signal ingest — legal path for Meta/TikTok/agency exports."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_CUSTOMER_DIR = Path(__file__).resolve().parents[2] / "data" / "customer_owned"


def customer_owned_dir() -> Path:
    _CUSTOMER_DIR.mkdir(parents=True, exist_ok=True)
    return _CUSTOMER_DIR


def _normalize_row(raw: dict[str, Any], default_platform: str = "customer_owned") -> dict[str, Any] | None:
    title = str(raw.get("title") or raw.get("caption") or raw.get("text") or "").strip()
    if not title:
        return None
    text = str(raw.get("text") or raw.get("caption") or raw.get("description") or "")[:4000]
    platform = str(raw.get("platform") or default_platform).strip().lower() or default_platform
    source = str(raw.get("source") or raw.get("account") or raw.get("page") or "Customer export")
    return {
        "source": source[:200],
        "platform": platform[:64],
        "title": title[:500],
        "text": text,
        "url": raw.get("url") or raw.get("permalink") or "",
        "published_at": raw.get("published_at") or raw.get("created_at") or raw.get("timestamp"),
        "engagement": int(raw.get("engagement") or raw.get("likes") or raw.get("views") or 0),
        "category": raw.get("category") or "general",
        "raw_json": raw,
    }


def fetch_customer_owned_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    status: list[dict[str, str]] = []
    folder = customer_owned_dir()
    files = sorted(folder.glob("*.json"))
    if not files:
        status.append(
            {
                "source": "Customer-owned data",
                "status": "skipped",
                "detail": "no JSON files in backend/data/customer_owned/",
            }
        )
        return items, status

    loaded = 0
    for path in files:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            rows = data if isinstance(data, list) else data.get("items") or data.get("posts") or []
            if not isinstance(rows, list):
                continue
            for row in rows:
                if not isinstance(row, dict):
                    continue
                norm = _normalize_row(row)
                if norm:
                    items.append(norm)
                    loaded += 1
        except Exception as e:
            status.append(
                {
                    "source": f"Customer-owned:{path.name}",
                    "status": "error",
                    "detail": str(e)[:180],
                }
            )
    status.append(
        {
            "source": "Customer-owned data",
            "status": "ok" if loaded else "skipped",
            "detail": f"{loaded} items from {len(files)} file(s)",
        }
    )
    return items, status


def save_customer_owned_payload(payload: list[dict[str, Any]] | dict[str, Any], filename: str = "upload.json") -> int:
    """Persist an upload for the next collection cycle; returns normalized count."""
    folder = customer_owned_dir()
    safe = "".join(c for c in filename if c.isalnum() or c in ("-", "_", ".")) or "upload.json"
    if not safe.endswith(".json"):
        safe += ".json"
    path = folder / safe
    rows = payload if isinstance(payload, list) else payload.get("items") or payload.get("posts") or []
    if not isinstance(rows, list):
        raise ValueError("Payload must be a list of items or {items:[...]}")
    normalized = []
    for row in rows:
        if isinstance(row, dict):
            n = _normalize_row(row)
            if n:
                # store original-ish for re-fetch
                normalized.append(
                    {
                        "title": n["title"],
                        "text": n["text"],
                        "platform": n["platform"],
                        "source": n["source"],
                        "url": n["url"],
                        "published_at": n["published_at"],
                        "engagement": n["engagement"],
                        "category": n["category"],
                    }
                )
    path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2), encoding="utf-8")
    return len(normalized)
