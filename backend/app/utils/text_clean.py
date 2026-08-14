"""Strip HTML / entity junk so UI titles stay human-readable."""

from __future__ import annotations

import html
import re
from urllib.parse import urlparse

# Broken numeric entities that lost & and ; → "#8217" or "8217;"
_BROKEN_DEC_ENTITY = re.compile(r"(?:&#|#|&amp;#)?(\d{2,6});?")
_BROKEN_HEX_ENTITY = re.compile(r"(?:&#x|#x|&amp;#x)?([0-9a-fA-F]{2,6});?")
_TAG_RE = re.compile(r"<[^>]+>", re.DOTALL)
_URL_RE = re.compile(r"https?://[^\s<>\"']+", re.IGNORECASE)
_WWW_RE = re.compile(r"\bwww\.[^\s<>\"']+", re.IGNORECASE)
_CSS_HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})\b")
_ATTR_FRAGMENT = re.compile(
    r"\b(?:class|style|src|href|alt|width|height|target|rel|id|data-[\w-]+)\s*=\s*[\"']?[^\"'\s>]*[\"']?",
    re.IGNORECASE,
)
_WP_CLASS_NOISE = re.compile(
    r"\b(?:attachment-\w+|size-\w+|wp-post-image|alignnone|aligncenter)\b",
    re.IGNORECASE,
)
_MULTI_SPACE = re.compile(r"\s+")
_MULTI_PUNCT = re.compile(r"([,;:]){2,}")
_LEADING_JUNK = re.compile(r"^[\s«»\"'“”‘’\-–—,:;#]+")
_TRAILING_JUNK = re.compile(r"[\s«»\"'“”‘’\-–—,:;]+$")

# Common decimal HTML entities we care about for titles
_KNOWN_DEC = {
    8216: "‘",
    8217: "’",
    8218: "‚",
    8220: "“",
    8221: "”",
    8222: "„",
    8230: "…",
    8211: "–",
    8212: "—",
    160: " ",
    39: "'",
    34: '"',
    38: "&",
    60: "<",
    62: ">",
}


def _replace_broken_entities(text: str) -> str:
    def dec_sub(m: re.Match[str]) -> str:
        try:
            n = int(m.group(1))
        except ValueError:
            return " "
        if n in _KNOWN_DEC:
            return _KNOWN_DEC[n]
        if 32 <= n < 0x110000:
            try:
                return chr(n)
            except ValueError:
                return " "
        return " "

    def hex_sub(m: re.Match[str]) -> str:
        try:
            n = int(m.group(1), 16)
        except ValueError:
            return " "
        if n in _KNOWN_DEC:
            return _KNOWN_DEC[n]
        if 32 <= n < 0x110000:
            try:
                return chr(n)
            except ValueError:
                return " "
        return " "

    # Prefer full &#123; first via html.unescape later; fix orphan #8217 style first
    text = re.sub(r"&#(\d{2,6});?", lambda m: _KNOWN_DEC.get(int(m.group(1)), chr(int(m.group(1))) if int(m.group(1)) < 0x110000 else " "), text)
    text = re.sub(r"&#x([0-9a-fA-F]{2,6});?", lambda m: chr(int(m.group(1), 16)) if int(m.group(1), 16) < 0x110000 else " ", text)
    # Orphan "#8217" / "#8220" (no &) — only when looks like entity code, not a real hashtag word
    text = re.sub(r"(?<![\w])#(\d{2,6})\b", dec_sub, text)
    return text


def strip_html(text: str) -> str:
    if not text:
        return ""
    t = str(text)
    # Remove scripts/styles blocks first
    t = re.sub(r"(?is)<script[^>]*>.*?</script>", " ", t)
    t = re.sub(r"(?is)<style[^>]*>.*?</style>", " ", t)
    t = _TAG_RE.sub(" ", t)
    return t


def clean_plain_text(text: str | None, *, max_len: int | None = None) -> str:
    """Decode entities, strip tags, drop CSS/attr noise. Safe for body copy."""
    if not text:
        return ""
    t = str(text)
    t = html.unescape(t)
    t = html.unescape(t)  # double-encoded feeds
    t = _replace_broken_entities(t)
    t = strip_html(t)
    t = html.unescape(t)
    t = _ATTR_FRAGMENT.sub(" ", t)
    t = _WP_CLASS_NOISE.sub(" ", t)
    t = _CSS_HEX.sub(" ", t)
    t = t.replace("\xa0", " ").replace("&nbsp;", " ")
    t = _MULTI_SPACE.sub(" ", t).strip()
    if max_len is not None and len(t) > max_len:
        t = t[: max_len - 1].rstrip() + "…"
    return t


