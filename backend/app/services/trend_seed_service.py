"""Trend Seed Engine — expand candidate phrases (Derja / FR / AR / Arabizi) for discovery."""

from __future__ import annotations

import re
from typing import Iterable

# Lightweight Tunisian / MENA spelling bridges (expandable)
_VARIANT_MAP: dict[str, list[str]] = {
    "barsha": ["برشا", "barcha", "برشة", "barsha"],
    "barcha": ["برشا", "barsha", "برشة"],
    "برشا": ["barsha", "barcha", "برشة"],
    "chicha": ["شيشة", "chicha", "sheesha"],
    "شيشة": ["chicha", "sheesha"],
    "fest9": ["فستق", "pistache", "fest9"],
    "pistache": ["فستق", "fest9", "pistache"],
    "tunisia": ["Tunisie", "tunis", "تونس", "tunisia"],
    "tunisie": ["Tunisia", "tunis", "تونس"],
    "ramadan": ["رمضان", "ramadhan", "ramadan"],
}


def _tokenize(phrase: str) -> list[str]:
    return [t for t in re.split(r"\s+", phrase.strip()) if t]


def expand_seed(phrase: str, *, max_variants: int = 16) -> list[str]:
    """Generate search/discovery expansions for a candidate topic."""
    raw = (phrase or "").strip()
    if not raw:
        return []
    out: list[str] = []
    seen: set[str] = set()

    def add(s: str) -> None:
        s2 = s.strip()
        if not s2:
            return
        k = s2.lower()
        if k in seen:
            return
        seen.add(k)
        out.append(s2)

    add(raw)
    add(f'"{raw}"')
    compact = re.sub(r"\s+", "", raw)
    add(f"#{compact}")
    add(f"{raw} Tunisia")
    add(f"{raw} Tunisie")

    tokens = _tokenize(raw)
    for tok in tokens:
        key = tok.lower()
        for v in _VARIANT_MAP.get(key, []):
            if len(tokens) == 1:
                add(v)
            else:
                # replace token in phrase
                add(re.sub(re.escape(tok), v, raw, count=1, flags=re.IGNORECASE))

    # Arabic + Latin pairing when two-word
    if len(tokens) == 2:
        a, b = tokens
        add(f"{a} + {b} Tunisia")
        add(f"{a} {b}")

    return out[:max_variants]


def expand_seeds(phrases: Iterable[str], *, max_total: int = 40) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for p in phrases:
        for v in expand_seed(p):
            k = v.lower()
            if k in seen:
                continue
            seen.add(k)
            out.append(v)
            if len(out) >= max_total:
                return out
    return out
