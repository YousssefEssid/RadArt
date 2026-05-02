import json
from pathlib import Path
from typing import Any

_BACKEND = Path(__file__).resolve().parent.parent
_MOCK_FILE = _BACKEND / "data" / "mock_social_trends.json"


def fetch_mock_social_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    status: list[dict[str, str]] = []
    try:
        raw = json.loads(_MOCK_FILE.read_text(encoding="utf-8"))
        for row in raw:
            items.append(
                {
                    "source": row.get("source", "Veille social"),
                    "platform": row.get("platform", "social"),
                    "title": row.get("title", ""),
                    "text": row.get("text", ""),
                    "url": row.get("url", ""),
                    "published_at": row.get("published_at"),
                    "engagement": int(row.get("engagement") or 0),
                    "category": row.get("category", "general"),
                    "raw_json": json.dumps(row, ensure_ascii=False),
                }
            )
        status.append({"source": "signaux_sociaux", "status": "ok", "detail": f"{len(items)} items"})
    except Exception as e:
        status.append({"source": "signaux_sociaux", "status": "error", "detail": str(e)[:200]})
    return items, status
