USER_AGENT = "RadArtBot/1.0"


def request_headers() -> dict[str, str]:
    return {"User-Agent": USER_AGENT, "Accept": "application/json, text/html;q=0.9,*/*;q=0.8"}
