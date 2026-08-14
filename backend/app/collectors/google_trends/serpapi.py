"""SerpApi Google Trends — live optional path (re-exports legacy via thin module)."""

from app.collectors.serpapi_google_trends_collector import fetch_serpapi_google_trends_items

__all__ = ["fetch_serpapi_google_trends_items"]
