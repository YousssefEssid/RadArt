from __future__ import annotations

from datetime import datetime, timezone
RISK_KEYWORDS = [
    "politique",
    "président",
    "gouvernement",
    "religion",
    "mort",
    "décès",
    "accident",
    "crise",
    "scandale",
    "attaque",
    "violence",
    "maladie",
    "hôpital",
    "justice",
    "procès",
    "terrorisme",
    "guerre",
]


def normalize(value: float, max_value: float) -> float:
    if max_value <= 0:
        return 0.0
    return min(100.0, (value / max_value) * 100.0)


def recency_score_from_hours(hours: float) -> float:
    if hours <= 6:
        return 100.0
    if hours <= 24:
        return 80.0
    if hours <= 48:
        return 60.0
    if hours <= 72:
        return 40.0
    return 20.0


def cluster_recency_score(latest_published: datetime | None) -> float:
    if not latest_published:
        return 50.0
    if latest_published.tzinfo is None:
        latest_published = latest_published.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    hours = max(0.0, (now - latest_published).total_seconds() / 3600.0)
    return recency_score_from_hours(hours)


def risk_from_text(text: str) -> float:
    t = text.lower()
    score = 20.0
    for kw in RISK_KEYWORDS:
        if kw in t:
            score += 15.0
    return min(100.0, score)


def trend_composite(
    volume_score: float,
    growth_score: float,
    engagement_score: float,
    diversity_score: float,
    recency_score: float,
) -> float:
    return (
        0.30 * volume_score
        + 0.25 * growth_score
        + 0.20 * engagement_score
        + 0.15 * diversity_score
        + 0.10 * recency_score
    )


def urgency_from_trend_score(trend_score: float) -> str:
    if trend_score >= 80:
        return "Act within 24–48 hours"
    if trend_score >= 60:
        return "Use this week"
    return "Monitor or use as evergreen insight"


def growth_score_from_counts(last_24: int, prev_24: int) -> float:
    if last_24 == 0 and prev_24 == 0:
        return 50.0
    if prev_24 == 0:
        return min(100.0, 50.0 + last_24 * 5)
    ratio = last_24 / max(1, prev_24)
    return min(100.0, normalize(ratio, 2.0) * 50 + 25)
