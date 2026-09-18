from fastapi import APIRouter, HTTPException, Query

from app.api.routes.technical_action import (
    get_technical_action_framework,
)
from app.api.routes.technical_decision import (
    get_technical_decision,
)
from app.api.routes.technical_execution_plan import (
    get_technical_execution_plan,
)
from app.api.routes.technical_position_sizing import (
    get_technical_position_sizing,
)
from app.api.routes.technical_risk_exposure import (
    get_technical_risk_exposure,
)
from app.api.routes.technical_scenarios import (
    get_technical_scenarios,
)
from app.services.technical.state_transition_service import (
    TechnicalStateTransitionService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

state_transition_service = TechnicalStateTransitionService()


@router.get("/state-transition/{symbol}")
def get_technical_state_transition(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
):
    """
    DE-TA-014.0 — Technical Monitoring & State Transition Engine

    Detects current technical state, next transition candidate,
    transition readiness and monitoring conditions.

    Persistent transition history is planned for DE-TA-014.1.
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

        action_response = get_technical_action_framework(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
        )

        risk_response = get_technical_risk_exposure(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
        )

        sizing_response = get_technical_position_sizing(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
        )

        execution_response = get_technical_execution_plan(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
        )

        result = state_transition_service.analyze(
            execution_response=execution_response,
            sizing_response=sizing_response,
            risk_response=risk_response,
            action_response=action_response,
            decision_response=decision_response,
            scenario_response=scenario_response,
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "current_price": decision_response.get("current_price"),
            "source_execution_engine_id": execution_response.get("engine_id"),
            "source_sizing_engine_id": sizing_response.get("engine_id"),
            "source_risk_engine_id": risk_response.get("engine_id"),
            "source_action_engine_id": action_response.get("engine_id"),
            "source_decision_engine_id": decision_response.get("engine_id"),
            "source_scenario_engine_id": scenario_response.get("engine_id"),
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
                "Failed to calculate technical state transition. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
