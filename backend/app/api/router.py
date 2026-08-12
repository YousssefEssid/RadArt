from fastapi import APIRouter

from app.api.v1 import briefs, collect, competitors, health, media, meta, trends

api_router = APIRouter()
api_router.include_router(collect.router)
api_router.include_router(media.router)
api_router.include_router(trends.router)
api_router.include_router(meta.router)
api_router.include_router(briefs.router)
api_router.include_router(competitors.router)

# Health stays at root (/health), not under /api
health_router = health.router
