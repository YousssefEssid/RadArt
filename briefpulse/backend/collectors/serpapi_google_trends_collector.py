"""
Google Trends via SerpApi (https://serpapi.com/google-trends-api).

Requires SERPAPI_API_KEY. Each successful request counts toward your SerpApi plan.
Default: 2 calls/run (RELATED_QUERIES + RELATED_TOPICS) to stay within free-tier budgets.
"""

from __future__ import annotations

import json
import time
from typing import Any
from urllib.parse import quote

import requests

from config import settings
from seed_sources import (
    SERPAPI_GOOGLE_TRENDS_SEEDS,
    SERPAPI_GOOGLE_TRENDS_TIMESERIES_QUERIES,
)
from utils.safety import request_headers
from utils.time_utils import utc_now_iso

SERPAPI_SEARCH_JSON = "https://serpapi.com/search.json"


def _engagement_from_extracted(v: Any, cap: int = 50_000) -> int:
    try:
        n = int(float(v))
    except (TypeError, ValueError):
        return 0
    return max(0, min(cap, n))


def _serpapi_trends(params: dict[str, Any]) -> tuple[dict[str, Any] | None, str | None]:
    key = (settings.serpapi_api_key or "").strip()
    if not key:
        return None, "no SERPAPI_API_KEY"
    p = {"engine": "google_trends", "api_key": key, **params}
    try:
        r = requests.get(SERPAPI_SEARCH_JSON, params=p, headers=request_headers(), timeout=45)
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        return None, str(e)[:300]

    meta = data.get("search_metadata") or {}
    if meta.get("status") != "Success":
        err = data.get("error") or meta.get("status") or "unknown"
        return None, str(err)[:300]
    return data, None


