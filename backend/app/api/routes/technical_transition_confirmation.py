from fastapi import APIRouter, HTTPException, Query

from app.api.routes.technical_execution_plan import (
    get_technical_execution_plan,
)
from app.api.routes.technical_regime_maturity import (
    build_regime_maturity_from_context,
)
from app.api.routes.technical_state_persistence import (
    get_technical_state_persistence,
)
from app.api.routes.technical_state_transition import (
    state_transition_service,
)
from app.services.technical.transition_confirmation_service import (
    TechnicalTransitionConfirmationService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

transition_confirmation_service = (
    TechnicalTransitionConfirmationService()
)


@router.get("/state-transition/confirmation/{symbol}")
def get_technical_transition_confirmation(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-TA-014.4 — Transition Confirmation & State Change Engine

    DE-CORE-002 phase 2:
    Builds the expensive technical evaluation once through DE-TA-013.0,
    reuses its Decision / Scenarios / Action / Risk / Sizing responses,
    derives DE-TA-014.0 from that shared context, and derives DE-TA-014.3
    from the already-computed Transition + Persistence responses.

    This removes the previous repeated calls to:
    - DE-TA-014.3 as a standalone cascade
    - DE-TA-014.0 as a standalone cascade
    - DE-TA-013.0 a second time
    - DE-TA-010.0 Action a second time
    - DE-TA-011.0 Risk a second time

    The endpoint does not mutate persistent state history.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        # 1) Build the expensive upstream evaluation once.
        execution_response = get_technical_execution_plan(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
            include_source_responses=True,
        )

        evaluation_context = (
            execution_response.pop("_evaluation_context", None) or {}
        )

        decision_response = (
            evaluation_context.get("decision_response") or {}
        )
        scenario_response = (
            evaluation_context.get("scenario_response") or {}
        )
        action_response = (
            evaluation_context.get("action_response") or {}
        )
        risk_response = (
            evaluation_context.get("risk_response") or {}
        )
        sizing_response = (
            evaluation_context.get("sizing_response") or {}
        )

        missing_sources = [
            name
            for name, value in {
                "decision_response": decision_response,
                "scenario_response": scenario_response,
                "action_response": action_response,
                "risk_response": risk_response,
                "sizing_response": sizing_response,
            }.items()
            if not value
        ]

        if missing_sources:
            raise RuntimeError(
                "Execution Plan did not expose the expected evaluation "
                f"context: {', '.join(missing_sources)}"
            )

        # 2) Build DE-TA-014.0 directly from the shared 013 context.
        transition_result = state_transition_service.analyze(
            execution_response=execution_response,
            sizing_response=sizing_response,
            risk_response=risk_response,
            action_response=action_response,
            decision_response=decision_response,
            scenario_response=scenario_response,
        )

        transition_response = {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "current_price": decision_response.get(
                "current_price",
                execution_response.get("current_price"),
            ),
            "source_execution_engine_id": execution_response.get("engine_id"),
            "source_sizing_engine_id": sizing_response.get("engine_id"),
            "source_risk_engine_id": risk_response.get("engine_id"),
            "source_action_engine_id": action_response.get("engine_id"),
            "source_decision_engine_id": decision_response.get("engine_id"),
            "source_scenario_engine_id": scenario_response.get("engine_id"),
            "performance": {
                "execution_plan_recomputed": False,
                "upstream_context_reused": True,
                "duplicate_upstream_calls_removed": 5,
            },
            **transition_result,
        }

        # 3) Persistence is historical and comparatively cheap; calculate once.
        persistence_response = get_technical_state_persistence(
            symbol=normalized_symbol,
            limit=history_limit,
        )

        # 4) Build DE-TA-014.3 from already-computed 014.0 + 014.2.
        maturity_response = build_regime_maturity_from_context(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            persistence_response=persistence_response,
            transition_response=transition_response,
        )

        # 5) Confirmation consumes the exact same contracts as before.
        result = transition_confirmation_service.analyze(
            maturity_response=maturity_response,
            persistence_response=persistence_response,
            transition_response=transition_response,
            execution_response=execution_response,
            action_response=action_response,
            risk_response=risk_response,
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "source_maturity_engine_id": (
                maturity_response.get("engine_id")
            ),
            "source_persistence_engine_id": (
                persistence_response.get("engine_id")
            ),
            "source_transition_engine_id": (
                transition_response.get("engine_id")
            ),
            "source_execution_engine_id": (
                execution_response.get("engine_id")
            ),
            "source_action_engine_id": (
                action_response.get("engine_id")
            ),
            "source_risk_engine_id": (
                risk_response.get("engine_id")
            ),
            "performance": {
                "shared_evaluation_context": True,
                "execution_plan_evaluations": 1,
                "transition_recomputed": False,
                "maturity_transition_recomputed": False,
                "action_recomputed": False,
                "risk_recomputed": False,
            },
            **result,
        }

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to calculate transition confirmation. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