def clean_display_title(text: str | None, *, max_len: int = 90) -> str:
    """Human-facing headline: no URLs, no HTML, no entity junk."""
    t = clean_plain_text(text)
    if not t:
        return "Tendance"

    # Drop URLs (keep domain name only if that's all we have later)
    urls = _URL_RE.findall(t) + _WWW_RE.findall(t)
    t = _URL_RE.sub(" ", t)
    t = _WWW_RE.sub(" ", t)

    # Drop leftover attribute / markup crumbs
    t = re.sub(r"\b(?:target|href|src|class|style|alt)\s*=?", " ", t, flags=re.IGNORECASE)
    t = re.sub(r"[<>{}|\\]+", " ", t)
    t = _MULTI_PUNCT.sub(r"\1", t)
    t = _MULTI_SPACE.sub(" ", t).strip()
    t = _LEADING_JUNK.sub("", t)
    t = _TRAILING_JUNK.sub("", t)
    t = _MULTI_SPACE.sub(" ", t).strip(" ,;—–-")

    # If title emptied into junk, salvage a site name or fallback
    if len(t) < 3:
        for u in urls:
            try:
                host = urlparse(u if "://" in u else f"https://{u}").hostname or ""
                host = host.removeprefix("www.")
                if host and "." in host:
                    return host.split(".")[0].replace("-", " ").title()[:max_len]
            except Exception:
                continue
        return "Tendance"

    # Prefer first clause if bloated with comma-separated junk
    if t.count(",") >= 2 and len(t) > 60:
        parts = [p.strip() for p in t.split(",") if p.strip()]
        # Keep parts that look like words, not codes
        parts = [p for p in parts if not re.fullmatch(r"#?\d+", p) and not re.fullmatch(r"[0-9a-fA-F]{3,8}", p)]
        if parts:
            # Prefer longest meaningful phrase
            parts.sort(key=len, reverse=True)
            t = parts[0]

    if len(t) > max_len:
        cut = t[: max_len - 1]
        if " " in cut:
            cut = cut.rsplit(" ", 1)[0]
        t = cut.rstrip(" ,;:.-") + "…"
    return t or "Tendance"


def is_junk_keyword(token: str) -> bool:
    """Filter fake hashtags from HTML entities / CSS / attributes."""
    s = (token or "").strip()
    if not s:
        return True
    raw = s.lstrip("#@").strip()
    low = raw.lower()
    if low in {
        "target",
        "href",
        "src",
        "class",
        "style",
        "alt",
        "width",
        "height",
        "rel",
        "http",
        "https",
        "www",
        "null",
        "undefined",
        "attachment",
        "wp-post-image",
        "size-full",
        "img",
    }:
        return True
    if re.fullmatch(r"\d{2,6}", raw):  # 8217, 8220…
        return True
    if re.fullmatch(r"[0-9a-f]{3}", low) or re.fullmatch(r"[0-9a-f]{6}", low):
        return True
    if raw.startswith("http") or "." in raw and "/" in raw:
        return True
    if len(raw) < 2:
        return True
    return False


def attractive_cluster_label(titles: list[str], keywords: list[str], *, max_len: int = 72) -> str:
    """Pick a clean display label — prefer real headlines over hashtag soup."""
    for title in titles:
        cleaned = clean_display_title(title, max_len=max_len)
        if cleaned and cleaned != "Tendance" and not is_junk_keyword(cleaned):
            # Skip labels that are mostly entity debris
            if not re.fullmatch(r"[#\d,\s]+", cleaned):
                return cleaned

    good_kw = [k.lstrip("#@") for k in keywords if not is_junk_keyword(k)]
    good_kw = [k for k in good_kw if not k.startswith("#") or not is_junk_keyword(k)]
    # Prefer non-hashtag phrases / words
    phrases = [k for k in good_kw if " " in k or (k[:1].isupper() and not k.startswith("#"))]
    if phrases:
        return clean_display_title(phrases[0], max_len=max_len)
    words = [k.lstrip("#") for k in good_kw if k.lstrip("#").isalpha() or re.search(r"[\u0600-\u06FF]", k)]
    if words:
        return clean_display_title(", ".join(words[:2]), max_len=max_len)
    return "Tendance émergente"
