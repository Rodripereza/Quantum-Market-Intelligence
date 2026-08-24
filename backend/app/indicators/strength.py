"""Trend-strength indicators for Quantum Market Intelligence."""

from __future__ import annotations

import pandas as pd

from app.indicators.trend import IndicatorInputError


def calculate_adx_dmi(
    market_data: pd.DataFrame,
    period: int = 14,
) -> pd.DataFrame:
    """
    Calculate Wilder ADX, +DI and -DI.

    Returns columns ADX_14, PLUS_DI_14 and MINUS_DI_14 by default.
    """
    if not isinstance(market_data, pd.DataFrame) or market_data.empty:
        raise IndicatorInputError("market_data must be a non-empty pandas DataFrame.")
    if not isinstance(period, int) or isinstance(period, bool) or period <= 0:
        raise IndicatorInputError("period must be a positive integer.")

    required = {"High", "Low", "Close"}
    missing = required.difference(market_data.columns)
    if missing:
        raise IndicatorInputError(
            "ADX/DMI requires columns: " + ", ".join(sorted(missing))
        )

    high = pd.to_numeric(market_data["High"], errors="coerce").astype(float)
    low = pd.to_numeric(market_data["Low"], errors="coerce").astype(float)
    close = pd.to_numeric(market_data["Close"], errors="coerce").astype(float)

    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0.0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0.0)

    previous_close = close.shift(1)
    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    # Wilder smoothing is equivalent to alpha=1/period.
    atr = true_range.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()
    plus_dm_smoothed = plus_dm.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()
    minus_dm_smoothed = minus_dm.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    plus_di = 100.0 * plus_dm_smoothed / atr
    minus_di = 100.0 * minus_dm_smoothed / atr

    di_sum = plus_di + minus_di
    dx = (100.0 * (plus_di - minus_di).abs() / di_sum).where(di_sum != 0)
    adx = dx.ewm(
        alpha=1 / period,
        adjust=False,
        min_periods=period,
    ).mean()

    return pd.DataFrame(
        {
            f"ADX_{period}": adx,
            f"PLUS_DI_{period}": plus_di,
            f"MINUS_DI_{period}": minus_di,
        },
        index=market_data.index,
    )
