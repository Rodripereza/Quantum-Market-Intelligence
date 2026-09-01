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
from app.api.routes.technical_scenarios import router as technical_scenarios_router
from app.api.routes.technical_action import router as technical_action_router
from app.api.routes.technical_risk_exposure import router as technical_risk_exposure_router
from app.api.routes.technical_position_sizing import router as technical_position_sizing_router
from app.api.routes.technical_execution_plan import router as technical_execution_plan_router
from app.api.routes.technical_state_transition import router as technical_state_transition_router
from app.api.routes.technical_state_history import router as technical_state_history_router
from app.api.routes.technical_state_persistence import router as technical_state_persistence_router
from app.api.routes.technical_regime_maturity import router as technical_regime_maturity_router
from app.api.routes.technical_transition_confirmation import router as technical_transition_confirmation_router
from app.api.routes.technical_decision_synthesis import router as technical_decision_synthesis_router
from app.api.routes.technical_ui_snapshot import router as technical_ui_snapshot_router
from app.api.routes.technical_setup_engine import router as technical_setup_engine_router
from app.api.routes.technical_price_plan import router as technical_price_plan_router
from app.api.routes.qmi_decision_history import router as qmi_decision_history_router
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
from app.api.routes.qmi_decision import router as qmi_decision_router
from app.api.routes.qmi_action_policy import router as qmi_action_policy_router
from app.api.routes.qmi_decision_snapshot import router as qmi_decision_snapshot_router
from app.api.routes.nio_deliveries import router as nio_deliveries_router

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
app.include_router(technical_scenarios_router)
app.include_router(technical_action_router)
app.include_router(technical_risk_exposure_router)
app.include_router(technical_position_sizing_router)
app.include_router(technical_execution_plan_router)
app.include_router(technical_state_transition_router)
app.include_router(technical_state_history_router)
app.include_router(technical_state_persistence_router)
app.include_router(technical_regime_maturity_router)
app.include_router(technical_transition_confirmation_router)
app.include_router(technical_decision_synthesis_router)
app.include_router(technical_ui_snapshot_router)
app.include_router(technical_setup_engine_router)
app.include_router(technical_price_plan_router)
app.include_router(qmi_decision_router)
app.include_router(qmi_action_policy_router)
app.include_router(qmi_decision_snapshot_router)
app.include_router(nio_deliveries_router)
app.include_router(qmi_decision_history_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to Quantum Market Intelligence API",
        "application": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
    }