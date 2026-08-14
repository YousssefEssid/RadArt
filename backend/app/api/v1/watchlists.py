from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.core.database import get_connection
from app.repositories import watchlist_repository as repo
from app.services.trend_seed_service import expand_seed

router = APIRouter(prefix="/watchlists", tags=["watchlists"])


class WatchlistIn(BaseModel):
    name: str = "Watchlist"
    workspace_id: int = 1


class TermIn(BaseModel):
    term_type: str = Field(..., description="brand|competitor|topic|keyword|hashtag|creator")
    value: str
    lang: str = "mixed"


class AccountIn(BaseModel):
    platform: str
    handle: str
    external_id: str | None = None
    role: str = "creator"


class SeedIn(BaseModel):
    phrase: str


@router.get("")
def list_watchlists(workspace_id: int = 1) -> dict[str, Any]:
    with get_connection() as conn:
        rows = repo.list_watchlists(conn, workspace_id)
        return {"workspace_id": workspace_id, "watchlists": rows}


@router.post("")
def create_watchlist(body: WatchlistIn) -> dict[str, Any]:
    with get_connection() as conn:
        return repo.create_watchlist(conn, body.name, body.workspace_id)


@router.get("/{watchlist_id}")
def get_watchlist(watchlist_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        try:
            return repo.watchlist_bundle(conn, watchlist_id)
        except ValueError as e:
            raise HTTPException(404, str(e)) from e


@router.delete("/{watchlist_id}")
def delete_watchlist(watchlist_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        ok = repo.delete_watchlist(conn, watchlist_id)
        if not ok:
            raise HTTPException(400, "Cannot delete default watchlist or not found")
        return {"deleted": True}


@router.post("/{watchlist_id}/terms")
def add_term(watchlist_id: int, body: TermIn) -> dict[str, Any]:
    with get_connection() as conn:
        if not repo.get_watchlist(conn, watchlist_id):
            raise HTTPException(404, "watchlist not found")
        try:
            return repo.add_term(conn, watchlist_id, body.term_type, body.value, body.lang)
        except ValueError as e:
            raise HTTPException(422, str(e)) from e


@router.delete("/{watchlist_id}/terms/{term_id}")
def delete_term(watchlist_id: int, term_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        ok = repo.delete_term(conn, term_id)
        if not ok:
            raise HTTPException(404, "term not found")
        return {"deleted": True}


@router.post("/{watchlist_id}/accounts")
def add_account(watchlist_id: int, body: AccountIn) -> dict[str, Any]:
    with get_connection() as conn:
        if not repo.get_watchlist(conn, watchlist_id):
            raise HTTPException(404, "watchlist not found")
        try:
            return repo.add_account(
                conn, watchlist_id, body.platform, body.handle, body.external_id, body.role
            )
        except ValueError as e:
            raise HTTPException(422, str(e)) from e


@router.delete("/{watchlist_id}/accounts/{account_id}")
def delete_account(watchlist_id: int, account_id: int) -> dict[str, Any]:
    with get_connection() as conn:
        ok = repo.delete_account(conn, account_id)
        if not ok:
            raise HTTPException(404, "account not found")
        return {"deleted": True}


@router.post("/seed/expand")
def expand_phrase(body: SeedIn) -> dict[str, Any]:
    variants = expand_seed(body.phrase)
    return {"phrase": body.phrase, "variants": variants}
