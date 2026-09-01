from fastapi import APIRouter, HTTPException, Query

from app.api.routes.qmi_decision import get_qmi_decision
from app.services.qmi_decision_policy_service import (
    QMIDecisionPolicyService,
)
from app.services.qmi_observation_pipeline_service import (
    QMIObservationPipelineService,
)


router = APIRouter(
    prefix="/api/qmi",
    tags=["QMI Decision Intelligence"],
)

policy_service = QMIDecisionPolicyService()
observation_pipeline_service = QMIObservationPipelineService()


@router.get("/action-policy/{symbol}")
def get_qmi_action_policy(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
    observe: bool = Query(default=True),
):
    """
    DE-CORE-005.2 — Business-Aware Decision Policy / Action Engine
    + DE-CORE-006.2 — Automatic Observation Pipeline

    Builds the action policy from DE-CORE-004.1.

    By default, every successful action-policy calculation is also offered to
    DE-CORE-006.2. Snapshot Policy (006.1) then decides SAVE / SKIP.

    observe=false disables the automatic observation side effect for explicit
    diagnostics or internal calls that must remain read-only.

    No order is executed and portfolio-aware sizing is not included yet.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        qmi_decision_response = get_qmi_decision(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
            history_limit=history_limit,
        )

        result = policy_service.analyze(
            symbol=normalized_symbol,
            qmi_decision_response=qmi_decision_response,
        )

        response = {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "source_cross_engine_id": qmi_decision_response.get("engine_id"),
            **result,
        }

        if observe:
            observation_pipeline = observation_pipeline_service.observe(
                symbol=normalized_symbol,
                period=period,
                interval=interval,
                action_policy_response=response,
                force=False,
                fail_open=True,
            )
        else:
            observation_pipeline = {
                "engine": observation_pipeline_service.ENGINE,
                "engine_id": observation_pipeline_service.ENGINE_ID,
                "version": observation_pipeline_service.VERSION,
                "status": "disabled",
                "symbol": normalized_symbol,
                "mode": "READ_ONLY",
                "snapshot_decision": "SKIP",
                "reason": "OBSERVATION_DISABLED",
                "saved": False,
                "snapshot_id": None,
                "transition_created": False,
            }

        response["observation_pipeline"] = observation_pipeline

        return response

    except HTTPException:
        raise

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to build QMI action policy. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
