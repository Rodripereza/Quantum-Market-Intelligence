"""
Trend indicators for Quantum Market Intelligence.

This module contains technical indicators used to identify market trends.
All indicators receive a pandas DataFrame containing, at minimum, a
closing-price column.
"""

from __future__ import annotations

import pandas as pd


class IndicatorInputError(ValueError):
    """Raised when the input data for an indicator is invalid."""


def _validate_market_data(
    market_data: pd.DataFrame,
    price_column: str,
    period: int,
) -> pd.Series:
    """
    Validate the market data and return the requested price series.

    Parameters
    ----------
    market_data:
        DataFrame containing historical market data.
    price_column:
        Name of the column used for the indicator calculation.
    period:
        Number of observations used by the indicator.

    Returns
    -------
    pandas.Series
        Numeric price series.

    Raises
    ------
    IndicatorInputError
        If the input data, column, or period is invalid.
    """

    if not isinstance(market_data, pd.DataFrame):
        raise IndicatorInputError(
            "market_data must be a pandas DataFrame."
        )

    if market_data.empty:
        raise IndicatorInputError(
            "market_data cannot be empty."
        )

    if not isinstance(period, int) or isinstance(period, bool):
        raise IndicatorInputError(
            "period must be an integer."
        )

    if period <= 0:
        raise IndicatorInputError(
            "period must be greater than zero."
        )

    if price_column not in market_data.columns:
        available_columns = ", ".join(
            str(column) for column in market_data.columns
        )

        raise IndicatorInputError(
            f"Column '{price_column}' was not found. "
            f"Available columns: {available_columns}"
        )

    price_series = pd.to_numeric(
        market_data[price_column],
        errors="coerce",
    )

    if price_series.notna().sum() == 0:
        raise IndicatorInputError(
            f"Column '{price_column}' does not contain numeric values."
        )

    return price_series.astype(float)


def calculate_sma(
    market_data: pd.DataFrame,
    period: int = 20,
    price_column: str = "Close",
) -> pd.Series:
    """
    Calculate the Simple Moving Average.

    The SMA is the arithmetic mean of the selected price column over
    the configured period.

    Parameters
    ----------
    market_data:
        DataFrame containing historical market data.
    period:
        Number of observations used by the moving average.
    price_column:
        Column containing the prices used in the calculation.

    Returns
    -------
    pandas.Series
        SMA values aligned with the original DataFrame index.
    """

    prices = _validate_market_data(
        market_data=market_data,
        price_column=price_column,
        period=period,
    )

    sma = prices.rolling(
        window=period,
        min_periods=period,
    ).mean()

    sma.name = f"SMA_{period}"

    return sma


def calculate_ema(
    market_data: pd.DataFrame,
    period: int = 20,
    price_column: str = "Close",
) -> pd.Series:
    """
    Calculate the Exponential Moving Average.

    The EMA gives greater weight to recent observations than the
    Simple Moving Average.

    Parameters
    ----------
    market_data:
        DataFrame containing historical market data.
    period:
        Number of observations used by the moving average.
    price_column:
        Column containing the prices used in the calculation.

    Returns
    -------
    pandas.Series
        EMA values aligned with the original DataFrame index.
    """

    prices = _validate_market_data(
        market_data=market_data,
        price_column=price_column,
        period=period,
    )

    ema = prices.ewm(
        span=period,
        adjust=False,
        min_periods=period,
    ).mean()

    ema.name = f"EMA_{period}"

    return ema