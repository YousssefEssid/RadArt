RSS_SOURCES = [
    {"name": "Mosaique FM", "url": "https://www.mosaiquefm.net/fr/rss", "category": "general"},
    {"name": "Business News", "url": "https://www.businessnews.com.tn/rss", "category": "business"},
    {
        "name": "Webdo",
        "url": "https://www.webdo.tn/fr/rss",
        "fallback_urls": ["https://www.webdo.tn/rss", "https://www.webdo.tn/en/rss"],
        "category": "general",
    },
    {"name": "Tunisie Numerique", "url": "https://www.tunisienumerique.com/feed/", "category": "general"},
    {"name": "Kapitalis", "url": "https://kapitalis.com/tunisie/feed/", "category": "general"},
    {"name": "L'Economiste Maghrebin", "url": "https://www.leconomistemaghrebin.com/feed/", "category": "business"},
    {"name": "African Manager", "url": "https://www.africanmanager.com/feed/", "category": "business"},
    {"name": "Leaders Tunisie", "url": "https://www.leaders.com.tn/rss.xml", "category": "business"},
    {"name": "Réalités", "url": "https://realites.com.tn/fr/feed/", "category": "general"},
    {"name": "Tuniscope", "url": "https://www.tuniscope.com/feed/", "category": "lifestyle"},
    {"name": "Shems FM", "url": "https://www.shemsfm.net/fr/rss", "category": "culture"},
    {"name": "Jawhara FM", "url": "https://www.jawharafm.net/fr/rss", "category": "culture"},
    {"name": "France 24 Afrique", "url": "https://www.france24.com/fr/afrique/rss", "category": "general"},
    {"name": "BBC Afrique", "url": "https://feeds.bbci.co.uk/afrique/rss.xml", "category": "general"},
    {"name": "Jeune Afrique", "url": "https://www.jeuneafrique.com/rss/", "category": "general"},
    {"name": "Billboard", "url": "https://www.billboard.com/feed/", "category": "culture"},
    {"name": "Variety", "url": "https://variety.com/feed/", "category": "culture"},
    {"name": "NME", "url": "https://www.nme.com/news/music/feed", "category": "culture"},
    {"name": "The Verge", "url": "https://www.theverge.com/rss/index.xml", "category": "viral"},
    {"name": "Know Your Meme", "url": "https://knowyourmeme.com/news.rss", "category": "viral"},
]

YOUTUBE_QUERIES = [
    "Tunisie viral",
    "Tunisie tiktok tendance",
    "chanson Tunisie",
    "football Tunisie",
    "meme Tunisie",
    "Tunisie actualité",
    "Tunisie économie",
    "Ramadan Tunisie",
    "concert Tunisie",
    "rap tunisien",
    "rentrée scolaire Tunisie",
    "humour tunisien",
    "derja Tunisie",
]

# Public RSS feeds from news.google.com (not Google Trends charts; no API key).
GOOGLE_NEWS_RSS_QUERIES = [
    {"q": "Tunisie", "category": "general"},
    {"q": "économie Tunisie", "category": "business"},
    {"q": "sport Tunisie OR football Tunisie", "category": "sport"},
    {"q": "météo Tunisie", "category": "weather"},
    {"q": "viral Tunisie OR tiktok Tunisie OR meme Tunisie", "category": "viral"},
    {"q": "musique Tunisie OR chanson Tunisie OR rap Tunisie", "category": "culture"},
    {"q": "festival Tunisie OR concert Tunisie", "category": "culture"},
    {"q": "rentrée scolaire Tunisie OR étudiants Tunisie", "category": "youth"},
    {"q": "télécom Tunisie OR Ooredoo OR Orange Tunisie OR Tunisie Telecom", "category": "business"},
    {"q": "boisson OR café OR soda Tunisie", "category": "lifestyle"},
    {
        "q": "viral meme OR tiktok trend OR internet challenge",
        "category": "viral",
        "hl": "en",
        "gl": "US",
        "ceid": "US:en",
    },
    {
        "q": "billboard viral song OR trending music video",
        "category": "culture",
        "hl": "en",
        "gl": "US",
        "ceid": "US:en",
    },
    {
        "q": "tendance tiktok OR meme viral OR challenge",
        "category": "viral",
        "hl": "fr",
        "gl": "FR",
        "ceid": "FR:fr",
    },
]

SERPAPI_GOOGLE_TRENDS_SEEDS = [
    {"q": "Tunisie", "category": "general"},
    {"q": "tiktok", "category": "viral"},
    {"q": "rentrée", "category": "youth"},
    {"q": "Ramadan", "category": "culture"},
]

SERPAPI_GOOGLE_TRENDS_TIMESERIES_QUERIES = [
    "Tunisie",
    "tiktok",
    "football Tunisie",
    "Ramadan Tunisie",
    "inflation Tunisie",
    "rentrée scolaire",
]

GDELT_KEYWORDS = [
    "Tunisia",
    "Tunisie",
    "Tunisia football",
    "Tunisia music",
    "tourism Tunisia",
    "inflation Tunisia",
    "Tunisia students",
]

REDDIT_FEEDS = [
    {"name": "r/Tunisia", "path": "Tunisia", "category": "general"},
    {"name": "Reddit viral mix", "path": "memes+videos+Music+soccer+OutOfTheLoop", "category": "viral"},
]

ITUNES_CHARTS = [
    {"store": "tn", "kind": "topsongs", "category": "culture", "label": "Apple Music TN"},
    {"store": "fr", "kind": "topsongs", "category": "culture", "label": "Apple Music FR"},
    {"store": "us", "kind": "topsongs", "category": "culture", "label": "Apple Music US"},
]