def _items_from_related_queries(
    data: dict[str, Any],
    seed_q: str,
    category: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    rq = data.get("related_queries") or {}
    for bucket in ("rising", "top"):
        for row in (rq.get(bucket) or [])[:15]:
            q = (row.get("query") or "").strip()
            if not q:
                continue
            ev = row.get("extracted_value")
            link = row.get("link") or f"https://trends.google.com/trends/explore?q={quote(q)}"
            raw = {"seed": seed_q, "bucket": bucket, "row": row}
            items.append(
                {
                    "source": "SerpApi · Google Trends",
                    "platform": "google_trends_serpapi",
                    "title": f"[{bucket}] {q}",
                    "text": f"Requête associée ({bucket}) pour « {seed_q} » — signal d’intérêt de recherche relatif.",
                    "url": link,
                    "published_at": utc_now_iso(),
                    "engagement": _engagement_from_extracted(ev),
                    "category": category,
                    "raw_json": json.dumps(raw, ensure_ascii=False)[:12000],
                }
            )
    return items


def _items_from_related_topics(
    data: dict[str, Any],
    seed_q: str,
    category: str,
) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    rt = data.get("related_topics") or {}
    for bucket in ("rising", "top"):
        for row in (rt.get(bucket) or [])[:15]:
            topic = row.get("topic") or {}
            title = (topic.get("title") or "").strip()
            if not title:
                continue
            ev = row.get("extracted_value")
            link = row.get("link") or (
                f"https://trends.google.com/trends/explore?q={quote(topic.get('value') or title)}"
            )
            raw = {"seed": seed_q, "bucket": bucket, "row": row}
            items.append(
                {
                    "source": "SerpApi · Google Trends",
                    "platform": "google_trends_serpapi",
                    "title": f"[topic:{bucket}] {title}",
                    "text": f"Sujet associé ({bucket}) pour « {seed_q} » — {topic.get('type') or 'Topic'}.",
                    "url": link,
                    "published_at": utc_now_iso(),
                    "engagement": _engagement_from_extracted(ev),
                    "category": category,
                    "raw_json": json.dumps(raw, ensure_ascii=False)[:12000],
                }
            )
    return items


def _items_from_timeseries(data: dict[str, Any], category: str) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    iot = data.get("interest_over_time") or {}
    averages = iot.get("averages") or []
    rows: list[dict[str, Any]] = []
    if averages:
        for row in averages[:8]:
            q = (row.get("query") or "").strip()
            if not q:
                continue
            rows.append({"query": q, "ev": row.get("value"), "raw": {"averages_row": row}, "suffix": "avg"})
    else:
        tl = iot.get("timeline_data") or []
        if tl:
            last = tl[-1]
            for v in (last.get("values") or [])[:8]:
                q = (v.get("query") or "").strip()
                if not q:
                    continue
                rows.append(
                    {
                        "query": q,
                        "ev": v.get("extracted_value"),
                        "raw": {"timeline_last": last.get("date"), "value": v},
                        "suffix": "last",
                    }
                )
    for r in rows:
        q = r["query"]
        raw = r["raw"]
        suf = r["suffix"]
        ev = r["ev"]
        label = "[12m avg]" if suf == "avg" else "[latest]"
        items.append(
            {
                "source": "SerpApi · Google Trends",
                "platform": "google_trends_serpapi",
                "title": f"{label} {q}",
                "text": f"Série temporelle Google Trends pour « {q} » (indice relatif; fenêtre: {suf}).",
                "url": f"https://trends.google.com/trends/explore?q={quote(q)}",
                "published_at": utc_now_iso(),
                "engagement": _engagement_from_extracted(ev, cap=100),
                "category": category,
                "raw_json": json.dumps(raw, ensure_ascii=False)[:8000],
            }
        )
    return items


def fetch_serpapi_google_trends_items() -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    items: list[dict[str, Any]] = []
    status: list[dict[str, str]] = []
    key = (settings.serpapi_api_key or "").strip()
    if not key:
        status.append({"source": "SerpApi Google Trends", "status": "skipped", "detail": "no SERPAPI_API_KEY"})
        return items, status

    budget = max(0, int(settings.serpapi_google_trends_max_requests_per_run or 0))
    if budget == 0:
        status.append(
            {"source": "SerpApi Google Trends", "status": "skipped", "detail": "max requests per run is 0"}
        )
        return items, status

    geo = (settings.serpapi_google_trends_geo or "").strip()
    hl = (settings.serpapi_google_trends_hl or "fr").strip()
    date = (settings.serpapi_google_trends_date or "today 3-m").strip()
    tz = settings.serpapi_google_trends_tz
    tz_param = str(tz) if tz is not None else None

    base_kw: dict[str, Any] = {
        "hl": hl,
        "date": date,
        "data_type": "RELATED_QUERIES",
    }
    if geo:
        base_kw["geo"] = geo
    if tz_param is not None and tz_param != "":
        base_kw["tz"] = tz_param

    seeds = SERPAPI_GOOGLE_TRENDS_SEEDS or [{"q": "Tunisie", "category": "general"}]

    for spec in seeds:
        if budget <= 0:
            break
        q = spec["q"]
        cat = spec.get("category", "general")
        data, err = _serpapi_trends({**base_kw, "q": q, "data_type": "RELATED_QUERIES"})
        budget -= 1
        if err or not data:
            status.append({"source": f"SerpApi Trends RQ:{q[:20]}", "status": "error", "detail": err or "empty"})
        else:
            chunk = _items_from_related_queries(data, q, cat)
            items.extend(chunk)
            status.append(
                {
                    "source": f"SerpApi Trends RQ:{q[:20]}",
                    "status": "ok",
                    "detail": f"{len(chunk)} items",
                }
            )
        time.sleep(0.55)

        if budget <= 0:
            break
        data, err = _serpapi_trends({**{k: v for k, v in base_kw.items() if k != "data_type"}, "q": q, "data_type": "RELATED_TOPICS"})
        budget -= 1
        if err or not data:
            status.append({"source": f"SerpApi Trends RT:{q[:20]}", "status": "error", "detail": err or "empty"})
        else:
            chunk = _items_from_related_topics(data, q, cat)
            items.extend(chunk)
            status.append(
                {
                    "source": f"SerpApi Trends RT:{q[:20]}",
                    "status": "ok",
                    "detail": f"{len(chunk)} items",
                }
            )
        time.sleep(0.55)

    if settings.serpapi_google_trends_include_timeseries and budget > 0:
        qs = [x.strip() for x in SERPAPI_GOOGLE_TRENDS_TIMESERIES_QUERIES if x.strip()][:5]
        if qs:
            combined = ",".join(qs)
            params = {
                "hl": hl,
                "date": date,
                "data_type": "TIMESERIES",
                "q": combined,
            }
            if geo:
                params["geo"] = geo
            if tz_param is not None and tz_param != "":
                params["tz"] = tz_param
            data, err = _serpapi_trends(params)
            budget -= 1
            if err or not data:
                status.append({"source": "SerpApi Trends TS", "status": "error", "detail": err or "empty"})
            else:
                items.extend(_items_from_timeseries(data, "general"))
                status.append({"source": "SerpApi Trends TS", "status": "ok", "detail": f"queries={len(qs)}"})

    return items, status
