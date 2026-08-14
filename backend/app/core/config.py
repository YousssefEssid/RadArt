from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py → parents[2] = backend/, parents[3] = project root
_BACKEND_ROOT = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _BACKEND_ROOT.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    gemini_api_key: str = ""
    youtube_api_key: str = ""
    youtube_max_search_queries_per_run: int = 5

    serpapi_api_key: str = ""
    serpapi_google_trends_geo: str = "TN"
    serpapi_google_trends_hl: str = "fr"
    serpapi_google_trends_date: str = "today 3-m"
    serpapi_google_trends_max_requests_per_run: int = 2
    serpapi_google_trends_include_timeseries: bool = False
    serpapi_google_trends_tz: int | None = None

    # Official Meta Graph — pages the customer manages/authorizes (never scrape private feeds)
    meta_page_access_token: str = ""
    meta_page_ids: str = ""
    instagram_business_account_id: str = ""
    meta_ig_hashtag_enabled: bool = False
    meta_ig_business_discovery_enabled: bool = False
    meta_page_public_content_enabled: bool = False

    # Official TikTok API token when product access is approved
    tiktok_access_token: str = ""

    # Google Trends official API (alpha) — SerpApi remains the live path
    google_trends_api_key: str = ""

    # Social search discovery (SerpApi Google by default)
    search_discovery_api_key: str = ""
    search_discovery_max_queries_per_run: int = 6

    # Experimental providers (never enable unofficial scrapers in prod)
    enable_experimental_collectors: bool = False

    collection_interval_minutes: int = 15
    # Prefer absolute or project-relative path. SQLite today; swap URL later for Postgres.
    database_path: str = str(_BACKEND_ROOT / "data" / "radart.db")

    cors_origins: str = "*"
    api_prefix: str = "/api"

    requests_verify_ssl: bool = True

    @property
    def db_path(self) -> Path:
        p = Path(self.database_path)
        if not p.is_absolute():
            p = _PROJECT_ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    @property
    def cors_origin_list(self) -> list[str]:
        raw = self.cors_origins.strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


settings = Settings()
