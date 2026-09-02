from fastapi import APIRouter, HTTPException, Query

from app.api.routes.qmi_action_policy import get_qmi_action_policy
from app.services.qmi_scheduled_observation_service import (
    scheduled_observation_service,
)


router = APIRouter(
    prefix="/api/qmi",
    tags=["QMI Decision Intelligence"],
)

scheduled_observation_service.configure_runner(get_qmi_action_policy)


@router.get("/scheduled-observation/status")
def get_scheduled_observation_status():
    """DE-CORE-006.5.1 — Scheduler + registry + automatic outcome refresh."""
    return scheduled_observation_service.status()


@router.get("/scheduled-observation/registry")
def get_scheduled_observation_registry():
    """DE-CORE-006.4.1 — Read persistent ticker registry."""
    return scheduled_observation_service.registry_status()


@router.post("/scheduled-observation/run-now")
async def run_scheduled_observation_now():
    """Run one complete observation cycle immediately."""
    return await scheduled_observation_service.run_cycle()


@router.post("/scheduled-observation/enabled")
def set_scheduled_observation_enabled(
    enabled: bool = Query(...),
):
    """Enable or disable automatic scheduled cycles for this runtime."""
    return scheduled_observation_service.set_enabled(enabled)


@router.post("/scheduled-observation/tickers/{symbol}")
def register_scheduled_ticker(
    symbol: str,
    enabled: bool = Query(default=True),
):
    """Persist a ticker in the scheduled-observation registry."""
    try:
        return scheduled_observation_service.register_ticker(
            symbol,
            enabled=enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/scheduled-observation/tickers/{symbol}/enabled")
def set_scheduled_ticker_enabled(
    symbol: str,
    enabled: bool = Query(...),
):
    """Persist enable/disable state for one registered ticker."""
    try:
        return scheduled_observation_service.set_ticker_enabled(
            symbol,
            enabled,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.delete("/scheduled-observation/tickers/{symbol}")
def remove_scheduled_ticker(symbol: str):
    """Permanently remove a ticker from the observation registry."""
    return scheduled_observation_service.remove_ticker(symbol)


@router.post("/scheduled-observation/refresh-pending-outcomes")
def refresh_scheduled_pending_outcomes(
    limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-CORE-006.5.1 — Administrative/manual diagnostic refresh.

    Normal scheduler cycles already refresh outcomes automatically.
    This endpoint remains available for explicit testing and maintenance.
    """
    return scheduled_observation_service.refresh_pending_outcomes(
        limit=limit,
    )
