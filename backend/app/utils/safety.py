USER_AGENT = "RadArtBot/1.0 (+https://github.com/YousssefEssid/RadArt; media-intelligence)"


def request_headers() -> dict[str, str]:
    return {
        "User-Agent": USER_AGENT,
        "Accept": "application/json, application/rss+xml, text/html;q=0.9,*/*;q=0.8",
    }
