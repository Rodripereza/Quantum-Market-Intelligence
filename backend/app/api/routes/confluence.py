from fastapi import APIRouter, HTTPException, Query

from app.api.routes.technical import get_technical_analysis
from app.services.market.market_service import MarketService
from app.services.technical.confluence_service import (
    TechnicalConfluenceService,
)
from app.services.technical.liquidity_service import LiquidityService
from app.services.technical.market_structure_service import (
    MarketStructureService,
)
from app.services.technical.support_resistance_service import (
    SupportResistanceService,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

market_service = MarketService()
structure_service = MarketStructureService()
support_resistance_service = SupportResistanceService()
liquidity_service = LiquidityService()
confluence_service = TechnicalConfluenceService()


@router.get("/confluence/{symbol}")
def get_technical_confluence(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
):
    """
    DE-TA-008.1 — Confluence Diagnostics & Explainability

    Auditable QMI technical-fusion layer with per-engine contribution diagnostics.

    Combines:
    - Market Structure
    - Trend
    - Strength
    - Momentum
    - Liquidity
    - Support / Resistance
    - Volume

    Volatility modifies confidence/risk but does not vote directionally.

    This endpoint does NOT issue BUY / HOLD / SELL decisions.
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

        # Reuse QMI's canonical technical endpoint so DE-TA-008.0 consumes
        # exactly the same Trend / Strength / Momentum / Volatility /
        # Volume engines currently displayed by Technical.jsx.
        technical_response = get_technical_analysis(
            symbol=normalized_symbol,
            period=period,
            interval=interval,
        )

        # FastAPI / Pydantic response models are objects, not dictionaries.
        # Convert them explicitly so the Confluence Engine can normalize
        # all engines with the same dict-based contract.
        if hasattr(technical_response, "model_dump"):
            technical = technical_response.model_dump()
        elif hasattr(technical_response, "dict"):
            technical = technical_response.dict()
        elif isinstance(technical_response, dict):
            technical = technical_response
        else:
            technical = vars(technical_response)

        market_structure = structure_service.analyze(
            history=history,
            pivot_window=pivot_window,
            max_swings=20,
        )

        support_resistance = support_resistance_service.analyze(
            history=history,
            pivot_window=pivot_window,
            min_touches=2,
            max_zones=6,
        )

        liquidity = liquidity_service.analyze(
            history=history,
            pivot_window=pivot_window,
            tolerance_pct=0.60,
            min_touches=2,
            max_pools=8,
        )

        result = confluence_service.analyze(
            technical=technical,
            market_structure=market_structure,
            support_resistance=support_resistance,
            liquidity=liquidity,
        )

        return {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "current_price": market_structure.get(
                "current_price"
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
                "Failed to calculate technical confluence. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
