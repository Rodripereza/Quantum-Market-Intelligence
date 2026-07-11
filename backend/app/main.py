from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.version import router as version_router
from app.api.routes.status import router as status_router
from app.api.routes.settings import router as settings_router
from app.api.routes.market import router as market_router
from app.api.routes.technical import router as technical_router

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
app.include_router(version_router)
app.include_router(status_router)
app.include_router(settings_router)
app.include_router(market_router)
app.include_router(technical_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Quantum Market Intelligence API",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }