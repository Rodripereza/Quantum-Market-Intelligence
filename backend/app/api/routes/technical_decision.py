from fastapi import APIRouter, HTTPException, Query

from app.api.routes.confluence import get_technical_confluence
from app.services.technical.decision_service import (
    TechnicalDecisionService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

decision_service = TechnicalDecisionService()


@router.get("/decision/{symbol}")
def get_technical_decision(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
):
    """
    DE-TA-008.2.0 — Technical Decision Layer

    Converts Technical Confluence into:
    - Technical Posture
    - Decision Readiness
    - Exposure Context
    - Supporting / Contradictory Evidence
    - Technical Blockers
    - Reversal Requirements
    - Risk Flags

    This endpoint does NOT issue BUY / HOLD / SELL decisions.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        confluence_response = get_technical_confluence(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
        )

        result = decision_service.analyze(
            confluence_response=confluence_response,
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "current_price": confluence_response.get(
                "current_price"
            ),
            "source_engine_id": confluence_response.get(
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
                "Failed to calculate technical decision layer. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
