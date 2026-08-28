from fastapi import APIRouter, HTTPException, Query

from app.api.routes.technical_transition_confirmation import (
    get_technical_transition_confirmation,
)
from app.services.technical.decision_synthesis_service import (
    TechnicalDecisionSynthesisService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

decision_synthesis_service = TechnicalDecisionSynthesisService()


@router.get("/decision-synthesis/{symbol}")
def get_technical_decision_synthesis(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-TA-015.0 — Technical Decision Synthesis Engine
    Performance revision 0.1.1

    Produces one final deterministic technical posture from DE-TA-014.4.

    DE-TA-014.4 already evaluates execution, action and risk. The synthesis
    engine therefore reuses that context instead of recalculating
    DE-TA-013.0 a second time.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        confirmation_response = (
            get_technical_transition_confirmation(
                symbol=normalized_symbol,
                period=period,
                interval=interval,
                pivot_window=pivot_window,
                history_limit=history_limit,
            )
        )

        result = decision_synthesis_service.analyze(
            confirmation_response=confirmation_response,
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "source_confirmation_engine_id": (
                confirmation_response.get("engine_id")
            ),
            "performance": {
                "execution_plan_recomputed": False,
                "synthesis_input": "DE-TA-014.4",
            },
            **result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to calculate technical decision synthesis. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
