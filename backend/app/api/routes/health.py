from fastapi import APIRouter

from app.core.settings import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
def health():
    return {
        "status": "ok",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }