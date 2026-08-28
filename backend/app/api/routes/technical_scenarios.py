from fastapi import APIRouter, HTTPException, Query

from app.api.routes.technical_decision import get_technical_decision
from app.services.technical.scenario_service import (
    TechnicalScenarioService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

scenario_service = TechnicalScenarioService()


@router.get("/scenarios/{symbol}")
def get_technical_scenarios(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
):
    """
    DE-TA-009.0 — Technical Scenario Engine

    Builds conditional technical scenarios from the
    DE-TA-008.2 Technical Decision Layer.

    Returns:
    - primary scenario
    - secondary scenario
    - ranked scenario set
    - activation conditions
    - invalidation conditions
    - key reversal requirements

    Plausibility scores are NOT calibrated probabilities.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        decision_response = get_technical_decision(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
        )

        result = scenario_service.analyze(
            decision_response=decision_response,
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "current_price": decision_response.get(
                "current_price"
            ),
            "source_engine_id": decision_response.get(
                "engine_id"
            ),
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
                "Failed to calculate technical scenarios. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
