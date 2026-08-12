"""ASGI entrypoint: `uvicorn main:app` or `uvicorn app.main:app` from backend/."""

from app.main import app

__all__ = ["app"]
