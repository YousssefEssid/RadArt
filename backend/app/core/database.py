import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator

from app.core.config import settings

SCHEMA = """
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

CREATE TABLE IF NOT EXISTS collection_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  started_at TEXT NOT NULL,
  ended_at TEXT,
  status TEXT,
  items_collected INTEGER DEFAULT 0,
  errors TEXT
);

CREATE TABLE IF NOT EXISTS brand_profiles (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  brand_name TEXT NOT NULL,
  industry TEXT,
  country TEXT DEFAULT 'Tunisia',
  audience TEXT,
  personality TEXT,
  languages_json TEXT,
  competitors_json TEXT,
  channels_json TEXT,
  objectives_json TEXT,
  forbidden_topics_json TEXT,
  tone TEXT,
  previous_campaigns TEXT,
  brand_guidelines_text TEXT,
  products TEXT,
  budget_level TEXT,
  is_active INTEGER DEFAULT 1,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlists (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  workspace_id INTEGER NOT NULL DEFAULT 1,
  name TEXT NOT NULL,
  is_default INTEGER DEFAULT 0,
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS watchlist_terms (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  watchlist_id INTEGER NOT NULL,
  term_type TEXT NOT NULL,
  value TEXT NOT NULL,
  lang TEXT DEFAULT 'mixed',
  created_at TEXT NOT NULL,
  UNIQUE(watchlist_id, term_type, value),
  FOREIGN KEY (watchlist_id) REFERENCES watchlists(id)
);

CREATE TABLE IF NOT EXISTS watchlist_accounts (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  watchlist_id INTEGER NOT NULL,
  platform TEXT NOT NULL,
  handle TEXT NOT NULL,
  external_id TEXT,
  role TEXT DEFAULT 'creator',
  created_at TEXT NOT NULL,
  UNIQUE(watchlist_id, platform, handle),
  FOREIGN KEY (watchlist_id) REFERENCES watchlists(id)
);

CREATE TABLE IF NOT EXISTS collector_health_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  source TEXT NOT NULL,
  status TEXT,
  items INTEGER DEFAULT 0,
  error TEXT,
  ran_at TEXT NOT NULL
);
"""

_MEDIA_EXTRA_COLS = [
    ("source_type", "TEXT"),
    ("source_method", "TEXT"),
    ("provider", "TEXT"),
    ("author_name", "TEXT"),
    ("author_external_id", "TEXT"),
    ("views", "INTEGER"),
    ("likes", "INTEGER"),
    ("comments", "INTEGER"),
    ("shares", "INTEGER"),
    ("hashtags", "TEXT"),
    ("mentions", "TEXT"),
    ("country", "TEXT"),
    ("confidence", "REAL"),
    ("raw_metadata_json", "TEXT"),
]


def get_db_path() -> Path:
    return settings.db_path


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(client_briefs)").fetchall()}
    if "competitors_json" not in cols:
        conn.execute("ALTER TABLE client_briefs ADD COLUMN competitors_json TEXT")

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS brand_profiles (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          brand_name TEXT NOT NULL,
          industry TEXT,
          country TEXT DEFAULT 'Tunisia',
          audience TEXT,
          personality TEXT,
          languages_json TEXT,
          competitors_json TEXT,
          channels_json TEXT,
          objectives_json TEXT,
          forbidden_topics_json TEXT,
          tone TEXT,
          previous_campaigns TEXT,
          brand_guidelines_text TEXT,
          products TEXT,
          budget_level TEXT,
          is_active INTEGER DEFAULT 1,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        )
        """
    )

    media_cols = {row[1] for row in conn.execute("PRAGMA table_info(media_items)").fetchall()}
    for name, typ in _MEDIA_EXTRA_COLS:
        if name not in media_cols:
            conn.execute(f"ALTER TABLE media_items ADD COLUMN {name} {typ}")

    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS watchlists (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          workspace_id INTEGER NOT NULL DEFAULT 1,
          name TEXT NOT NULL,
          is_default INTEGER DEFAULT 0,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS watchlist_terms (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          watchlist_id INTEGER NOT NULL,
          term_type TEXT NOT NULL,
          value TEXT NOT NULL,
          lang TEXT DEFAULT 'mixed',
          created_at TEXT NOT NULL,
          UNIQUE(watchlist_id, term_type, value),
          FOREIGN KEY (watchlist_id) REFERENCES watchlists(id)
        );
        CREATE TABLE IF NOT EXISTS watchlist_accounts (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          watchlist_id INTEGER NOT NULL,
          platform TEXT NOT NULL,
          handle TEXT NOT NULL,
          external_id TEXT,
          role TEXT DEFAULT 'creator',
          created_at TEXT NOT NULL,
          UNIQUE(watchlist_id, platform, handle),
          FOREIGN KEY (watchlist_id) REFERENCES watchlists(id)
        );
        CREATE TABLE IF NOT EXISTS collector_health_runs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          source TEXT NOT NULL,
          status TEXT,
          items INTEGER DEFAULT 0,
          error TEXT,
          ran_at TEXT NOT NULL
        );
        """
    )


def init_db() -> None:
    path = get_db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(path) as conn:
        conn.executescript(SCHEMA)
        _migrate(conn)
        conn.commit()


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return {k: row[k] for k in row.keys()}


def fetch_all(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> list[dict[str, Any]]:
    cur = conn.execute(sql, params)
    return [row_to_dict(r) for r in cur.fetchall()]


def fetch_one(conn: sqlite3.Connection, sql: str, params: tuple = ()) -> dict[str, Any] | None:
    cur = conn.execute(sql, params)
    row = cur.fetchone()
    return row_to_dict(row) if row else None
