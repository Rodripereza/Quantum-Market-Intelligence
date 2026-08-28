from fastapi import APIRouter, HTTPException, Query
from app.api.routes.technical_decision_synthesis import get_technical_decision_synthesis
from app.services.technical.setup_engine_service import TechnicalSetupEngineService

router = APIRouter(prefix="/api/technical", tags=["Technical Analysis"])
setup_engine_service = TechnicalSetupEngineService()


@router.get("/setup/{symbol}")
def get_technical_setup(
    symbol: str,
    period: str = Query(default="1y"),
    interval: str = Query(default="1d"),
    pivot_window: int = Query(default=3, ge=1, le=20),
    history_limit: int = Query(default=500, ge=1, le=1000),
):
    """DE-TA-016.0 — Technical Opportunity / Setup Qualification Engine."""
    normalized_symbol = symbol.strip().upper()
    if not normalized_symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol is required.")
    try:
        synthesis_response = get_technical_decision_synthesis(
            symbol=normalized_symbol, period=period, interval=interval,
            pivot_window=pivot_window, history_limit=history_limit,
        )
        result = setup_engine_service.analyze(synthesis_response=synthesis_response)
        return {
            "symbol": normalized_symbol, "period": period, "interval": interval,
            "source_synthesis_engine_id": synthesis_response.get("engine_id"),
            **result,
        }
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate technical setup. {type(exc).__name__}: {exc}",
        ) from exc
