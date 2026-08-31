from fastapi import APIRouter, HTTPException, Query

from app.api.routes.technical_ui_snapshot import get_technical_ui_snapshot
from app.fundamental.service import FundamentalService
from app.services.qmi_decision_service import QMIDecisionService


router = APIRouter(
    prefix="/api/qmi",
    tags=["QMI Decision Intelligence"],
)

fundamental_service = FundamentalService()
qmi_decision_service = QMIDecisionService()


@router.get("/decision/{symbol}")
def get_qmi_decision(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-CORE-004.1 — Cross-Engine Decision Fusion + Business Momentum

    Fuses:
    - DE-TA-015.0 Technical Decision Synthesis
    - DE-FA-004.0 Fundamental Decision Engine
    - DE-FA-BM-001.1 Adaptive Business Momentum

    Technical execution/risk gates are preserved. This endpoint does not
    execute trades and does not yet include portfolio or macro constraints.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        technical_snapshot = get_technical_ui_snapshot(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
            history_limit=history_limit,
        )

        technical_response = (
            technical_snapshot.get("decision_synthesis") or {}
        )

        fundamental_response = fundamental_service.analyze(
            normalized_symbol
        )

        result = qmi_decision_service.analyze(
            symbol=normalized_symbol,
            technical_response=technical_response,
            fundamental_response=fundamental_response,
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "source_technical_engine_id": (
                technical_response.get("engine_id")
            ),
            "source_fundamental_engine_id": (
                fundamental_response.data.engine_version
            ),
            "source_fundamental_decision_engine_id": "DE-FA-004.0",
            "source_business_momentum_engine_id": (
                getattr(
                    getattr(fundamental_response, "business_momentum", None),
                    "engine_id",
                    None,
                )
            ),
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
                "Failed to build QMI cross-engine decision. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
