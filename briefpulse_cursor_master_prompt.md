# Cursor Master Prompt — RADJ / TrendRadar MVP

You are Cursor acting as a senior full-stack engineer, AI engineer, and product architect.

Build a working hackathon MVP called **RADJ**: an AI-powered media intelligence assistant for communication agencies. The platform must automatically collect media/news/trend signals while the app is running, store them in SQLite, detect trends, match trends with a client brief, and generate campaign recommendations.

The user should not need to manually scrape anything. When the backend starts, the system must initialize the SQLite database, run the first data collection automatically, then continue collecting periodically in the background.

---

## 1. Product goal

RADJ is not a simple news summarizer.

It is a **trend-to-brief intelligence assistant** that:

1. Collects media signals from RSS/news/public sources/YouTube when API key exists/mock social trend files.
2. Cleans and stores everything in SQLite.
3. Groups similar media items into trend clusters.
4. Scores each trend based on volume, recency, source diversity, engagement, and growth.
5. Allows an agency user to enter a client brief.
6. Matches the brief with the most relevant trends.
7. Generates strategic outputs:
   - trend summary,
   - why it matters,
   - relevant sectors,
   - brand fit score,
   - risk score,
   - campaign idea,
   - recommended media format,
   - suggested influencer type,
   - urgency/timing.

The demo must work even without API keys by using RSS feeds and local mock data.

---

## 2. Tech stack

Use this stack:

### Backend
- Python 3.11+
- FastAPI
- SQLite database
- Native `sqlite3` or SQLAlchemy. Prefer native `sqlite3` if faster to implement.
- APScheduler for periodic background collection.
- feedparser for RSS feeds.
- requests + BeautifulSoup4 for allowed public pages only.
- scikit-learn for TF-IDF vectorization and clustering.
- Pydantic for request/response schemas.
- Optional LLM provider through environment variables:
  - `OPENAI_API_KEY`
  - `GEMINI_API_KEY`
  - If no key exists, use rule-based fallback outputs.

### Frontend
- React + Vite
- TypeScript
- Tailwind CSS
- Clean dashboard UI
- Cards, badges, filters, score bars, brief input form.

### Storage
- SQLite file: `backend/data/briefpulse.db`
- No external database.
- Create all tables automatically on backend startup.

---

## 3. Legal and ethical scraping rules

Do not build an aggressive or illegal scraper.

Implement collection in this priority order:

1. RSS feeds.
2. Official APIs when keys exist.
3. Public pages only if allowed by robots.txt and terms.
4. Local mock data for unavailable platforms.

The scraper must:
- use a custom user agent: `RADJHackathonBot/1.0`;
- respect `robots.txt` where possible;
- apply rate limiting with delays;
- avoid login-required pages;
- avoid bypassing paywalls;
- avoid scraping private social media data;
- avoid infinite crawling;
- only collect title, URL, date, source, short text/description, and public engagement metrics when available.

For the hackathon MVP, prioritize RSS + YouTube API optional + mock social trend data.

---

## 4. Project structure

Create this structure:

```txt
briefpulse/
  README.md
  .env.example
  requirements.txt
  backend/
    main.py
    config.py
    db.py
    scheduler.py
    seed_sources.py
    data/
      briefpulse.db
      mock_social_trends.json
    collectors/
      __init__.py
      rss_collector.py
      youtube_collector.py
      gdelt_collector.py
      public_page_collector.py
      mock_social_collector.py
    services/
      __init__.py
      ingestion_service.py
      trend_service.py
      brief_service.py
      recommendation_service.py
      llm_service.py
      scoring_service.py
      text_service.py
    models/
      __init__.py
      schemas.py
    utils/
      __init__.py
      hashing.py
      time_utils.py
      safety.py
  frontend/
    package.json
    index.html
    src/
      main.tsx
      App.tsx
      api.ts
      components/
        Dashboard.tsx
        TrendCard.tsx
        BriefForm.tsx
        SourceStatus.tsx
        ScoreBadge.tsx
        Layout.tsx
      styles.css
```

---

## 5. Backend database schema

Create these SQLite tables automatically on startup.

### `media_items`

