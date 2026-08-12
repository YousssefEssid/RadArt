from __future__ import annotations

import json
import re
import sqlite3
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

import numpy as np
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer

from app.core.database import get_connection
from app.services.scoring_service import (
    cluster_recency_score,
    growth_score_from_counts,
    normalize,
    risk_from_text,
    trend_composite,
)
from app.services.social_signals import signals_to_cluster_text
from app.utils.time_utils import parse_iso

WINDOW_HOURS = 72


def _item_time(row: dict[str, Any]) -> datetime | None:
    for key in ("published_at", "collected_at"):
        dt = parse_iso(row.get(key))
        if dt:
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
    return None


def load_recent_items(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=WINDOW_HOURS)
    rows = conn.execute(
        "SELECT * FROM media_items ORDER BY id ASC",
    ).fetchall()
    out = []
    for r in rows:
        d = dict(r)
        t = _item_time(d)
        if t and t >= cutoff:
            out.append(d)
    if not out:
        rows = conn.execute("SELECT * FROM media_items ORDER BY id DESC LIMIT 200").fetchall()
        out = [dict(r) for r in rows]
    return out


def _text_blob(row: dict[str, Any]) -> str:
    base = f"{row.get('title') or ''} {row.get('text') or ''}".strip()
    extra = ""
    try:
        sig = json.loads(row.get("entities") or "{}")
        if isinstance(sig, dict):
            extra = signals_to_cluster_text(sig)
    except json.JSONDecodeError:
        pass
    return f"{base} {extra}".strip()


def _keyword_fallback(items: list[dict[str, Any]]) -> list[list[int]]:
    clusters: dict[str, list[int]] = defaultdict(list)
    for i, row in enumerate(items):
        kws = []
        try:
            kws = json.loads(row.get("keywords") or "[]")
        except json.JSONDecodeError:
            pass
        key = kws[0] if kws else re.sub(r"\W+", "", (row.get("title") or "x")[:24].lower()) or "misc"
        clusters[key].append(i)
    return list(clusters.values())


