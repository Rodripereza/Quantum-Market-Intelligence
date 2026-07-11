"""
Technical analysis service for Quantum Market Intelligence.

This service coordinates the technical indicator engine and transforms
historical market data into a structured technical-analysis response.
"""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.indicators import (
    calculate_ema,
    calculate_macd,
    calculate_rsi,
    calculate_sma,
)
from app.indicators.trend import IndicatorInputError


class TechnicalAnalysisError(ValueError):
    """Raised when technical analysis cannot be completed."""


class TechnicalService:
    """
    Coordinate the QMI technical indicator engine.

    The service receives normalized OHLCV market data and calculates
    the configured trend and momentum indicators.
    """

    DEFAULT_SMA_PERIODS = (20, 50, 200)
    DEFAULT_EMA_PERIODS = (20, 50, 200)

    def analyze(
        self,
        market_data: pd.DataFrame,
        symbol: str,
        sma_periods: tuple[int, ...] = DEFAULT_SMA_PERIODS,
        ema_periods: tuple[int, ...] = DEFAULT_EMA_PERIODS,
        rsi_period: int = 14,
        macd_fast_period: int = 12,
        macd_slow_period: int = 26,
        macd_signal_period: int = 9,
        price_column: str = "Close",
    ) -> dict[str, Any]:
        """
        Calculate a complete technical-analysis snapshot.

        Parameters
        ----------
        market_data:
            Historical market data containing at least a closing-price
            column.
        symbol:
            Financial instrument symbol.
        sma_periods:
            Periods used for Simple Moving Averages.
        ema_periods:
            Periods used for Exponential Moving Averages.
        rsi_period:
            Period used for RSI.
        macd_fast_period:
            Fast EMA period used by MACD.
        macd_slow_period:
            Slow EMA period used by MACD.
        macd_signal_period:
            Signal-line EMA period used by MACD.
        price_column:
            Price column used by the indicators.

        Returns
        -------
        dict
            Structured technical-analysis result.
        """

        normalized_symbol = self._validate_symbol(symbol)
        self._validate_market_data(market_data, price_column)

        try:
            sma_values = {
                f"sma_{period}": calculate_sma(
                    market_data=market_data,
                    period=period,
                    price_column=price_column,
                )
                for period in sma_periods
            }

            ema_values = {
                f"ema_{period}": calculate_ema(
                    market_data=market_data,
                    period=period,
                    price_column=price_column,
                )
                for period in ema_periods
            }

            rsi = calculate_rsi(
                market_data=market_data,
                period=rsi_period,
                price_column=price_column,
            )

            macd = calculate_macd(
                market_data=market_data,
                fast_period=macd_fast_period,
                slow_period=macd_slow_period,
                signal_period=macd_signal_period,
                price_column=price_column,
            )

        except (IndicatorInputError, ValueError) as exc:
            raise TechnicalAnalysisError(
                f"Technical analysis failed for {normalized_symbol}: {exc}"
            ) from exc

        last_price = self._latest_value(market_data[price_column])

        trend = {
            **{
                name: self._latest_value(series)
                for name, series in sma_values.items()
            },
            **{
                name: self._latest_value(series)
                for name, series in ema_values.items()
            },
        }

        macd_line_column = (
            f"MACD_{macd_fast_period}_{macd_slow_period}"
        )
        macd_signal_column = f"MACD_SIGNAL_{macd_signal_period}"

        momentum = {
            f"rsi_{rsi_period}": self._latest_value(rsi),
            "macd": {
                "line": self._latest_value(
                    macd[macd_line_column]
                ),
                "signal": self._latest_value(
                    macd[macd_signal_column]
                ),
                "histogram": self._latest_value(
                    macd["MACD_HISTOGRAM"]
                ),
            },
        }

        return {
            "symbol": normalized_symbol,
            "last_price": last_price,
            "observations": len(market_data),
            "trend": trend,
            "momentum": momentum,
            "signals": self._build_signals(
                last_price=last_price,
                trend=trend,
                momentum=momentum,
                rsi_period=rsi_period,
            ),
        }

    @staticmethod
    def _validate_symbol(symbol: str) -> str:
        """Validate and normalize a financial instrument symbol."""

        if not isinstance(symbol, str):
            raise TechnicalAnalysisError(
                "symbol must be a string."
            )

        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise TechnicalAnalysisError(
                "symbol cannot be empty."
            )

        return normalized_symbol

    @staticmethod
    def _validate_market_data(
        market_data: pd.DataFrame,
        price_column: str,
    ) -> None:
        """Validate the basic market-data structure."""

        if not isinstance(market_data, pd.DataFrame):
            raise TechnicalAnalysisError(
                "market_data must be a pandas DataFrame."
            )

        if market_data.empty:
            raise TechnicalAnalysisError(
                "market_data cannot be empty."
            )

        if price_column not in market_data.columns:
            raise TechnicalAnalysisError(
                f"Column '{price_column}' was not found."
            )

    @staticmethod
    def _latest_value(series: pd.Series) -> float | None:
        """
        Return the latest valid numeric value from a pandas Series.

        None is returned when the series does not yet contain enough
        valid observations for the requested indicator.
        """

        numeric_series = pd.to_numeric(
            series,
            errors="coerce",
        ).dropna()

        if numeric_series.empty:
            return None

        return round(float(numeric_series.iloc[-1]), 6)

    @staticmethod
    def _build_signals(
        last_price: float | None,
        trend: dict[str, float | None],
        momentum: dict[str, Any],
        rsi_period: int,
    ) -> dict[str, str]:
        """Generate basic descriptive technical signals."""

        trend_signal = "insufficient_data"
        momentum_signal = "insufficient_data"
        macd_signal = "insufficient_data"

        sma_20 = trend.get("sma_20")
        sma_50 = trend.get("sma_50")
        sma_200 = trend.get("sma_200")

        if (
            last_price is not None
            and sma_20 is not None
            and sma_50 is not None
        ):
            if last_price > sma_20 > sma_50:
                trend_signal = "bullish"
            elif last_price < sma_20 < sma_50:
                trend_signal = "bearish"
            else:
                trend_signal = "neutral"

            if sma_200 is not None:
                if last_price > sma_200 and trend_signal == "bullish":
                    trend_signal = "strong_bullish"
                elif last_price < sma_200 and trend_signal == "bearish":
                    trend_signal = "strong_bearish"

        rsi_value = momentum.get(f"rsi_{rsi_period}")

        if rsi_value is not None:
            if rsi_value >= 70:
                momentum_signal = "overbought"
            elif rsi_value <= 30:
                momentum_signal = "oversold"
            else:
                momentum_signal = "neutral"

        macd_values = momentum.get("macd", {})
        macd_line = macd_values.get("line")
        signal_line = macd_values.get("signal")
        histogram = macd_values.get("histogram")

        if (
            macd_line is not None
            and signal_line is not None
            and histogram is not None
        ):
            if macd_line > signal_line and histogram > 0:
                macd_signal = "bullish"
            elif macd_line < signal_line and histogram < 0:
                macd_signal = "bearish"
            else:
                macd_signal = "neutral"

        return {
            "trend": trend_signal,
            "momentum": momentum_signal,
            "macd": macd_signal,
        }


technical_service = TechnicalService()