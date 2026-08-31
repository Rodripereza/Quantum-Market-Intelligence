from fastapi import APIRouter, HTTPException, Query

from app.api.routes.qmi_decision import get_qmi_decision
from app.fundamental.service import FundamentalService
from app.services.qmi_decision_policy_service import QMIDecisionPolicyService


router = APIRouter(
    prefix="/api/qmi",
    tags=["QMI Decision Intelligence"],
)

fundamental_service = FundamentalService()
policy_service = QMIDecisionPolicyService()


@router.get("/decision-snapshot/{symbol}")
def get_qmi_decision_snapshot(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-CORE-005.1 — Shared Decision Context

    Returns one consolidated payload for the frontend:
    - Fundamental analysis
    - DE-CORE-004.0 Cross-Engine Decision
    - DE-CORE-005.0 Action Policy

    The expensive Technical + Fundamental cross-engine calculation is executed
    only once for this request. Action Policy reuses the already-built decision.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        # Build the cross-engine decision once.
        qmi_decision_response = get_qmi_decision(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
            history_limit=history_limit,
        )

        # Fundamental is fetched independently only for the full frontend panel.
        # Market/fundamental provider caches can serve this quickly, while the
        # expensive technical decision tree is NOT repeated.
        fundamental_response = fundamental_service.analyze(
            normalized_symbol
        )

        # Reuse the already-built DE-CORE-004.0 decision directly.
        action_policy_response = policy_service.analyze(
            symbol=normalized_symbol,
            qmi_decision_response=qmi_decision_response,
        )

        fundamental_payload = (
            fundamental_response.model_dump()
            if hasattr(fundamental_response, "model_dump")
            else fundamental_response
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "engine": "QMI Shared Decision Context",
            "engine_id": "DE-CORE-005.1",
            "version": "0.1.0",
            "status": "operational",
            "performance": {
                "shared_decision_context": True,
                "cross_engine_evaluations": 1,
                "action_policy_reuses_cross_engine": True,
                "duplicate_qmi_decision_calls_removed": 1,
                "frontend_requests_consolidated": 3,
            },
            "fundamental": fundamental_payload,
            "qmi_decision_response": qmi_decision_response,
            "action_policy_response": action_policy_response,
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
                "Failed to build shared QMI decision context. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
