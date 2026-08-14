# RadArt

**RadArt** is **AI Cultural & Marketing Intelligence for Tunisia and MENA**.

It detects what is gaining attention, understands whether it matters for a brand, and turns that into campaigns teams can execute — between social listening, trend intel, competitive watch, and an AI strategist.

> What is happening right now? What matters for my brand? What should we do, and why?

**Advantage:** local understanding + speed + actionable recommendations (Derja / Arabizi / Arabic / French / English) — not “more dashboards” or raw source volume.

Technically the engine still runs: collect → cluster → score → match brief → recommend. Commercially the product leads with **workflows**, starting with **Morning Radar**.

---

## Who it is for

| Audience | How they use RadArt |
|----------|---------------------|
| **Communication / digital agencies** | Morning answer for each client; brief → executable angles |
| **Brand / social managers** | Spot songs, memes, news spikes before they cool; reputation alerts |
| **Strategy / creative teams** | Why it matters + what to do (formats, urgency, local angles) |

RadArt is **not** a generic news reader or “top trends” wall.

---

## What the platform does

### 1. Morning Radar (`/dashboard`)
- Answers: **what changed since yesterday?**
- Classifies signals: Emerging · Growing · Competitor move · Conversation shift · Reputation · Brand opportunity · Fading
- Each trend becomes an **Opportunity Card**: **RAD Score**, momentum, Tunisia relevance, audience, lifecycle, sources, why it’s growing, Brand Fit, Recommended move
- Optional technical explorer for platform filters / raw trend cards

### 1b. Brand Brain (`/marque`)
- Build **Brand DNA** (industry, audience, personality, languages, competitors, channels, objectives, forbidden topics, tone, guidelines, products, budget)
- Every Opportunity Card is scored through that DNA — including **don’t chase** (e.g. 23% fit)

### RAD Score (product identity)
- `RAD = Relevance × Acceleration × Differentiation`
- Combines momentum, freshness, Tunisia relevance, audience overlap, brand fit, source diversity, competitive saturation, − brand safety risk
- Always explained (why), never a naked number

### Should we jump on this?
- On each Opportunity Card: **Analyse for my brand** → YES / CAUTION / NO with fit scores
- **Generate Campaign** → big idea, insight, concept, key message, TikTok/Reel concepts, captions, visual, influencers, hashtags, timing, KPIs
- Bridge: social listening → marketing execution

### 2. Brief client (`/brief`)
- Paste a brief or upload `.pptx` / `.docx` / `.pdf` / `.txt`
- Parses sector, target, tone, constraints, competitors
- Matches live trend clusters → **campaign recommendations** (angles, formats, influencer type, urgency)

### 3. Competitor War Room (`/concurrents`)
- Per competitor: talking points, campaigns gaining traction, themes owned, audience, formats, silences, early trend adopts
- **Theme board** + **Opportunity gaps** (e.g. A owns price, B owns premium → Convenience positioning)
- Sources: Brand Brain competitors (live) or telecom TN demo
- **Competitive alerts** on Morning Radar: competitor content spikes + acceleration + differentiated response (not louder copy)

### 4. Sources & collecte (`/sources`)
- Status of every collector (ok / error / skipped)
- **Signal coverage** board: Tunisia market context + live / needs key / customer-owned / planned / forbidden
- Upload **customer-owned** JSON exports (legal Meta/TikTok path)
- Trigger a **full collection** of all intel sources
- Optional keys: YouTube, SerpApi Trends, Meta Graph pages, TikTok official token

### 5. Tarifs / Contact (`/tarifs`, `/contact`)
- Product packaging (Start / Pro / Agency) and contact for custom needs

---

## Product pipeline

```
Public sources          SQLite              Intelligence
─────────────────       ──────────────      ─────────────────────────
RSS / Google News  ──►  media_items    ──►  trend clusters (scores)
Reddit / Apple Music    trend_clusters      Morning Radar buckets
YouTube / GDELT         client_briefs       brief matching
SerpApi / Meta / TikTok recommendations     campaign cards
(customer-owned JSON)   brand_profiles      Brand Brain + RAD
```

1. **Collect** curated public feeds (no unofficial Meta/TikTok scrape)
2. **Enrich** text (keywords, hashtags, category, sentiment)
3. **Cluster** similar items into trends and score them
4. **Morning Radar** — classify into actionable workflow buckets
5. **Match** trends to a client brief → **recommend** safe / bold / local angles

