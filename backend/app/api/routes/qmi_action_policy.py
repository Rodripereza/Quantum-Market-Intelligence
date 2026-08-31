from fastapi import APIRouter, HTTPException, Query

from app.api.routes.qmi_decision import get_qmi_decision
from app.services.qmi_decision_policy_service import (
    QMIDecisionPolicyService,
)


router = APIRouter(
    prefix="/api/qmi",
    tags=["QMI Decision Intelligence"],
)

policy_service = QMIDecisionPolicyService()


@router.get("/action-policy/{symbol}")
def get_qmi_action_policy(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-CORE-005.2 — Business-Aware Decision Policy / Action Engine

    Converts DE-CORE-004.1 Cross-Engine Decision Fusion into an advisory
    operational policy:
    ADD / HOLD / REDUCE / EXIT / WAIT, enriched with Business Momentum and divergence context.

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

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "source_cross_engine_id": qmi_decision_response.get("engine_id"),
            **result,
        }

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
