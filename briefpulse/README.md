# RADJ

AI-powered media intelligence MVP: collect public signals (RSS, optional APIs, mock social), cluster trends in SQLite, match a client brief, and surface campaign recommendations.

## Prerequisites

- Python 3.11+
- Node.js 18+ (for the frontend)

## Backend

```bash
cd backend
python -m venv .venv
```

Windows:

```bash
.venv\Scripts\activate
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r ../requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

API: `http://localhost:8000` · OpenAPI: `http://localhost:8000/docs`

On startup the app initializes SQLite at `backend/data/briefpulse.db`, runs a first collection in the background, and schedules collection every 15 minutes (configurable).

## Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173`

Optional: point the UI at another API host:

```bash
set VITE_API_BASE=http://localhost:8000
npm run dev
```

## Environment (optional)

Copy `.env.example` to `.env` at the project root (`briefpulse/.env`).

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Optional LLM for richer brief parsing and copy |
| `GEMINI_API_KEY` | Optional LLM (used if OpenAI not set) |
| `YOUTUBE_API_KEY` | Optional YouTube search results |
| `COLLECTION_INTERVAL_MINUTES` | Default `15` |
| `DATABASE_PATH` | Default `backend/data/briefpulse.db` |

The demo runs with **no API keys** (RSS + mock social + rule-based outputs).

## Legal / collection note

Collectors use the `RADJHackathonBot/1.0` user agent, timeouts, and curated sources only. Some feeds or sites may fail on certain networks (SSL, rate limits); mock data and demo items keep the UI usable.

### Facebook, Instagram, TikTok

RADJ does **not** scrape private feeds or bypass logins on Meta/TikTok (that violates their Terms of Service and is fragile legally). For real data you would use **official APIs** (e.g. Meta Graph API with app review, TikTok for Developers / research programs) or **your own** exported or licensed content.

The app **does** parse **trend signals** from any caption-like text you ingest: **hashtags**, **@mentions**, **quoted phrases**, and **multi-word capitalized names** (e.g. public figures), then folds them into keywords and clustering. The file `backend/data/mock_social_trends.json` simulates TikTok/Instagram/Facebook-style captions for demos.

### Google Trends

Google does **not** publish an official, API-key **Google Trends** REST service like YouTube Data API. The charts at [trends.google.com](https://trends.google.com) are for humans in the browser. Unofficial Python libraries (e.g. **pytrends**) hit internal endpoints and can break or conflict with Terms of Use — use only if you accept that risk.

RADJ includes **`google_news_rss_collector`**: public **Google News RSS** URLs (`news.google.com/rss/search?...`) for Tunisia-focused queries. That is **not** the same as Trends scores, but it adds timely headlines with **no API key** and feeds the same clustering pipeline.

**SerpApi Google Trends** (optional): set `SERPAPI_API_KEY` from [SerpApi](https://serpapi.com/). The collector calls `engine=google_trends` (`search.json`) and turns **related queries**, **related topics**, and optionally **interest over time** into `media_items` for clustering. Tune `SERPAPI_GOOGLE_TRENDS_MAX_REQUESTS_PER_RUN` to respect your monthly search quota.
