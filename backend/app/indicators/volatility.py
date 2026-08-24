"""
Volatility indicators for Quantum Market Intelligence.

This module contains volatility measurements used by the QMI technical
analysis and scoring engines.
"""

from __future__ import annotations

import pandas as pd
import numpy as np

from app.indicators.trend import IndicatorInputError


def _numeric_column(market_data: pd.DataFrame, column: str) -> pd.Series:
    """Return a validated numeric market-data column."""

    if not isinstance(market_data, pd.DataFrame):
        raise IndicatorInputError("market_data must be a pandas DataFrame.")

    if market_data.empty:
        raise IndicatorInputError("market_data cannot be empty.")

    if column not in market_data.columns:
        raise IndicatorInputError(f"Column '{column}' was not found.")

    series = pd.to_numeric(market_data[column], errors="coerce").astype(float)

    if series.notna().sum() == 0:
        raise IndicatorInputError(
            f"Column '{column}' does not contain numeric values."
        )

    return series


def calculate_true_range(market_data: pd.DataFrame) -> pd.Series:
    """
    Calculate True Range.

    TR is the maximum of:
    - High - Low
    - abs(High - previous Close)
    - abs(Low - previous Close)
    """

    high = _numeric_column(market_data, "High")
    low = _numeric_column(market_data, "Low")
    close = _numeric_column(market_data, "Close")
    previous_close = close.shift(1)

    components = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    )

    true_range = components.max(axis=1)
    true_range.name = "TRUE_RANGE"
    return true_range


def calculate_atr(
    market_data: pd.DataFrame,
    period: int = 14,
) -> pd.Series:
    """
    Calculate Average True Range using Wilder smoothing.

    Parameters
    ----------
    market_data:
        OHLCV DataFrame containing High, Low and Close columns.
    period:
        Wilder smoothing period.
    """

    if not isinstance(period, int) or isinstance(period, bool):
        raise IndicatorInputError("period must be an integer.")

    if period <= 0:
        raise IndicatorInputError("period must be greater than zero.")

    true_range = calculate_true_range(market_data)

    atr = true_range.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    atr.name = f"ATR_{period}"
    return atr



def calculate_historical_volatility(
    market_data: pd.DataFrame,
    period: int = 20,
    price_column: str = "Close",
    annualization: int = 252,
) -> pd.Series:
    """Annualized historical volatility from logarithmic returns."""
    if not isinstance(market_data, pd.DataFrame) or market_data.empty:
        raise ValueError("market_data must be a non-empty pandas DataFrame.")
    if price_column not in market_data.columns:
        raise ValueError(f"Missing price column: {price_column}")
    if period <= 1:
        raise ValueError("period must be greater than 1.")

    prices = pd.to_numeric(market_data[price_column], errors="coerce")
    returns = np.log(prices / prices.shift(1))
    hv = returns.rolling(period, min_periods=period).std(ddof=0) * np.sqrt(annualization)
    hv.name = f"HV_{period}"
    return hv


def calculate_bollinger_bandwidth(
    market_data: pd.DataFrame,
    period: int = 20,
    std_multiplier: float = 2.0,
    price_column: str = "Close",
) -> pd.DataFrame:
    """Calculate Bollinger middle/upper/lower bands and normalized bandwidth."""
    if not isinstance(market_data, pd.DataFrame) or market_data.empty:
        raise ValueError("market_data must be a non-empty pandas DataFrame.")
    if price_column not in market_data.columns:
        raise ValueError(f"Missing price column: {price_column}")
    if period <= 1:
        raise ValueError("period must be greater than 1.")

    prices = pd.to_numeric(market_data[price_column], errors="coerce")
    middle = prices.rolling(period, min_periods=period).mean()
    std = prices.rolling(period, min_periods=period).std(ddof=0)
    upper = middle + std_multiplier * std
    lower = middle - std_multiplier * std
    bandwidth = ((upper - lower) / middle).where(middle != 0)

    return pd.DataFrame(
        {
            f"BB_MIDDLE_{period}": middle,
            f"BB_UPPER_{period}": upper,
            f"BB_LOWER_{period}": lower,
            f"BB_WIDTH_{period}": bandwidth,
        },
        index=market_data.index,
    )