def _run_trend_detection_impl(conn: sqlite3.Connection) -> int:
    conn.execute("DELETE FROM recommendations")
    conn.execute("DELETE FROM trend_clusters")
    conn.execute("UPDATE media_items SET cluster_id = NULL")

    items = load_recent_items(conn)
    if len(items) < 2:
        return 0

    texts = [_text_blob(r) for r in items]
    n_items = len(items)
    n_clusters = min(8, max(2, n_items // 4))
    n_clusters = min(n_clusters, n_items)

    labels: np.ndarray
    if n_items < 4:
        groups = _keyword_fallback(items)
        labels = np.zeros(n_items, dtype=int)
        gid = 0
        for g in groups:
            for idx in g:
                labels[idx] = gid
            gid += 1
    else:
        vectorizer = TfidfVectorizer(max_features=1500, ngram_range=(1, 2), min_df=1)
        X = vectorizer.fit_transform(texts)
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        labels = km.fit_predict(X)

    by_cluster: dict[int, list[int]] = defaultdict(list)
    for idx, lab in enumerate(labels.tolist()):
        by_cluster[int(lab)].append(idx)

    now = datetime.now(timezone.utc)
    max_size = max(len(v) for v in by_cluster.values())
    max_eng = max(sum(int(items[i].get("engagement") or 0) for i in v) for v in by_cluster.values()) or 1
    max_div = max(len({items[i].get("source") for i in v}) for v in by_cluster.values()) or 1

    from app.utils.time_utils import utc_now_iso

    for _cid, indices in by_cluster.items():
        cluster_items = [items[i] for i in indices]
        combined = " ".join(_text_blob(x) for x in cluster_items)
        try:
            all_kw: list[str] = []
            for x in cluster_items:
                all_kw.extend(json.loads(x.get("keywords") or "[]"))
        except json.JSONDecodeError:
            all_kw = []
        top_kw = list(dict.fromkeys(all_kw))[:6]
        label = ", ".join(top_kw[:3]) if top_kw else (cluster_items[0].get("title") or "Trend")[:80]
        summary = (cluster_items[0].get("text") or cluster_items[0].get("title") or "")[:280]

        vol = normalize(float(len(indices)), float(max_size))
        eng_sum = sum(int(x.get("engagement") or 0) for x in cluster_items)
        eng = normalize(float(eng_sum), float(max_eng))
        div = normalize(float(len({x.get("source") for x in cluster_items})), float(max_div))

        times = [_item_time(x) for x in cluster_items]
        times = [t for t in times if t]
        latest = max(times) if times else None
        rec = cluster_recency_score(latest)

        last24 = sum(1 for t in times if t and (now - t) <= timedelta(hours=24))
        prev24 = sum(
            1 for t in times if t and timedelta(hours=24) < (now - t) <= timedelta(hours=48)
        )
        growth = growth_score_from_counts(last24, prev24)

        risk = risk_from_text(combined)
        tscore = trend_composite(vol, growth, eng, div, rec)

        ts = utc_now_iso()
        cur = conn.execute(
            """
            INSERT INTO trend_clusters (
              label, summary, keywords, category, volume_score, growth_score,
              engagement_score, diversity_score, recency_score, trend_score, risk_score,
              created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                label[:500],
                summary,
                json.dumps(top_kw, ensure_ascii=False),
                cluster_items[0].get("category") or "general",
                vol,
                growth,
                eng,
                div,
                rec,
                tscore,
                risk,
                ts,
                ts,
            ),
        )
        new_id = int(cur.lastrowid)
        for i in indices:
            conn.execute(
                "UPDATE media_items SET cluster_id = ? WHERE id = ?",
                (new_id, items[i]["id"]),
            )

    return len(by_cluster)


def run_trend_detection(conn: sqlite3.Connection | None = None) -> int:
    if conn is not None:
        return _run_trend_detection_impl(conn)
    with get_connection() as c:
        return _run_trend_detection_impl(c)


def _row_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def _matches_trend_filters(
    trend: dict[str, Any],
    *,
    categories: list[str] | None,
    q: str | None,
    min_trend_score: float | None,
    max_risk: float | None,
) -> bool:
    if categories:
        cat = (trend.get("category") or "").strip().lower()
        if cat not in categories:
            return False
    if min_trend_score is not None:
        if float(trend.get("trend_score") or 0) < min_trend_score:
            return False
    if max_risk is not None:
        if float(trend.get("risk_score") or 0) > max_risk:
            return False
    if q and q.strip():
        ql = q.strip().lower()
        parts = [str(trend.get("label") or ""), str(trend.get("summary") or "")]
        kws = trend.get("keywords")
        if isinstance(kws, list):
            parts.extend(str(x) for x in kws)
        blob = " ".join(parts).lower()
        if ql not in blob:
            return False
    return True


def get_trends_for_api(
    conn: sqlite3.Connection,
    *,
    category: str | None = None,
    q: str | None = None,
    min_trend_score: float | None = None,
    max_risk: float | None = None,
) -> list[dict[str, Any]]:
    cats: list[str] | None = None
    if category and category.strip():
        cats = [c.strip().lower() for c in category.split(",") if c.strip()]

    clusters = conn.execute(
        "SELECT * FROM trend_clusters ORDER BY trend_score DESC"
    ).fetchall()
    out = []
    for c in clusters:
        row = _row_dict(c)
        cid = row["id"]
        items = [
            _row_dict(x)
            for x in conn.execute(
                """
                SELECT id, title, url, source, platform, published_at
                FROM media_items WHERE cluster_id = ? ORDER BY id DESC LIMIT 5
                """,
                (cid,),
            ).fetchall()
        ]
        cnt = conn.execute(
            "SELECT COUNT(*) FROM media_items WHERE cluster_id = ?",
            (cid,),
        ).fetchone()[0]
        srcs = conn.execute(
            "SELECT COUNT(DISTINCT source) FROM media_items WHERE cluster_id = ?",
            (cid,),
        ).fetchone()[0]
        kws = []
        try:
            kws = json.loads(row.get("keywords") or "[]")
        except json.JSONDecodeError:
            pass
        rec = {
            "id": cid,
            "label": row["label"],
            "summary": row.get("summary") or "",
            "keywords": kws,
            "category": row.get("category") or "",
            "trend_score": round(float(row.get("trend_score") or 0), 1),
            "risk_score": round(float(row.get("risk_score") or 0), 1),
            "source_count": int(srcs),
            "item_count": int(cnt),
            "latest_items": items,
        }
        if not _matches_trend_filters(
            rec,
            categories=cats,
            q=q,
            min_trend_score=min_trend_score,
            max_risk=max_risk,
        ):
            continue
        out.append(rec)
    return out
