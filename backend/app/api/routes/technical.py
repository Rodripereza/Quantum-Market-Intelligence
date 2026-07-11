"""
Technical analysis API routes for Quantum Market Intelligence.

This module connects the Market Data Engine with the Technical
Analysis Engine.
"""

from __future__ import annotations

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.schemas.technical_schema import TechnicalAnalysisResponse
from app.services.market.market_service import MarketService
from app.services.technical import (
    TechnicalAnalysisError,
    technical_service,
)


router = APIRouter(
    prefix="/api/technical",
    tags=["Technical Analysis"],
)

market_service = MarketService()


def _history_to_dataframe(history: list[dict]) -> pd.DataFrame:
    """
    Convert normalized MarketService history into an OHLCV DataFrame.

    MarketService returns lowercase JSON-compatible field names.
    The indicator engine uses conventional capitalized OHLCV columns.
    """

    if not history:
        raise TechnicalAnalysisError(
            "Historical market data cannot be empty."
        )

    market_data = pd.DataFrame(history)

    required_columns = {
        "date",
        "open",
        "high",
        "low",
        "close",
        "volume",
    }

    missing_columns = required_columns.difference(
        market_data.columns
    )

    if missing_columns:
        missing = ", ".join(sorted(missing_columns))

        raise TechnicalAnalysisError(
            f"Historical market data is missing columns: {missing}."
        )

    market_data = market_data.rename(
        columns={
            "date": "Date",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
    )

    market_data["Date"] = pd.to_datetime(
        market_data["Date"],
        errors="coerce",
    )

    numeric_columns = [
        "Open",
        "High",
        "Low",
        "Close",
        "Volume",
    ]

    for column in numeric_columns:
        market_data[column] = pd.to_numeric(
            market_data[column],
            errors="coerce",
        )

    market_data = (
        market_data
        .dropna(subset=["Date", "Close"])
        .sort_values("Date")
        .drop_duplicates(subset=["Date"], keep="last")
        .reset_index(drop=True)
    )

    if market_data.empty:
        raise TechnicalAnalysisError(
            "Historical market data does not contain valid observations."
        )

    return market_data


@router.get(
    "/{symbol}",
    response_model=TechnicalAnalysisResponse,
    summary="Get Technical Analysis",
    description=(
        "Retrieve historical market data and calculate a complete "
        "technical-analysis snapshot for a financial instrument."
    ),
)
def get_technical_analysis(
    symbol: str,
    period: str = Query(
        default="1y",
        description="Historical period requested from the market provider.",
        examples=["1y"],
    ),
    interval: str = Query(
        default="1d",
        description="Historical data interval.",
        examples=["1d"],
    ),
) -> TechnicalAnalysisResponse:
    """
    Return a complete technical-analysis snapshot for a symbol.
    """

    try:
        history = market_service.get_history(
            symbol=symbol,
            period=period,
            interval=interval,
        )

        market_data = _history_to_dataframe(history)

        result = technical_service.analyze(
            market_data=market_data,
            symbol=symbol,
        )

        return TechnicalAnalysisResponse.model_validate(result)

    except TechnicalAnalysisError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Failed to calculate technical analysis.",
        ) from exc