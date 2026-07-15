"""
Fundamental Analysis API
"""

from fastapi import APIRouter, HTTPException

from app.fundamental.service import FundamentalService
from app.fundamental.schemas import FundamentalInsight

router = APIRouter(
    prefix="/api/fundamental",
    tags=["Fundamental Analysis"],
)

service = FundamentalService()


@router.get(
    "/{symbol}",
    response_model=FundamentalInsight,
    summary="Fundamental Analysis",
)
def get_fundamental_analysis(symbol: str):
    """
    Return the complete QMI fundamental analysis.
    """

    try:
        return service.analyze(symbol.upper())

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )