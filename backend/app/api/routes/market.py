from fastapi import APIRouter, HTTPException

from app.services.market.market_service import MarketService

router = APIRouter(
    prefix="/api/market",
    tags=["Market"],
)

service = MarketService()


@router.get("/quote/{symbol}")
def get_quote(symbol: str):
    try:
        return service.get_quote(symbol)
    except Exception as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )
@router.get("/history/{symbol}")
def get_history(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
):
    try:
        return service.get_history(
            symbol=symbol,
            period=period,
            interval=interval,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve historical market data.",
        ) from exc