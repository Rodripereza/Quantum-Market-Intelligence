from fastapi import APIRouter, HTTPException, Query

from app.services.qmi_calibration_learning_service import (
    QMICalibrationLearningService,
)


router = APIRouter(
    prefix="/api/qmi",
    tags=["QMI Decision Intelligence"],
)

calibration_service = QMICalibrationLearningService()


# Static route MUST remain before /calibration/{symbol}.
@router.get("/calibration/aggregate")
def get_multi_symbol_calibration(
    symbols: str = Query(
        ...,
        description="Comma-separated tickers, e.g. NIO,RKLB",
    ),
    limit_per_symbol: int = Query(default=1000, ge=1, le=5000),
):
    """
    DE-CORE-006.7 — Aggregate calibration evidence across selected tickers.
    """
    try:
        parsed = [
            item.strip().upper()
            for item in symbols.split(",")
            if item.strip()
        ]
        return calibration_service.analyze_all(
            parsed,
            limit_per_symbol=limit_per_symbol,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Calibration analysis failed. {type(exc).__name__}: {exc}",
        ) from exc


@router.get("/calibration/{symbol}")
def get_symbol_calibration(
    symbol: str,
    limit: int = Query(default=1000, ge=1, le=5000),
):
    """
    DE-CORE-006.7 — Read-only calibration evidence for one ticker.
    """
    try:
        return calibration_service.analyze_symbol(
            symbol,
            limit=limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Calibration analysis failed. {type(exc).__name__}: {exc}",
        ) from exc
