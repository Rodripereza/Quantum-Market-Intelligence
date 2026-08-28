from fastapi import APIRouter, HTTPException, Query

from app.api.routes.support_resistance import get_support_resistance

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
from app.services.technical.decision_synthesis_service import (
    TechnicalDecisionSynthesisService,
)
from app.services.technical.transition_confirmation_service import (
    TechnicalTransitionConfirmationService,
)
from app.services.technical.setup_engine_service import (
    TechnicalSetupEngineService,
)
from app.services.technical.price_plan_service import (
    TechnicalPricePlanService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

transition_confirmation_service = (
    TechnicalTransitionConfirmationService()
)
decision_synthesis_service = TechnicalDecisionSynthesisService()
setup_engine_service = TechnicalSetupEngineService()
price_plan_service = TechnicalPricePlanService()


@router.get("/ui-snapshot/{symbol}")
def get_technical_ui_snapshot(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-CORE-003 — Technical UI Snapshot

    Builds one shared evaluation for the upper technical UI pipeline and
    returns the complete DE-TA-013.0 → DE-TA-015.0 snapshot:

    - Execution Plan
    - State Transition
    - State Persistence
    - Regime Maturity
    - Transition Confirmation
    - Decision Synthesis
    - Technical Setup Qualification
    - Technical Price Plan
    - Support / Resistance context

    The expensive upstream technical context is evaluated only once.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        # 1) Build DE-TA-013.0 once, including its already-computed sources.
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

        # 2) Derive DE-TA-014.0 from the same context.
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
                "upstream_context_reused": True,
                "duplicate_upstream_calls_removed": 5,
            },
            **transition_result,
        }

        # 3) Historical persistence is loaded once.
        persistence_response = get_technical_state_persistence(
            symbol=normalized_symbol,
            limit=history_limit,
        )

        # 4) Derive DE-TA-014.3 from existing 014.0 + 014.2.
        maturity_response = build_regime_maturity_from_context(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            persistence_response=persistence_response,
            transition_response=transition_response,
        )

        # 5) Derive DE-TA-014.4 without re-running the upstream tree.
        confirmation_result = transition_confirmation_service.analyze(
            maturity_response=maturity_response,
            persistence_response=persistence_response,
            transition_response=transition_response,
            execution_response=execution_response,
            action_response=action_response,
            risk_response=risk_response,
        )

        confirmation_response = {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "source_maturity_engine_id": maturity_response.get("engine_id"),
            "source_persistence_engine_id": persistence_response.get("engine_id"),
            "source_transition_engine_id": transition_response.get("engine_id"),
            "source_execution_engine_id": execution_response.get("engine_id"),
            "source_action_engine_id": action_response.get("engine_id"),
            "source_risk_engine_id": risk_response.get("engine_id"),
            "performance": {
                "shared_evaluation_context": True,
                "execution_plan_evaluations": 1,
                "transition_recomputed": False,
                "action_recomputed": False,
                "risk_recomputed": False,
            },
            **confirmation_result,
        }

        # 6) DE-TA-015.0 consumes the already-computed confirmation.
        synthesis_result = decision_synthesis_service.analyze(
            confirmation_response=confirmation_response,
        )

        synthesis_response = {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "source_confirmation_engine_id": confirmation_response.get(
                "engine_id"
            ),
            "performance": {
                "execution_plan_recomputed": False,
                "synthesis_input": "DE-TA-014.4",
                "ui_snapshot_context_reused": True,
            },
            **synthesis_result,
        }

        # 7) DE-TA-016.0 reuses the already-computed 015.0 synthesis.
        setup_result = setup_engine_service.analyze(
            synthesis_response=synthesis_response,
        )

        setup_response = {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "source_synthesis_engine_id": synthesis_response.get("engine_id"),
            "performance": {
                "decision_synthesis_recomputed": False,
                "ui_snapshot_context_reused": True,
            },
            **setup_result,
        }

        # 8) Build DE-TA-006.1 once for the UI and DE-TA-016.1.
        # MarketService cache makes this reuse the same recent history.
        support_resistance_response = get_support_resistance(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
            min_touches=2,
            max_zones=6,
        )

        # 9) DE-TA-016.1 reuses the already-computed 016.0 setup + S/R.
        price_plan_result = price_plan_service.analyze(
            setup_response=setup_response,
            support_resistance_response=support_resistance_response,
        )

        price_plan_response = {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "source_setup_engine_id": setup_response.get("engine_id"),
            "source_support_resistance_engine_id": (
                support_resistance_response.get("engine_id")
            ),
            "performance": {
                "setup_recomputed": False,
                "support_resistance_reused": True,
                "ui_snapshot_context_reused": True,
            },
            **price_plan_result,
        }

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "engine": "QMI Technical UI Snapshot",
            "engine_id": "DE-CORE-003",
            "version": "0.1.0",
            "status": "operational",
            "performance": {
                "shared_evaluation_context": True,
                "execution_plan_evaluations": 1,
                "ui_requests_consolidated": 9,
                "upper_pipeline_recomputations_removed": True,
            },
            "execution_plan": execution_response,
            "state_transition": transition_response,
            "state_persistence": persistence_response,
            "regime_maturity": maturity_response,
            "transition_confirmation": confirmation_response,
            "decision_synthesis": synthesis_response,
            "technical_setup": setup_response,
            "support_resistance": support_resistance_response,
            "technical_price_plan": price_plan_response,
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
                "Failed to calculate technical UI snapshot. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