```sql
CREATE TABLE IF NOT EXISTS media_items (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  external_id TEXT,
  hash TEXT UNIQUE,
  source TEXT NOT NULL,
  platform TEXT NOT NULL,
  title TEXT NOT NULL,
  text TEXT,
  url TEXT,
  published_at TEXT,
  collected_at TEXT NOT NULL,
  author TEXT,
  engagement INTEGER DEFAULT 0,
  language TEXT,
  category TEXT,
  keywords TEXT,
  entities TEXT,
  sentiment TEXT,
  cluster_id INTEGER,
  raw_json TEXT
);
```

### `trend_clusters`

```sql
CREATE TABLE IF NOT EXISTS trend_clusters (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  label TEXT NOT NULL,
  summary TEXT,
  keywords TEXT,
  category TEXT,
  volume_score REAL DEFAULT 0,
  growth_score REAL DEFAULT 0,
  engagement_score REAL DEFAULT 0,
  diversity_score REAL DEFAULT 0,
  recency_score REAL DEFAULT 0,
  trend_score REAL DEFAULT 0,
  risk_score REAL DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);
```

### `client_briefs`

```sql
CREATE TABLE IF NOT EXISTS client_briefs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  client_name TEXT,
  sector TEXT,
  target TEXT,
  objective TEXT,
  tone TEXT,
  constraints TEXT,
  raw_brief TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

### `recommendations`

```sql
CREATE TABLE IF NOT EXISTS recommendations (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  brief_id INTEGER NOT NULL,
  cluster_id INTEGER NOT NULL,
  brand_fit_score REAL DEFAULT 0,
  risk_score REAL DEFAULT 0,
  recommendation_text TEXT,
  campaign_angle_safe TEXT,
  campaign_angle_bold TEXT,
  campaign_angle_local TEXT,
  suggested_formats TEXT,
  influencer_type TEXT,
  urgency TEXT,
  created_at TEXT NOT NULL,
  FOREIGN KEY (brief_id) REFERENCES client_briefs(id),
  FOREIGN KEY (cluster_id) REFERENCES trend_clusters(id)
);
```

### `collection_runs`

```sql
CREATE TABLE IF NOT EXISTS collection_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  status TEXT,
  items_collected INTEGER DEFAULT 0,
  errors TEXT
);
```

---

## 6. Backend API routes

Implement these routes.

### Health

```http
GET /health
```

Returns:

```json
{
  "status": "ok",
  "db": "connected",
  "scheduler": "running"
}
```

### Trigger collection manually

```http
POST /api/collect/run
```

Runs collection immediately in background and returns:

```json
{
  "message": "collection started"
}
```

### Collection status

```http
GET /api/collect/status
```

Returns last collection runs and source status.

### Media items

```http
GET /api/media-items?limit=50
```

Returns latest media items.

### Trends

```http
GET /api/trends
```

Returns trend clusters ordered by `trend_score DESC`.

Each trend must include:

```json
{
  "id": 1,
  "label": "Canicule en Tunisie",
  "summary": "...",
  "keywords": ["canicule", "chaleur", "météo"],
  "category": "weather/lifestyle",
  "trend_score": 87,
  "risk_score": 42,
  "source_count": 4,
  "item_count": 12,
  "latest_items": []
}
```

### Analyze brief

```http
POST /api/briefs/analyze
```

Input:

```json
{
  "client_name": "Freshy Drink",
  "raw_brief": "We are a beverage brand targeting Tunisian students. We want a humorous summer campaign for engagement. Avoid politics and health claims."
}
```

Output:

```json
{
  "brief_id": 1,
  "parsed_brief": {
    "sector": "beverage",
    "target": "students and young adults",
    "objective": "engagement",
    "tone": "humorous/local",
    "constraints": "avoid politics and health claims"
  },
  "recommendations": []
}
```

### Recommendations

```http
GET /api/briefs/{brief_id}/recommendations
```

Returns recommendations ranked by `brand_fit_score DESC` and `risk_score ASC`.

---

## 7. Automatic data collection

The backend must collect data automatically.

Implement `backend/scheduler.py` using APScheduler.

Rules:

1. Start scheduler on FastAPI startup.
2. Run `collect_all_sources()` immediately once after startup.
3. Run it every 15 minutes.
4. Add endpoint to trigger it manually.
5. Prevent overlapping runs using a global lock or DB status check.
6. Log each run in `collection_runs`.
7. After each collection, automatically run trend detection and update `trend_clusters`.

Pseudo logic:

```python
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        collect_and_process,
        "interval",
        minutes=15,
        id="collect_and_process",
        replace_existing=True,
        max_instances=1
    )
    scheduler.start()
    collect_and_process_async_once()
