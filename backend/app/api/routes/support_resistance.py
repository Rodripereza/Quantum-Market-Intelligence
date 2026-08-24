from fastapi import APIRouter, HTTPException, Query

from app.services.market.market_service import MarketService
from app.services.technical.support_resistance_service import (
    SupportResistanceService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

market_service = MarketService()
support_resistance_service = SupportResistanceService()


@router.get("/support-resistance/{symbol}")
def get_support_resistance(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    min_touches: int = Query(default=2, ge=1, le=10),
    max_zones: int = Query(default=6, ge=2, le=20),
):
    """
    DE-TA-006.1 — Support & Resistance Zones

    Returns confirmed structural support/resistance zones,
    zone strength, touches, recency and distance to current price.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        history = market_service.get_history(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
        )

        result = support_resistance_service.analyze(
            history=history,
            pivot_window=pivot_window,
            min_touches=min_touches,
            max_zones=max_zones,
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            **result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate support and resistance zones.",
        ) from exc
