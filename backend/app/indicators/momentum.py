"""
Momentum indicators for Quantum Market Intelligence.

This module contains indicators used to measure price momentum,
trend strength and potential overbought or oversold conditions.
"""

from __future__ import annotations

import pandas as pd

from app.indicators.trend import _validate_market_data


def calculate_rsi(
    market_data: pd.DataFrame,
    period: int = 14,
    price_column: str = "Close",
) -> pd.Series:
    """
    Calculate the Relative Strength Index using Wilder smoothing.

    RSI values normally range between 0 and 100:

    - Above 70 can indicate overbought conditions.
    - Below 30 can indicate oversold conditions.
    - Around 50 represents neutral momentum.

    Parameters
    ----------
    market_data:
        DataFrame containing historical market data.
    period:
        Number of observations used in the calculation.
    price_column:
        Column containing the prices used in the calculation.

    Returns
    -------
    pandas.Series
        RSI values aligned with the original DataFrame index.
    """

    prices = _validate_market_data(
        market_data=market_data,
        price_column=price_column,
        period=period,
    )

    price_change = prices.diff()

    gains = price_change.clip(lower=0.0)
    losses = -price_change.clip(upper=0.0)

    average_gain = gains.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    average_loss = losses.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    relative_strength = average_gain / average_loss

    rsi = 100.0 - (100.0 / (1.0 + relative_strength))

    # Continuous rises produce RSI 100.
    rsi = rsi.mask(
        (average_loss == 0.0) & (average_gain > 0.0),
        100.0,
    )

    # Flat prices represent neutral momentum.
    rsi = rsi.mask(
        (average_loss == 0.0) & (average_gain == 0.0),
        50.0,
    )

    rsi.name = f"RSI_{period}"

    return rsi


def calculate_macd(
    market_data: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
    price_column: str = "Close",
) -> pd.DataFrame:
    """
    Calculate the Moving Average Convergence Divergence indicator.

    MACD consists of:

    - MACD line: fast EMA minus slow EMA.
    - Signal line: EMA of the MACD line.
    - Histogram: MACD line minus signal line.

    Parameters
    ----------
    market_data:
        DataFrame containing historical market data.
    fast_period:
        Period used by the fast exponential moving average.
    slow_period:
        Period used by the slow exponential moving average.
    signal_period:
        Period used by the MACD signal line.
    price_column:
        Column containing the prices used in the calculation.

    Returns
    -------
    pandas.DataFrame
        DataFrame containing the MACD line, signal line and histogram.
    """

    if not isinstance(fast_period, int) or isinstance(fast_period, bool):
        raise ValueError("fast_period must be an integer.")

    if not isinstance(slow_period, int) or isinstance(slow_period, bool):
        raise ValueError("slow_period must be an integer.")

    if not isinstance(signal_period, int) or isinstance(signal_period, bool):
        raise ValueError("signal_period must be an integer.")

    if fast_period <= 0:
        raise ValueError("fast_period must be greater than zero.")

    if slow_period <= 0:
        raise ValueError("slow_period must be greater than zero.")

    if signal_period <= 0:
        raise ValueError("signal_period must be greater than zero.")

    if fast_period >= slow_period:
        raise ValueError(
            "fast_period must be smaller than slow_period."
        )

    prices = _validate_market_data(
        market_data=market_data,
        price_column=price_column,
        period=slow_period,
    )

    fast_ema = prices.ewm(
        span=fast_period,
        adjust=False,
        min_periods=fast_period,
    ).mean()

    slow_ema = prices.ewm(
        span=slow_period,
        adjust=False,
        min_periods=slow_period,
    ).mean()

    macd_line = fast_ema - slow_ema

    signal_line = macd_line.ewm(
        span=signal_period,
        adjust=False,
        min_periods=signal_period,
    ).mean()

    histogram = macd_line - signal_line

    macd_column = f"MACD_{fast_period}_{slow_period}"
    signal_column = f"MACD_SIGNAL_{signal_period}"
    histogram_column = "MACD_HISTOGRAM"

    result = pd.DataFrame(
        {
            macd_column: macd_line,
            signal_column: signal_line,
            histogram_column: histogram,
        },
        index=market_data.index,
    )

    return result


def calculate_stochastic(
    market_data: pd.DataFrame,
    k_period: int = 14,
    d_period: int = 3,
) -> pd.DataFrame:
    """Calculate Fast %K and smoothed %D Stochastic Oscillator."""
    if not isinstance(market_data, pd.DataFrame) or market_data.empty:
        raise ValueError("market_data must be a non-empty pandas DataFrame.")
    if k_period <= 0 or d_period <= 0:
        raise ValueError("k_period and d_period must be greater than zero.")

    required = {"High", "Low", "Close"}
    missing = required.difference(market_data.columns)
    if missing:
        raise ValueError(
            "Stochastic requires columns: " + ", ".join(sorted(missing))
        )

    high = pd.to_numeric(market_data["High"], errors="coerce")
    low = pd.to_numeric(market_data["Low"], errors="coerce")
    close = pd.to_numeric(market_data["Close"], errors="coerce")

    lowest_low = low.rolling(k_period, min_periods=k_period).min()
    highest_high = high.rolling(k_period, min_periods=k_period).max()
    price_range = highest_high - lowest_low

    percent_k = 100.0 * (close - lowest_low) / price_range
    percent_k = percent_k.where(price_range != 0, 50.0)
    percent_d = percent_k.rolling(d_period, min_periods=d_period).mean()

    return pd.DataFrame(
        {
            f"STOCH_K_{k_period}": percent_k,
            f"STOCH_D_{d_period}": percent_d,
        },
        index=market_data.index,
    )


def calculate_roc(
    market_data: pd.DataFrame,
    period: int = 20,
    price_column: str = "Close",
) -> pd.Series:
    """Calculate percentage Rate of Change."""
    prices = _validate_market_data(
        market_data=market_data,
        price_column=price_column,
        period=period + 1,
    )
    roc = prices.pct_change(periods=period) * 100.0
    roc.name = f"ROC_{period}"
    return roc
