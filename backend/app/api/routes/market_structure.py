from fastapi import APIRouter, HTTPException, Query

from app.services.market.market_service import MarketService
from app.services.technical.market_structure_service import (
    MarketStructureService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

market_service = MarketService()
structure_service = MarketStructureService()


@router.get("/market-structure/{symbol}")
def get_market_structure(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    max_swings: int = Query(default=20, ge=4, le=100),
):
    """
    DE-TA-005.1 — Swing & Trend Structure

    Detects confirmed swing highs/lows, classifies them as
    HH / HL / LH / LL and determines the current structural trend.
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

        result = structure_service.analyze(
            history=history,
            pivot_window=pivot_window,
            max_swings=max_swings,
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
            detail="Failed to calculate market structure.",
        ) from exc