```

Use FastAPI lifespan or startup event.

---

## 8. Data sources to implement

### 8.1 RSS collector

Create `rss_collector.py`.

Use `feedparser`.

Hardcode initial sources in `seed_sources.py`:

```python
RSS_SOURCES = [
    {
        "name": "Mosaique FM",
        "url": "https://www.mosaiquefm.net/fr/rss",
        "category": "general"
    },
    {
        "name": "TAP News",
        "url": "https://www.tap.info.tn/fr/rss",
        "category": "general"
    },
    {
        "name": "Business News",
        "url": "https://www.businessnews.com.tn/rss",
        "category": "business"
    },
    {
        "name": "Webdo",
        "url": "https://www.webdo.tn/fr/rss",
        "category": "general"
    }
]
```

Important: Some feeds may fail. Do not crash. Catch errors and continue.

Each RSS item becomes a normalized media item:

```python
{
  "source": source_name,
  "platform": "rss",
  "title": title,
  "text": summary,
  "url": link,
  "published_at": published_date,
  "engagement": 0,
  "category": source_category,
  "raw_json": original_entry
}
```

### 8.2 YouTube collector

Create `youtube_collector.py`.

If `YOUTUBE_API_KEY` does not exist, return an empty list and do not crash.

Search these queries:

```python
YOUTUBE_QUERIES = [
    "Tunisie actualité",
    "Tunisie économie",
    "Tunisie sport",
    "Tunisie tendance",
    "Tunisie météo",
    "Ramadan Tunisie",
    "Etudiants Tunisie",
    "inflation Tunisie"
]
```

Limit:
- max 5 results per query.
- cache by URL/hash.
- do not exceed quota.

Normalize:
```python
{
  "source": channel_title,
  "platform": "youtube",
  "title": video_title,
  "text": description,
  "url": "https://www.youtube.com/watch?v=<id>",
  "published_at": published_at,
  "engagement": 0,
  "category": "youtube"
}
```

### 8.3 Mock social trend collector

Create `backend/data/mock_social_trends.json`.

It must always exist so the demo works.

Example data:

```json
[
  {
    "source": "Mock TikTok Tunisia",
    "platform": "mock_social",
    "title": "Students joking about exams and caffeine",
    "text": "Tunisian students are sharing humorous content about exams, sleepless nights, coffee, snacks and stress.",
    "url": "mock://social/exams-caffeine",
    "published_at": "2026-05-01T09:00:00",
    "engagement": 8200,
    "category": "youth"
  },
  {
    "source": "Mock Instagram Tunisia",
    "platform": "mock_social",
    "title": "Summer heat survival memes",
    "text": "Local pages are posting memes about heat, cold drinks, air conditioning and transport during hot days.",
    "url": "mock://social/summer-heat",
    "published_at": "2026-05-01T10:00:00",
    "engagement": 12000,
    "category": "lifestyle"
  },
  {
    "source": "Mock Facebook Tunisia",
    "platform": "mock_social",
    "title": "Price sensitivity and daily shopping",
    "text": "People are discussing grocery prices, promotions, discount stores and budget shopping habits.",
    "url": "mock://social/price-shopping",
    "published_at": "2026-05-01T08:00:00",
    "engagement": 6500,
    "category": "retail"
  }
]
```

### 8.4 GDELT collector, optional

Create `gdelt_collector.py`.

If easy, use simple HTTP requests to GDELT document API with keywords:
- Tunisia
- Tunisie
- Tunisian economy
- Ramadan Tunisia
- tourism Tunisia
- inflation Tunisia

If the request fails, return empty list.

### 8.5 Public page collector, optional

Create `public_page_collector.py`.

Use it only for a curated list of URLs, no broad crawling.

Rules:
- check robots.txt if possible;
- request homepage or specific news pages;
- parse article cards;
- limit to 10 links per site;
- add delay.

If this is too slow, implement a placeholder and rely on RSS/mock.

---

## 9. Data ingestion and deduplication

Create `ingestion_service.py`.

It must:

1. Collect from all collectors.
2. Normalize all items.
3. Generate a stable hash from:
   - platform + source + title + url.
4. Insert into `media_items`.
5. Ignore duplicates.
6. Return number of inserted items.

Hash function:

```python
import hashlib

