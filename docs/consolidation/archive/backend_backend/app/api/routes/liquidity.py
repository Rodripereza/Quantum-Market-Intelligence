from fastapi import APIRouter, HTTPException, Query

from app.services.market.market_service import MarketService
from app.services.technical.liquidity_service import LiquidityService


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

market_service = MarketService()
liquidity_service = LiquidityService()


@router.get("/liquidity/{symbol}")
def get_liquidity(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    tolerance_pct: float = Query(default=0.60, ge=0.05, le=5.0),
    min_touches: int = Query(default=2, ge=2, le=10),
    max_pools: int = Query(default=8, ge=2, le=30),
):
    """
    DE-TA-007.5 — Liquidity Cluster State & Bias Engine

    Detects BSL/SSL pools, institutional sweeps, cluster lifecycle and liquidity bias context.
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

        result = liquidity_service.analyze(
            history=history,
            pivot_window=pivot_window,
            tolerance_pct=tolerance_pct,
            min_touches=min_touches,
            max_pools=max_pools,
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
            detail="Failed to calculate liquidity pools.",
        ) from exc
