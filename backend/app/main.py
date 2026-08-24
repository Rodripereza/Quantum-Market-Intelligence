from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.health import router as health_router
from app.api.routes.version import router as version_router
from app.api.routes.status import router as status_router
from app.api.routes.settings import router as settings_router
from app.api.routes.market import router as market_router
from app.api.routes.technical import router as technical_router
from app.api.routes.market_structure import router as market_structure_router
from app.api.routes.support_resistance import router as support_resistance_router
from app.api.routes.liquidity import router as liquidity_router
from app.api.routes.confluence import router as confluence_router
from app.api.routes.technical_decision import router as technical_decision_router
from app.exceptions.base_exception import QMIException
from app.exceptions.handlers import (
    generic_exception_handler,
    qmi_exception_handler,
)

from app.core.logging import setup_logging
from app.core.settings import settings
from app.api.routes.test import router as test_router
from app.middleware import RequestContextMiddleware
from app.api.routes.fundamental import router as fundamental_router
from app.core.database import create_db
from app.models.portfolio import PortfolioPosition
from app.api.routes.portfolio import router as portfolio_router
from app.api.routes.auth import router as auth_router
from app.api.routes.news import router as news_router
from app.api.routes.ai import router as ai_router

setup_logging()
create_db()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    debug=settings.debug,
    description="Quantum Market Intelligence backend API",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5174",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(
    QMIException,
    qmi_exception_handler,
)

app.add_exception_handler(
    Exception,
    generic_exception_handler,
)

app.add_middleware(RequestContextMiddleware)
app.include_router(health_router)
app.include_router(version_router)
app.include_router(status_router)
app.include_router(settings_router)
app.include_router(market_router)
app.include_router(technical_router)
app.include_router(market_structure_router)
app.include_router(support_resistance_router)
app.include_router(liquidity_router)
app.include_router(fundamental_router)
app.include_router(portfolio_router)
app.include_router(auth_router)
app.include_router(news_router)
app.include_router(ai_router)
app.include_router(confluence_router)
app.include_router(technical_decision_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Quantum Market Intelligence API",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }