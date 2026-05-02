import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Generator, Iterable

from config import settings

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
"""


def get_db_path() -> Path:
    return settings.db_path


def _migrate(conn: sqlite3.Connection) -> None:
    cols = {row[1] for row in conn.execute("PRAGMA table_info(client_briefs)").fetchall()}
    if "competitors_json" not in cols:
        conn.execute("ALTER TABLE client_briefs ADD COLUMN competitors_json TEXT")


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
