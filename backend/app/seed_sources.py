RSS_SOURCES = [
    {"name": "Mosaique FM", "url": "https://www.mosaiquefm.net/fr/rss", "category": "general"},
    {"name": "Business News", "url": "https://www.businessnews.com.tn/rss", "category": "business"},
    {
        "name": "Webdo",
        "url": "https://www.webdo.tn/fr/rss",
        "fallback_urls": [
            "https://www.webdo.tn/rss",
            "https://www.webdo.tn/en/rss",
        ],
        "category": "general",
    },
]

YOUTUBE_QUERIES = [
    "Tunisie actualité",
    "Tunisie économie",
    "Tunisie sport",
    "Tunisie tendance",
    "Tunisie météo",
    "Ramadan Tunisie",
    "Etudiants Tunisie",
    "inflation Tunisie",
]

# Public RSS feeds from news.google.com (not the same as Google Trends charts; no API key).
GOOGLE_NEWS_RSS_QUERIES = [
    {"q": "Tunisie", "category": "general"},
    {"q": "économie Tunisie", "category": "business"},
    {"q": "sport Tunisie", "category": "sport"},
    {"q": "météo Tunisie", "category": "weather"},
]

# SerpApi Google Trends (engine=google_trends) — needs SERPAPI_API_KEY in .env
SERPAPI_GOOGLE_TRENDS_SEEDS = [
    {"q": "Tunisie", "category": "general"},
]

# Up to 5 comma-separated queries in one TIMESERIES request (optional; costs +1 SerpApi search).
SERPAPI_GOOGLE_TRENDS_TIMESERIES_QUERIES = [
    "Tunisie",
    "inflation Tunisie",
    "Ramadan Tunisie",
    "météo Tunisie",
    "étudiants Tunisie",
]

GDELT_KEYWORDS = [
    "Tunisia",
    "Tunisie",
    "Tunisian economy",
    "Ramadan Tunisia",
    "tourism Tunisia",
    "inflation Tunisia",
]
