from fastapi import APIRouter, HTTPException, Query

from app.api.routes.support_resistance import get_support_resistance
from app.api.routes.technical_setup_engine import get_technical_setup
from app.services.technical.price_plan_service import (
    TechnicalPricePlanService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

price_plan_service = TechnicalPricePlanService()


@router.get("/price-plan/{symbol}")
def get_technical_price_plan(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
    min_touches: int = Query(default=2, ge=1, le=10),
    max_zones: int = Query(default=6, ge=2, le=20),
):
    """DE-TA-016.1 — Technical Price Plan Engine."""
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        setup_response = get_technical_setup(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
            history_limit=history_limit,
        )

        sr_response = get_support_resistance(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
            pivot_window=pivot_window,
            min_touches=min_touches,
            max_zones=max_zones,
        )

        result = price_plan_service.analyze(
            setup_response=setup_response,
            support_resistance_response=sr_response,
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "source_setup_engine_id": setup_response.get("engine_id"),
            "source_support_resistance_engine_id": sr_response.get("engine_id"),
            **result,
        }

    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to calculate technical price plan. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
