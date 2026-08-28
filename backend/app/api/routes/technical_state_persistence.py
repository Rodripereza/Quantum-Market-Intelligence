from fastapi import APIRouter, HTTPException, Query

from app.services.technical.state_history_service import (
    TechnicalStateHistoryService,
)
from app.services.technical.state_persistence_service import (
    TechnicalStatePersistenceService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

history_service = TechnicalStateHistoryService()
persistence_service = TechnicalStatePersistenceService()


@router.get("/state-transition/persistence/{symbol}")
def get_technical_state_persistence(
    symbol: str,
    limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-TA-014.2 — State Persistence & Regime Duration Engine

    Interprets persistent DE-TA-014.1 history and returns:
    - current-state duration
    - consecutive snapshots
    - persistence strength
    - regime stability
    - state score trend
    - transition readiness trend
    - next-state pressure
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        history = history_service.history(
            normalized_symbol,
            limit=limit,
        )

        transitions = history_service.transitions(
            normalized_symbol,
            limit=limit,
        )

        result = persistence_service.analyze(
            history=history,
            transitions=transitions,
        )

        return {
            "symbol": normalized_symbol,
            "source_history_engine_id": "DE-TA-014.1",
            **result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to calculate technical state persistence. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
