import hashlib


def stable_hash(*parts: object) -> str:
    base = "||".join([str(p or "").strip().lower() for p in parts])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
