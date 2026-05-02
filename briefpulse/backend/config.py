from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    openai_api_key: str = ""
    gemini_api_key: str = ""
    youtube_api_key: str = ""
    # Each search.list call costs 100 quota units (default daily budget is 10,000). Cap searches per run.
    youtube_max_search_queries_per_run: int = 5

    # SerpApi — https://serpapi.com/manage-api-key (Google Trends engine)
    serpapi_api_key: str = ""
    serpapi_google_trends_geo: str = "TN"
    serpapi_google_trends_hl: str = "fr"
    serpapi_google_trends_date: str = "today 3-m"
    # Each RELATED_QUERIES / RELATED_TOPICS / TIMESERIES call uses one SerpApi search credit.
    serpapi_google_trends_max_requests_per_run: int = 2
    serpapi_google_trends_include_timeseries: bool = False
    # Optional tz offset in minutes per SerpApi docs; leave unset to use SerpApi default.
    serpapi_google_trends_tz: int | None = None

    collection_interval_minutes: int = 15
    database_path: str = "backend/data/briefpulse.db"

    # TLS: some regional news sites have incomplete chains; set REQUESTS_VERIFY_SSL=false for local dev only.
    requests_verify_ssl: bool = True

    @property
    def db_path(self) -> Path:
        p = Path(self.database_path)
        if not p.is_absolute():
            p = _ROOT / p
        p.parent.mkdir(parents=True, exist_ok=True)
        return p


settings = Settings()
