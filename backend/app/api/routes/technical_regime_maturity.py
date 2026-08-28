from fastapi import APIRouter, HTTPException, Query

from app.api.routes.technical_state_persistence import (
    get_technical_state_persistence,
)
from app.api.routes.technical_state_transition import (
    get_technical_state_transition,
)
from app.services.technical.regime_maturity_service import (
    TechnicalRegimeMaturityService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

regime_maturity_service = TechnicalRegimeMaturityService()


def build_regime_maturity_from_context(
    *,
    symbol: str,
    period: str,
    interval: str,
    persistence_response: dict,
    transition_response: dict,
) -> dict:
    """
    DE-CORE-002 phase 2 internal builder.

    Builds DE-TA-014.3 from already-computed Persistence + Transition
    responses. It performs no upstream technical recomputation.
    """
    result = regime_maturity_service.analyze(
        persistence_response=persistence_response,
        transition_response=transition_response,
    )

    return {
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "source_persistence_engine_id": (
            persistence_response.get("engine_id")
        ),
        "source_transition_engine_id": (
            transition_response.get("engine_id")
        ),
        "performance": {
            "transition_recomputed": False,
            "persistence_recomputed": False,
            "shared_context_reused": True,
        },
        **result,
    }


@router.get("/state-transition/maturity/{symbol}")
def get_technical_regime_maturity(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-TA-014.3 — Regime Maturity & Transition Probability Engine

    Converts DE-TA-014.2 persistence + DE-TA-014.0 transition state into:
    - maturity phase
    - maturity score
    - transition probability
    - target state
    - transition confidence

    DE-CORE-002 phase 2:
    The public endpoint remains backwards-compatible. Internal callers can
    reuse build_regime_maturity_from_context() to avoid recomputing 014.0.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        persistence_response = get_technical_state_persistence(
            symbol=normalized_symbol,
            limit=history_limit,
        )

        transition_response = get_technical_state_transition(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
        )

        result = regime_maturity_service.analyze(
            persistence_response=persistence_response,
            transition_response=transition_response,
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "source_persistence_engine_id": (
                persistence_response.get("engine_id")
            ),
            "source_transition_engine_id": (
                transition_response.get("engine_id")
            ),
            **result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to calculate regime maturity. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
