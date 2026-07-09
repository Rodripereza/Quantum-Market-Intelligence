from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.core.logging import setup_logging
from app.core.settings import settings


setup_logging()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="Quantum Market Intelligence backend API",
)


app.include_router(health_router)


@app.get("/")
def root():
    return {
        "message": "Welcome to Quantum Market Intelligence API",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }