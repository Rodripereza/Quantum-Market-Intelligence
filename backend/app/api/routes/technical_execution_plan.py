from fastapi import APIRouter, HTTPException, Query

from app.api.routes.technical_action import (
    get_technical_action_framework,
)
from app.api.routes.technical_decision import (
    get_technical_decision,
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
from app.services.technical.execution_plan_service import (
    TechnicalExecutionPlanService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

execution_plan_service = TechnicalExecutionPlanService()


@router.get("/execution-plan/{symbol}")
def get_technical_execution_plan(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    include_source_responses: bool = Query(
        default=False,
        include_in_schema=False,
    ),
):
    """
    DE-TA-013.0 — Technical Execution Plan

    DE-CORE-002 phase 1:
    Optionally exposes the already-computed upstream responses so internal
    consumers such as DE-TA-014.0 can reuse them instead of recalculating
    Decision, Scenarios, Action, Risk and Position Sizing.

    Does NOT place orders or use real portfolio capital.
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

        result = execution_plan_service.analyze(
            sizing_response=sizing_response,
            risk_response=risk_response,
            action_response=action_response,
            decision_response=decision_response,
            scenario_response=scenario_response,
        )

        response = {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "current_price": decision_response.get("current_price"),
            "source_sizing_engine_id": sizing_response.get("engine_id"),
            "source_risk_engine_id": risk_response.get("engine_id"),
            "source_action_engine_id": action_response.get("engine_id"),
            "source_decision_engine_id": decision_response.get("engine_id"),
            "source_scenario_engine_id": scenario_response.get("engine_id"),
            **result,
        }

        if include_source_responses:
            response["_evaluation_context"] = {
                "decision_response": decision_response,
                "scenario_response": scenario_response,
                "action_response": action_response,
                "risk_response": risk_response,
                "sizing_response": sizing_response,
            }

        return response

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
                "Failed to calculate technical execution plan. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
