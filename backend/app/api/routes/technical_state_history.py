from fastapi import APIRouter, HTTPException, Query

from app.api.routes.technical_state_transition import (
    get_technical_state_transition,
)
from app.services.technical.state_history_service import (
    TechnicalStateHistoryService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

state_history_service = TechnicalStateHistoryService()


@router.post("/state-transition/snapshot/{symbol}")
def record_technical_state_snapshot(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
):
    """
    DE-TA-014.1 — Persist current technical state snapshot.

    Computes DE-TA-014.0 and writes the result to the persistent state
    history database. If the state changed versus the previous snapshot,
    a transition audit event is created automatically.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        transition_response = get_technical_state_transition(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
        )

        persistence = state_history_service.record_snapshot(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            current_price=transition_response.get("current_price"),
            transition_response=transition_response,
        )

        return {
            "symbol": normalized_symbol,
            "engine": "QMI Persistent State History & Transition Audit",
            "engine_id": "DE-TA-014.1",
            "version": "0.1.0",
            "status": "operational",
            "source_transition_engine_id": (
                transition_response.get("engine_id")
            ),
            "persistence": persistence,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to persist technical state snapshot. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@router.get("/state-transition/history/{symbol}")
def get_technical_state_history(
    symbol: str,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    DE-TA-014.1 — Read persistent technical state snapshots.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    history = state_history_service.history(
        normalized_symbol,
        limit=limit,
    )

    return {
        "symbol": normalized_symbol,
        "engine_id": "DE-TA-014.1",
        "count": len(history),
        "history": history,
    }


@router.get("/state-transition/audit/{symbol}")
def get_technical_state_transition_audit(
    symbol: str,
    limit: int = Query(default=100, ge=1, le=1000),
):
    """
    DE-TA-014.1 — Read real state-change audit events only.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    transitions = state_history_service.transitions(
        normalized_symbol,
        limit=limit,
    )

    return {
        "symbol": normalized_symbol,
        "engine_id": "DE-TA-014.1",
        "count": len(transitions),
        "transitions": transitions,
    }


@router.get("/state-transition/history-summary/{symbol}")
def get_technical_state_history_summary(symbol: str):
    """
    DE-TA-014.1 — Persistent state-history summary.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    return {
        "engine_id": "DE-TA-014.1",
        **state_history_service.summary(normalized_symbol),
    }