def stable_hash(*parts):
    base = "||".join([str(p or "").strip().lower() for p in parts])
    return hashlib.sha256(base.encode("utf-8")).hexdigest()
```

---

## 10. Text enrichment

Create `text_service.py`.

For each item, enrich with:

- language detection: simple heuristic is okay.
- keywords: TF-IDF or simple keyword extraction.
- category: rules based on keywords.
- sentiment: simple rule-based positive/neutral/negative.

Category rules:

```python
CATEGORY_KEYWORDS = {
  "politics": ["président", "gouvernement", "ministre", "élection", "parlement", "politique"],
  "economy": ["inflation", "prix", "économie", "marché", "banque", "emploi", "croissance"],
  "sport": ["football", "match", "club", "stade", "derby", "équipe"],
  "weather": ["météo", "pluie", "chaleur", "canicule", "température"],
  "youth": ["étudiant", "examen", "université", "bac", "campus"],
  "retail": ["promotion", "achat", "prix", "magasin", "supermarché", "discount"],
  "culture": ["festival", "musique", "cinéma", "artiste", "concert"]
}
```

---

## 11. Trend detection

Create `trend_service.py`.

Trend detection must run after every collection.

Process:

1. Load media items from the last 72 hours.
2. Build text field = title + text.
3. Vectorize using `TfidfVectorizer`.
4. Cluster using either:
   - `KMeans` when enough items exist,
   - fallback simple grouping by top keywords when few items exist.
5. For each cluster:
   - generate label from top keywords or most representative title;
   - generate short summary;
   - calculate scores;
   - save/update `trend_clusters`;
   - update `media_items.cluster_id`.

### Scoring formula

```python
trend_score = (
    0.30 * volume_score +
    0.25 * growth_score +
    0.20 * engagement_score +
    0.15 * diversity_score +
    0.10 * recency_score
)
```

Score components must be normalized from 0 to 100.

Definitions:

- `volume_score`: number of items in cluster compared to max cluster size.
- `engagement_score`: sum of engagement compared to max engagement.
- `diversity_score`: number of unique sources compared to max source diversity.
- `recency_score`: newer items score higher.
- `growth_score`: compare mentions in last 24h vs previous 24h. If not enough history, use 50 as neutral.

Risk score:
- increase if topic contains politics, religion, tragedy, violence, health claims, death, scandal, crisis;
- decrease if lifestyle, culture, sports, student humor, food, entertainment.

Risk keywords:

```python
RISK_KEYWORDS = [
  "politique", "président", "gouvernement", "religion", "mort", "décès",
  "accident", "crise", "scandale", "attaque", "violence", "maladie",
  "hôpital", "justice", "procès", "terrorisme", "guerre"
]
```

---

## 12. Brief parsing

Create `brief_service.py`.

Input: raw client brief.

Extract:
- client name,
- sector,
- target,
- objective,
- tone,
- constraints,
- period.

Use LLM if API key exists. Otherwise use rules.

Rule-based extraction examples:

- If brief contains `drink`, `beverage`, `boisson`, `café`, sector = `food/beverage`.
- If brief contains `student`, `étudiant`, `Gen Z`, target = `students / Gen Z`.
- If brief contains `engagement`, objective = `engagement`.
- If brief contains `sales`, `conversion`, objective = `conversion`.
- If brief contains `humor`, `funny`, `humour`, tone = `humorous`.
- If brief contains `premium`, tone = `premium`.
- If brief contains `avoid`, `éviter`, constraints = following phrase.

Store parsed brief in `client_briefs`.

---

## 13. Recommendation engine

Create `recommendation_service.py`.

For each trend cluster and brief, calculate brand fit.

```python
brand_fit_score = (
  0.40 * sector_relevance +
  0.25 * target_relevance +
  0.20 * timing_relevance +
  0.15 * tone_compatibility
)
```

Rules:

- Beverage/food fits with weather, youth, exams, culture, sports, lifestyle.
- Telecom fits with youth, sports, events, weather, transport, digital behavior.
- Banking/finance fits with economy, youth, shopping, inflation, entrepreneurship.
- Beauty/skincare fits with weather, lifestyle, health-safe topics, events, women-oriented content.
- Retail fits with price, shopping, promotions, family, back-to-school.
- Tourism fits with culture, weather, events, international news.

Risk adjustment:
- If risk_score > 70, either lower recommendation priority or suggest a safe angle.
- If constraints mention politics, heavily penalize politics trends.
- If constraints mention health claims, penalize health-sensitive trends.

For every matched trend, generate:

1. `recommendation_text`
2. `campaign_angle_safe`
3. `campaign_angle_bold`
4. `campaign_angle_local`
5. `suggested_formats`
6. `influencer_type`
7. `urgency`

Example:

```json
{
  "trend": "Summer heat survival memes",
  "brand_fit_score": 92,
  "risk_score": 35,
  "recommendation_text": "Use the heatwave conversation to position the drink as the fun break of Tunisian summer.",
  "campaign_angle_safe": "Stay fresh during hot days.",
  "campaign_angle_bold": "When Tunisia turns into an oven, your drink becomes the rescue button.",
  "campaign_angle_local": "Chnowa yberred 3lik nhar skhoun? Freshy.",
  "suggested_formats": "TikTok/Reels, story poll, micro-influencer skits",
  "influencer_type": "Tunisian student lifestyle micro-influencers",
  "urgency": "Act within 48 hours"
}
```

If LLM key exists, use LLM to make ideas more creative. If not, use templates.

---

## 14. LLM service

Create `llm_service.py`.

It must be optional.

Function:

```python
def generate_json(prompt: str, fallback: dict) -> dict:
    ...
