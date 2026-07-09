from fastapi import APIRouter

from app.core.settings import settings

router = APIRouter(tags=["Version"])


@router.get("/api/version")
def version():
    return {
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }