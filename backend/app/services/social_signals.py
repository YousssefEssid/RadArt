"""
Extract trend-oriented tokens from social-style text (captions, titles).

Works on any string you legally obtain (RSS, official APIs, user-provided exports,
curated caption-style samples). This module does not fetch from Meta/TikTok.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Any

# Hashtag: #word (letters, numbers, underscore; Unicode letters)
HASHTAG_RE = re.compile(r"#([\wÀ-ÿ\u0600-\u06FF]{2,})", re.UNICODE)
# @handle (Instagram/TikTok style)
MENTION_RE = re.compile(r"@([\w.]{2,40})")
# Quoted phrases — often challenges or sound names
QUOTED_RE = re.compile(r'"([^"]{2,80})"|«([^»]{2,80})»')
# Multi-word capitalized phrase (e.g. "Logan Paul", "Summer Vibes")
TITLE_CASE_PHRASE_RE = re.compile(
    r"\b(?:[A-ZÀÁÂÄÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸ]"
    r"[a-zà-ÿ]*(?:\s+[A-ZÀÁÂÄÆÇÈÉÊËÌÍÎÏÐÑÒÓÔÕÖØÙÚÛÜÝÞŸ][a-zà-ÿ]*)+)\b"
)


from app.utils.text_clean import is_junk_keyword


def _norm_token(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).strip()
    return s


def extract_hashtags(text: str) -> list[str]:
    seen: list[str] = []
    for m in HASHTAG_RE.finditer(text or ""):
        t = _norm_token(m.group(1))
        if not t or is_junk_keyword(t) or is_junk_keyword(f"#{t}"):
            continue
        if t.lower() not in {x.lower() for x in seen}:
            seen.append(t)
    return seen


def extract_mentions(text: str) -> list[str]:
    seen: list[str] = []
    for m in MENTION_RE.finditer(text or ""):
        t = _norm_token(m.group(1))
        if not t or is_junk_keyword(t):
            continue
        if t.lower() not in {x.lower() for x in seen}:
            seen.append(t)
    return seen


def extract_quoted_phrases(text: str) -> list[str]:
    seen: list[str] = []
    for m in QUOTED_RE.finditer(text or ""):
        t = _norm_token(m.group(1) or m.group(2) or "")
        if len(t) < 2 or is_junk_keyword(t):
            continue
        if t.lower() not in {x.lower() for x in seen}:
            seen.append(t)
    return seen


def extract_title_case_phrases(text: str, max_phrases: int = 8) -> list[str]:
    """Heuristic for person names / brand phrases in Latin script."""
    out: list[str] = []
    for m in TITLE_CASE_PHRASE_RE.finditer(text or ""):
        phrase = _norm_token(m.group(0))
        words = phrase.split()
        if len(words) < 2:
            continue
        if is_junk_keyword(phrase):
            continue
        if phrase.lower() in {x.lower() for x in out}:
            continue
        out.append(phrase)
        if len(out) >= max_phrases:
            break
    return out


def extract_social_signals(text: str) -> dict[str, Any]:
    """Structured signals for storage and clustering."""
    t = text or ""
    tags = extract_hashtags(t)
    mentions = extract_mentions(t)
    quoted = extract_quoted_phrases(t)
    names = extract_title_case_phrases(t)
    return {
        "hashtags": tags,
        "mentions": mentions,
        "quoted_phrases": quoted,
        "title_case_phrases": names,
    }


def merge_keywords_with_signals(base_keywords: list[str], signals: dict[str, Any], max_total: int = 20) -> list[str]:
    """
    Put high-signal social tokens first (hashtags, @handles, names), then TF-IDF-style keywords.
    Deduplicate case-insensitively.
    """
    seen_lower: set[str] = set()
    merged: list[str] = []

    def add_many(items: list[str], prefix: str | None = None):
        for x in items:
            s = f"{prefix}{x}" if prefix else x
            if is_junk_keyword(s) or is_junk_keyword(x):
                continue
            low = s.lower()
            if low in seen_lower:
                continue
            seen_lower.add(low)
            merged.append(s)
            if len(merged) >= max_total:
                return

    add_many(signals.get("hashtags") or [], "#")
    add_many([f"@{m}" for m in (signals.get("mentions") or [])])
    add_many(signals.get("quoted_phrases") or [])
    add_many(signals.get("title_case_phrases") or [])
    for w in base_keywords:
        if is_junk_keyword(w):
            continue
        low = w.lower()
        if low in seen_lower:
            continue
        seen_lower.add(low)
        merged.append(w)
        if len(merged) >= max_total:
            break
    return merged


def signals_to_cluster_text(signals: dict[str, Any]) -> str:
    """Extra bag-of-words line so TF-IDF sees hashtags / names explicitly."""
    parts: list[str] = []
    for h in signals.get("hashtags") or []:
        if is_junk_keyword(h):
            continue
        parts.append(f"#{h}")
        parts.append(h)
    for m in signals.get("mentions") or []:
        if is_junk_keyword(m):
            continue
        parts.append(f"@{m}")
        parts.append(m)
    for q in signals.get("quoted_phrases") or []:
        if is_junk_keyword(q):
            continue
        parts.append(q)
    for n in signals.get("title_case_phrases") or []:
        if is_junk_keyword(n):
            continue
        parts.append(n)
    return " ".join(parts)
