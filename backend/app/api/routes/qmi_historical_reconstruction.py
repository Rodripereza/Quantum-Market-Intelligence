from fastapi import APIRouter, HTTPException, Query

from app.services.qmi_historical_reconstruction_service import (
    QMIHistoricalReconstructionService,
)


router = APIRouter(
    prefix="/api/qmi",
    tags=["QMI Decision Intelligence"],
)

reconstruction_service = QMIHistoricalReconstructionService()


@router.get("/historical-reconstruction/{symbol}")
def get_qmi_historical_reconstruction(
    symbol: str,
    limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-CORE-006.3.1 — Reconstruct historical QMI state evolution.

    Read-only endpoint. Consecutive snapshots with the same ACTION are grouped
    into episodes and historical transitions are enriched with episode context.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(status_code=400, detail="Ticker symbol is required.")

    try:
        return reconstruction_service.reconstruct(
            normalized_symbol,
            limit=limit,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to reconstruct QMI historical state. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc


@router.get("/state-transition-intelligence/{symbol}")
def get_qmi_state_transition_intelligence(
    symbol: str,
    limit: int = Query(default=500, ge=1, le=1000),
):
    """
    DE-CORE-006.3.1 — Explain QMI action transitions.

    Returns transition sequence, primary driver, driver family,
    confirmation breadth and a concise interpretation of WHY QMI changed.
    """
    normalized_symbol = symbol.strip().upper()

    if not normalized_symbol:
        raise HTTPException(
            status_code=400,
            detail="Ticker symbol is required.",
        )

    try:
        return reconstruction_service.transition_intelligence(
            normalized_symbol,
            limit=limit,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Failed to build QMI state transition intelligence. "
                f"{type(exc).__name__}: {exc}"
            ),
        ) from exc
