from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, HTTPException, UploadFile
from pydantic import BaseModel, Field

from app.core.database import get_connection
from app.repositories import brand as brand_repo
from app.services.brief_file_extract import extract_text_from_filename_and_bytes

router = APIRouter(prefix="/brands", tags=["brands"])


class BrandDNAIn(BaseModel):
    brand_name: str = Field(..., min_length=1, max_length=200)
    industry: str | None = None
    country: str | None = "Tunisia"
    audience: str | None = None
    personality: str | None = None
    languages: list[str] = Field(default_factory=list)
    competitors: list[str] = Field(default_factory=list)
    channels: list[str] = Field(default_factory=list)
    objectives: list[str] = Field(default_factory=list)
    forbidden_topics: list[str] = Field(default_factory=list)
    tone: str | None = None
    previous_campaigns: str | None = None
    brand_guidelines_text: str | None = None
    products: str | None = None
    budget_level: str | None = Field(None, description="€ | €€ | €€€")


@router.get("/active")
def get_active_brand() -> dict[str, Any]:
    with get_connection() as conn:
        brand = brand_repo.get_active_brand(conn)
        return brand or {}


@router.get("/")
def list_brands() -> list[dict[str, Any]]:
    with get_connection() as conn:
        return brand_repo.list_brands(conn)


@router.post("/")
def create_brand(body: BrandDNAIn) -> dict[str, Any]:
    with get_connection() as conn:
        return brand_repo.upsert_brand(conn, body.model_dump())


@router.put("/{brand_id}")
def update_brand(brand_id: int, body: BrandDNAIn) -> dict[str, Any]:
    with get_connection() as conn:
        existing = brand_repo.get_brand(conn, brand_id)
        if not existing:
            raise HTTPException(404, "brand not found")
        return brand_repo.upsert_brand(conn, body.model_dump(), brand_id=brand_id)


@router.post("/guidelines/extract-text")
async def extract_guidelines(file: UploadFile = File(...)) -> dict[str, str]:
    raw = await file.read()
    if len(raw) > 12 * 1024 * 1024:
        raise HTTPException(413, "Fichier trop volumineux (max 12 Mo).")
    if not raw:
        raise HTTPException(422, "Fichier vide.")
    try:
        text = extract_text_from_filename_and_bytes(file.filename or "guidelines", raw)
    except ValueError as e:
        raise HTTPException(422, str(e)) from e
    return {"text": text, "filename": file.filename or ""}
