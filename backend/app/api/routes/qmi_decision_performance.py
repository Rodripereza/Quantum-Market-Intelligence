from fastapi import APIRouter, HTTPException, Query

from app.services.qmi_decision_performance_analytics_service import (
    QMIDecisionPerformanceAnalyticsService,
)


router = APIRouter(
    prefix="/api/qmi",
    tags=["QMI Decision Intelligence"],
)

performance_service = QMIDecisionPerformanceAnalyticsService()


@router.get("/performance/aggregate")
def get_multi_symbol_decision_performance(
    symbols: str = Query(
        ...,
        description="Comma-separated tickers, e.g. NIO,RKLB",
    ),
    limit_per_symbol: int = Query(default=1000, ge=1, le=5000),
):
    """
    DE-CORE-006.6 — Aggregate analytics across selected tickers.
    """
    try:
        parsed = [
            item.strip().upper()
            for item in symbols.split(",")
            if item.strip()
        ]
        return performance_service.analyze_all(
            parsed,
            limit_per_symbol=limit_per_symbol,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Performance analytics failed. {type(exc).__name__}: {exc}",
        ) from exc


@router.get("/performance/{symbol}")
def get_decision_performance(
    symbol: str,
    limit: int = Query(default=1000, ge=1, le=5000),
):
    """
    DE-CORE-006.6 — Read-only performance analytics for one ticker.
    """
    try:
        return performance_service.analyze_symbol(
            symbol,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Performance analytics failed. {type(exc).__name__}: {exc}",
        ) from exc


