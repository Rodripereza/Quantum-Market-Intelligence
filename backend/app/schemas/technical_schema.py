"""
Pydantic schemas for the QMI Technical Analysis API.

These models define the public contract returned by the technical
analysis endpoints.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class MacdResponse(BaseModel):
    """Latest MACD indicator values."""

    line: float | None = Field(
        default=None,
        description="Latest MACD line value.",
    )
    signal: float | None = Field(
        default=None,
        description="Latest MACD signal-line value.",
    )
    histogram: float | None = Field(
        default=None,
        description="Latest MACD histogram value.",
    )


class TrendResponse(BaseModel):
    """Latest trend-indicator values."""

    sma_20: float | None = Field(
        default=None,
        description="Latest 20-period Simple Moving Average.",
    )
    sma_50: float | None = Field(
        default=None,
        description="Latest 50-period Simple Moving Average.",
    )
    sma_200: float | None = Field(
        default=None,
        description="Latest 200-period Simple Moving Average.",
    )
    ema_20: float | None = Field(
        default=None,
        description="Latest 20-period Exponential Moving Average.",
    )
    ema_50: float | None = Field(
        default=None,
        description="Latest 50-period Exponential Moving Average.",
    )
    ema_200: float | None = Field(
        default=None,
        description="Latest 200-period Exponential Moving Average.",
    )


class MomentumResponse(BaseModel):
    """Latest momentum-indicator values."""

    rsi_14: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Latest 14-period Relative Strength Index.",
    )
    macd: MacdResponse


class TechnicalSignalsResponse(BaseModel):
    """Descriptive signals generated from the technical indicators."""

    trend: str = Field(
        description=(
            "Trend classification: strong_bullish, bullish, neutral, "
            "bearish, strong_bearish or insufficient_data."
        ),
    )
    momentum: str = Field(
        description=(
            "Momentum classification: overbought, neutral, oversold "
            "or insufficient_data."
        ),
    )
    macd: str = Field(
        description=(
            "MACD classification: bullish, neutral, bearish "
            "or insufficient_data."
        ),
    )


class TechnicalAnalysisResponse(BaseModel):
    """Complete technical-analysis snapshot for one market symbol."""

    symbol: str = Field(
        min_length=1,
        description="Normalized financial instrument symbol.",
        examples=["NIO"],
    )
    last_price: float | None = Field(
        default=None,
        description="Latest valid closing price.",
    )
    observations: int = Field(
        ge=1,
        description="Number of historical observations analyzed.",
    )
    trend: TrendResponse
    momentum: MomentumResponse
    signals: TechnicalSignalsResponse