---

## Stack

| Layer | Tech |
|-------|------|
| Backend | FastAPI (`backend/app`): routers → repositories → services → collectors |
| Frontend | React + Vite + TypeScript, React Router, TanStack Query |
| Data | SQLite (`backend/data/radart.db`) — path configurable for Postgres later |
| Jobs | In-process scheduler (default every 15 minutes) |

```
backend/app/
  api/v1/          # HTTP routes (incl. /radar/morning)
  repositories/    # SQL access
  services/        # trends, morning radar, briefs, recommendations, LLM
  collectors/      # RSS, Reddit, Apple Music, Google News, …
  jobs/            # collection + clustering schedule
  core/            # config, database
frontend/src/
  app/             # providers + router
  features/        # radar (Morning Radar), brief, competitors, sources, pricing, contact
  shared/          # api, ui, lib, config
```

---

## Prerequisites

- Python 3.11+
- Node.js 18+

## Run locally

### Backend

```bash
cd backend
python -m venv .venv
```

Windows: `.venv\Scripts\activate`  
macOS/Linux: `source .venv/bin/activate`

```bash
pip install -r ../requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- API: http://localhost:8000  
- Docs: http://localhost:8000/docs  
- Smoke test: `pytest app/tests -q`

On startup RadArt creates the SQLite DB, runs a first collection in the background, then collects again every 15 minutes (configurable).

### Frontend

```bash
cd frontend
npm install
npm run dev
```

App: http://localhost:5173  

Routes: `/dashboard` · `/brief` · `/concurrents` · `/sources` · `/tarifs` · `/contact`

Optional API host:

```bash
set VITE_API_BASE=http://localhost:8000
npm run dev
```

---

## Environment (optional)

Copy `.env.example` to `.env` at the project root.

| Variable | Purpose |
|----------|---------|
| `OPENAI_API_KEY` | Richer brief parsing / copy (optional) |
| `GEMINI_API_KEY` | LLM fallback if OpenAI is unset |
| `YOUTUBE_API_KEY` | YouTube search results |
| `SERPAPI_API_KEY` | Google Trends via SerpApi |
| `META_PAGE_ACCESS_TOKEN` + `META_PAGE_IDS` | Official Graph API for authorized pages |
| `TIKTOK_ACCESS_TOKEN` | Official TikTok API when approved |
| `COLLECTION_INTERVAL_MINUTES` | Default `15` |
| `DATABASE_PATH` | Default `backend/data/radart.db` |
| `CORS_ORIGINS` | Default `*` |

The demo runs **without API keys** (RSS, Reddit RSS, Apple Music charts, Google News RSS, rule-based LLM fallbacks).

---

## Data sources

| Source | What it captures | Key? |
|--------|------------------|------|
| RSS (TN press, Afrique, Billboard, NME, Variety, Verge, Know Your Meme, …) | News, music, entertainment | No |
| Google News RSS (TN / FR / US queries) | Viral, meme, song, sport headlines | No |
| Reddit RSS (`r/Tunisia` + viral mix) | What people hop on | No |
| Apple Music charts (TN / FR / US) | Songs going mainstream | No |
| GDELT | Global news mentions | No |
| Customer-owned JSON exports | Brand/agency Meta–TikTok dumps they have rights to | No (upload) |
| YouTube Data API | Video search | Optional |
| SerpApi Google Trends | Related queries / topics | Optional |
| Meta Graph API | Posts from pages you manage / authorize | Optional |
| TikTok official API | When approved; else customer-owned path | Optional |
| Licensed social firehose | Dense TN FB/IG/TikTok (roadmap) | Partner |

### Legal note

- Collectors use the `RadArtBot/1.0` user agent, timeouts, and curated public URLs only.
- RadArt does **not** scrape private Meta / TikTok feeds or bypass logins. Coverage grows via official APIs, customer-owned exports, and licensed partners.
- See `/sources` → Signal coverage for the live vs needs-key vs forbidden map.
- Hashtags, @mentions, and caption-like text **are** parsed when present in ingested content.
- Google Trends charts are not an official REST API; SerpApi is the optional supported path.

---

## License / status

Hackathon / MVP build for agency media intelligence. Extend with auth, Postgres, and a real job queue when you move beyond the demo.