```

Priority:
1. If `OPENAI_API_KEY` exists, use OpenAI.
2. Else if `GEMINI_API_KEY` exists, use Gemini.
3. Else return fallback.

Do not break the app if no LLM key exists.

All LLM calls must:
- have short prompts;
- request JSON output;
- include fallback handling;
- catch exceptions.

---

## 15. Frontend requirements

Build a dashboard with these sections:

### Top header
- Product name: RADJ
- Subtitle: “From media noise to campaign opportunities”
- Button: “Refresh Data”
- Status: scheduler running / last collection time.

### Left section: Trend Radar
Cards for trends.

Each card shows:
- trend label,
- summary,
- trend score badge,
- risk score badge,
- category,
- number of sources,
- latest items,
- recommended sectors.

### Right section: Brief Analyzer
Form fields:
- Client name
- Raw brief textarea
- Button: “Generate recommendations”

Below form:
- parsed brief chips,
- recommendation cards ranked by brand fit score.

### Recommendation card
Show:
- trend label,
- brand fit score,
- risk score,
- recommended action,
- safe angle,
- bold angle,
- local angle,
- suggested formats,
- influencer type,
- urgency.

### Source status block
Show:
- number of media items,
- number of trend clusters,
- last collection run,
- source success/fail info.

The UI must be clean, modern, hackathon-ready, and responsive.

---

## 16. Frontend API client

Create `frontend/src/api.ts`.

Functions:

```ts
getHealth()
getTrends()
getMediaItems()
getCollectionStatus()
runCollection()
analyzeBrief(payload)
getRecommendations(briefId)
```

Use `fetch` with backend base URL:

```ts
const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";
```

---

## 17. Demo data and fallback behavior

The app must look alive even if real RSS feeds fail.

On first startup:

1. Initialize DB.
2. Insert mock social trends.
3. Try RSS sources.
4. Try optional APIs.
5. Run trend detection.

If no media items exist after collection, insert at least 8 demo items covering:
- summer heat,
- exams/students,
- inflation/price sensitivity,
- football derby,
- tourism,
- cultural festival,
- beauty/skincare in summer,
- transport delays.

This guarantees a working demo.

---

## 18. Commands

Create a `README.md` with exact commands.

### Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r ../requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Environment

Create `.env.example`:

```env
OPENAI_API_KEY=
GEMINI_API_KEY=
YOUTUBE_API_KEY=
COLLECTION_INTERVAL_MINUTES=15
DATABASE_PATH=backend/data/briefpulse.db
```

The app must run without any key.

---

## 19. Acceptance criteria

The project is complete only if all these criteria are met:

1. Running the backend creates SQLite DB automatically.
2. Backend startup automatically launches first collection.
3. Scheduler keeps collecting every 15 minutes.
4. Manual refresh endpoint works.
5. The app does not crash if RSS/API sources fail.
6. Mock social data guarantees demo content.
7. Trend clustering creates at least 5 trend cards.
8. Trend cards show trend score and risk score.
9. User can submit a client brief.
10. The system returns ranked recommendations.
11. Recommendations include safe, bold, and local campaign angles.
12. No external database is required.
13. No API key is mandatory.
14. Frontend can display data from backend.
15. README commands are accurate.

---

## 20. Important implementation details

### Avoid blocking startup forever

Do not make the backend wait too long on startup.

Use short request timeouts:

```python
requests.get(url, timeout=8)
```

Run collection safely in a background thread or scheduler job.

### Prevent duplicate data

Use the hash unique constraint. If insert fails because of duplicate hash, ignore it.

### Handle Arabic/French/English

Do not depend only on English stopwords. Keep vectorization language-neutral.

Good TF-IDF settings:

```python
TfidfVectorizer(
    max_features=1500,
    ngram_range=(1, 2),
    min_df=1
)
```

### Cluster count

Choose cluster count dynamically:

```python
n_clusters = min(8, max(2, len(items) // 4))
```

If fewer than 4 items, do keyword grouping instead.

### Score normalization

Create helper:

```python
def normalize(value, max_value):
    if max_value <= 0:
        return 0
    return min(100, (value / max_value) * 100)
```

### Recency score

Use hours since latest item:

```python
if hours <= 6: score = 100
elif hours <= 24: score = 80
elif hours <= 48: score = 60
elif hours <= 72: score = 40
else: score = 20
```

### Risk score

Start at 20. Add 15 for each matched risk keyword. Cap at 100.

### Urgency

- Trend score >= 80: “Act within 24–48 hours”
- Trend score >= 60: “Use this week”
- Trend score < 60: “Monitor or use as evergreen insight”

---

## 21. Visual design direction

Use a sharp agency/AI dashboard style.

Style:
- dark navy or off-white background;
- cards with rounded corners;
- colored score badges;
- clean typography;
- subtle gradients;
- “radar / signal / pulse” feeling.

Avoid clutter. The jury should understand the value in 20 seconds.

---

## 22. Homepage copy

Use these texts:

### Hero title
`RADJ`

### Subtitle
`From media noise to campaign opportunities.`

### Explanation
`RADJ detects rising media signals, filters them through each client brief, and turns trends into actionable campaign recommendations.`

### CTA
`Analyze a brief`

---

## 23. Example brief for demo

Pre-fill the frontend textarea with:

```txt
Client: Freshy Drink.
We are a beverage brand targeting Tunisian students and young adults.
We want a humorous summer campaign to increase engagement on TikTok and Instagram.
Avoid politics and avoid direct health claims.
```

Expected result:
The platform should recommend trends related to summer heat, exams/students, youth memes, sports/culture, with local humorous angles.

---

## 24. What not to build

Do not build:
- login/authentication;
- payment system;
- complex admin roles;
- full social media scraping;
- infinite web crawler;
- external database;
- complex deployment;
- complicated machine learning training.

Focus on a working, polished, end-to-end MVP.

---

## 25. Final instruction to Cursor

Generate the full project files now.

Prioritize:
1. A backend that runs.
2. Automatic collection and SQLite storage.
3. Trend detection and recommendation endpoints.
4. A clean frontend dashboard.
5. Robust fallback demo data.

After generating files, provide exact run commands and mention any optional environment keys.

The final app must be demo-ready in local development.
