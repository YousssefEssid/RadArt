import json
import re
from typing import Any

from app.services.social_signals import extract_social_signals, merge_keywords_with_signals

CATEGORY_KEYWORDS = {
    "politics": ["président", "gouvernement", "ministre", "élection", "parlement", "politique"],
    "economy": ["inflation", "prix", "économie", "marché", "banque", "emploi", "croissance"],
    "sport": ["football", "match", "club", "stade", "derby", "équipe", "caf", "can"],
    "weather": ["météo", "pluie", "chaleur", "canicule", "température"],
    "youth": ["étudiant", "examen", "université", "bac", "campus"],
    "retail": ["promotion", "achat", "prix", "magasin", "supermarché", "discount"],
    "viral": ["meme", "mème", "viral", "tiktok", "challenge", "fyp", "audio", "sound", "trend"],
    "culture": ["festival", "musique", "cinéma", "artiste", "concert", "chanson", "rap", "clip", "album", "spotify"],
}

POSITIVE = ["gain", "success", "croissance", "record", "victoire", "bonne", "positive"]
NEGATIVE = ["crise", "mort", "accident", "chute", "perte", "scandale", "attaque"]


def _detect_language(text: str) -> str:
    if re.search(r"[\u0600-\u06FF]", text):
        return "ar"
    if re.search(r"[àâçéèêëîïôùûüÿœæ]", text.lower()):
        return "fr"
    return "en"


def _keywords_simple(text: str, max_kw: int = 8) -> list[str]:
    words = re.findall(r"[\wàâçéèêëîïôùûüÿœæ]+", text.lower(), flags=re.UNICODE)
    stop = {
        "the",
        "and",
        "for",
        "avec",
        "dans",
        "une",
        "des",
        "les",
        "pour",
        "sur",
        "est",
        "qui",
    }
    freq: dict[str, int] = {}
    for w in words:
        if len(w) < 3 or w in stop:
            continue
        freq[w] = freq.get(w, 0) + 1
    ranked = sorted(freq.keys(), key=lambda x: -freq[x])
    return ranked[:max_kw]


def _category_from_keywords(combined: str, fallback: str | None) -> str:
    low = combined.lower()
    for cat, kws in CATEGORY_KEYWORDS.items():
        for kw in kws:
            if kw in low:
                return cat
    return fallback or "general"


def _sentiment(text: str) -> str:
    low = text.lower()
    p = sum(1 for w in POSITIVE if w in low)
    n = sum(1 for w in NEGATIVE if w in low)
    if p > n:
        return "positive"
    if n > p:
        return "negative"
    return "neutral"


def enrich_item(item: dict[str, Any]) -> dict[str, Any]:
    title = str(item.get("title") or "")
    body = str(item.get("text") or "")
    combined = f"{title} {body}".strip()
    lang = _detect_language(combined)
    signals = extract_social_signals(combined)
    kws = merge_keywords_with_signals(_keywords_simple(combined), signals)
    cat = _category_from_keywords(combined, item.get("category"))
    sent = _sentiment(combined)
    item = dict(item)
    item["language"] = lang
    item["keywords"] = json.dumps(kws, ensure_ascii=False)
    item["entities"] = json.dumps(signals, ensure_ascii=False)
    item["category"] = cat
    item["sentiment"] = sent
    return item
