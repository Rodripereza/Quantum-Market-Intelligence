from fastapi import APIRouter, HTTPException, Query

from app.services.qmi_outcome_tracking_service import (
    QMIOutcomeTrackingService,
)


router = APIRouter(
    prefix="/api/qmi",
    tags=["QMI Decision Intelligence"],
)

outcome_service = QMIOutcomeTrackingService()


@router.post("/outcomes/refresh/{symbol}")
def refresh_symbol_outcomes(
    symbol: str,
    snapshot_limit: int = Query(default=100, ge=1, le=1000),
):
    """
    DE-CORE-006.5 — Create/update objective market outcomes for a symbol's
    persisted QMI snapshots.
    """
    try:
        return outcome_service.refresh_symbol(
            symbol,
            snapshot_limit=snapshot_limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Outcome refresh failed. {type(exc).__name__}: {exc}",
        ) from exc


@router.post("/outcomes/refresh-snapshot/{snapshot_id}")
def refresh_snapshot_outcome(snapshot_id: int):
    """Refresh one specific QMI snapshot outcome."""
    try:
        return outcome_service.refresh_snapshot(snapshot_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Outcome refresh failed. {type(exc).__name__}: {exc}",
        ) from exc


@router.post("/outcomes/refresh-pending")
def refresh_pending_outcomes(
    limit: int = Query(default=250, ge=1, le=1000),
):
    """Re-evaluate previously created PENDING/PARTIAL outcomes."""
    try:
        return outcome_service.refresh_pending(limit=limit)
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Pending outcome refresh failed. {type(exc).__name__}: {exc}",
        ) from exc


@router.get("/outcomes/{symbol}")
def get_symbol_outcomes(
    symbol: str,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """Read objective outcome history for a ticker."""
    try:
        outcomes = outcome_service.history(symbol, limit=limit)
        return {
            "symbol": symbol.strip().upper(),
            "engine_id": outcome_service.ENGINE_ID,
            "count": len(outcomes),
            "outcomes": outcomes,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/outcomes/summary/{symbol}")
def get_symbol_outcome_summary(symbol: str):
    """Read DE-CORE-006.5 completion/status summary."""
    try:
        return outcome_service.summary(symbol)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
