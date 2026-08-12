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
