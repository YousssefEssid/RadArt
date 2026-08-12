# RadArt

AI-powered media intelligence MVP: collect public signals (RSS, optional APIs, mock social), cluster trends in SQLite, match a client brief, and surface campaign recommendations.

## Architecture

| Layer | Stack |
|-------|--------|
| Backend | FastAPI app package (`backend/app`): routers → repositories → services → collectors |
| Frontend | React + Vite + TypeScript, React Router, TanStack Query, feature folders |
| Data | SQLite today (`backend/data/radart.db`); path configurable for a later Postgres move |

```
backend/app/
  api/v1/          # HTTP routers
  repositories/    # SQL access
  services/        # domain logic
  collectors/      # external sources
  jobs/            # scheduler / collection pipeline
  core/            # config, database
frontend/src/
  app/             # providers + router
  features/        # radar, brief, competitors, sources, pricing, contact
  shared/          # api client, ui, lib, config
```

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

Smoke test:

```bash
pytest app/tests -q
```

On startup the app initializes SQLite at `backend/data/radart.db`, runs a first collection in the background, and schedules collection every 15 minutes (configurable).

## Frontend

```bash
cd frontend
npm install
npm run dev
```

App: `http://localhost:5173` (deep links: `/dashboard`, `/brief`, `/concurrents`, `/sources`, `/tarifs`, `/contact`)

Optional: point the UI at another API host:

```bash
set VITE_API_BASE=http://localhost:8000
npm run dev
```

## Environment (optional)

Copy `.env.example` to `.env` at the project root (`RadArt/.env`).

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Optional LLM for richer brief parsing and copy |
| `GEMINI_API_KEY` | Optional LLM (used if OpenAI not set) |
| `YOUTUBE_API_KEY` | Optional YouTube search results |
| `COLLECTION_INTERVAL_MINUTES` | Default `15` |
| `DATABASE_PATH` | Default `backend/data/radart.db` |

The demo runs with **no API keys** (RSS + Reddit + iTunes charts + mock social + rule-based outputs).

### Extra collectors (public, no login)

| Source | What it captures |
|--------|------------------|
| RSS (TN + Afrique + Billboard/NME/Variety/Verge/Know Your Meme) | News, music, entertainment |
| Google News RSS (TN + FR + US queries) | Viral / tiktok / meme / songs headlines |
| Reddit hot JSON (`r/Tunisia`, memes, videos, Music, soccer, …) | What people hop on right now |
| iTunes charts (TN / FR / US songs + TN clips) | Songs & music videos going mainstream |
| YouTube Data API | Optional, if `YOUTUBE_API_KEY` is set |
| SerpApi Google Trends | Optional, if `SERPAPI_API_KEY` is set |

Still **no unofficial Meta/TikTok scrape** (ToS). Social-style captions for demo live in `backend/data/mock_social_trends.json`.

## Legal / collection note

Collectors use the `RadArtBot/1.0` user agent, timeouts, and curated sources only. Some feeds or sites may fail on certain networks (SSL, rate limits); mock data and demo items keep the UI usable.

### Facebook, Instagram, TikTok

RadArt does **not** scrape private feeds or bypass logins on Meta/TikTok (that violates their Terms of Service and is fragile legally). For real data you would use **official APIs** (e.g. Meta Graph API with app review, TikTok for Developers / research programs) or **your own** exported or licensed content.

The app **does** parse **trend signals** from any caption-like text you ingest: **hashtags**, **@mentions**, **quoted phrases**, and **multi-word capitalized names** (e.g. public figures), then folds them into keywords and clustering. The file `backend/data/mock_social_trends.json` simulates TikTok/Instagram/Facebook-style captions for demos.

### Google Trends

Google does **not** publish an official, API-key **Google Trends** REST service like YouTube Data API. The charts at [trends.google.com](https://trends.google.com) are for humans in the browser. Unofficial Python libraries (e.g. **pytrends**) hit internal endpoints and can break or conflict with Terms of Use — use only if you accept that risk.

RadArt includes **`google_news_rss_collector`**: public **Google News RSS** URLs (`news.google.com/rss/search?...`) for Tunisia-focused queries. That is **not** the same as Trends scores, but it adds timely headlines with **no API key** and feeds the same clustering pipeline.

**SerpApi Google Trends** (optional): set `SERPAPI_API_KEY` from [SerpApi](https://serpapi.com/). The collector calls `engine=google_trends` (`search.json`) and turns **related queries**, **related topics**, and optionally **interest over time** into `media_items` for clustering. Tune `SERPAPI_GOOGLE_TRENDS_MAX_REQUESTS_PER_RUN` to respect your monthly search quota.
