from fastapi import APIRouter

from app.core.settings import settings

router = APIRouter(tags=["Settings"])


@router.get("/api/settings")
def get_settings():
    return {
        "debug": settings.debug,
        "environment": settings.environment,
        "timezone": settings.default_timezone,
        "currency": settings.default_currency,
        "market": settings.default_market,
    }