from fastapi import APIRouter, HTTPException, Query

from app.api.routes.technical_decision import (
    get_technical_decision,
)
from app.api.routes.technical_scenarios import (
    get_technical_scenarios,
)
from app.services.technical.action_service import (
    TechnicalActionService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

action_service = TechnicalActionService()


@router.get("/action-framework/{symbol}")
def get_technical_action_framework(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
):
    """
    DE-TA-010.0 — Technical Action Framework

    Converts Decision + Scenario evidence into:
    - action posture
    - technical permissions
    - action readiness
    - entry constraints
    - confirmation gates
    - invalidation gates
    - escalation / downgrade conditions

    This endpoint does NOT issue BUY / HOLD / SELL.
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

        scenario_response = get_technical_scenarios(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
        )

        result = action_service.analyze(
            decision_response=decision_response,
            scenario_response=scenario_response,
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "current_price": decision_response.get(
                "current_price"
            ),
            "source_decision_engine_id": (
                decision_response.get("engine_id")
            ),
            "source_scenario_engine_id": (
                scenario_response.get("engine_id")
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
                "Failed to calculate technical action framework. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
