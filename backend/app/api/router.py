from fastapi import APIRouter

from app.api.v1 import (
    brands,
    briefs,
    collect,
    competitors,
    health,
    media,
    meta,
    opportunities,
    radar,
    sources,
    trends,
    watchlists,
)

api_router = APIRouter()
api_router.include_router(collect.router)
api_router.include_router(media.router)
api_router.include_router(trends.router)
api_router.include_router(radar.router)
api_router.include_router(opportunities.router)
api_router.include_router(brands.router)
api_router.include_router(sources.router)
api_router.include_router(watchlists.router)
api_router.include_router(meta.router)
api_router.include_router(briefs.router)
api_router.include_router(competitors.router)

# Health stays at root (/health), not under /api
health_router = health.router
