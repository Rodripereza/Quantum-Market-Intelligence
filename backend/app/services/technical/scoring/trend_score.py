"""
QMI Trend Score Engine.

This module converts raw trend measurements into a normalized directional
score between -100 and +100. It implements the first mathematical layer of
the QMI Decision Engine without coupling the scoring logic to FastAPI.
"""

from __future__ import annotations

import math

import pandas as pd

from app.indicators import calculate_ema, calculate_sma
from app.indicators.volatility import calculate_atr
from app.services.technical.scoring.models import (
    TrendComponent,
    TrendScoreResult,
)
from app.services.technical.scoring.normalization import (
    clamp_score,
    linear_score,
)


class TrendScoringError(ValueError):
    """Raised when QMI Trend Score cannot be calculated."""


class TrendScoreEngine:
    """Calculate the normalized QMI Trend Score."""

    WEIGHTS = {
        "price_vs_sma200": 0.25,
        "sma50_vs_sma200": 0.25,
        "sma200_slope": 0.20,
        "price_vs_ema20": 0.15,
        "market_structure": 0.15,
    }

    MIN_OBSERVATIONS = 220

    def calculate(self, market_data: pd.DataFrame) -> TrendScoreResult:
        """Calculate a complete directional trend score."""

        self._validate_market_data(market_data)

        close = pd.to_numeric(market_data["Close"], errors="coerce")
        sma_50 = calculate_sma(market_data, period=50)
        sma_200 = calculate_sma(market_data, period=200)
        ema_20 = calculate_ema(market_data, period=20)
        atr_14 = calculate_atr(market_data, period=14)

        latest_close = self._latest(close)
        latest_sma_50 = self._latest(sma_50)
        latest_sma_200 = self._latest(sma_200)
        latest_ema_20 = self._latest(ema_20)
        latest_atr = self._latest(atr_14)

        required = {
            "close": latest_close,
            "sma_50": latest_sma_50,
            "sma_200": latest_sma_200,
            "ema_20": latest_ema_20,
            "atr_14": latest_atr,
        }

        missing = [name for name, value in required.items() if value is None]
        if missing:
            raise TrendScoringError(
                "Insufficient data for Trend Score. Missing: "
                + ", ".join(missing)
            )

        if latest_atr <= 0:
            raise TrendScoringError("ATR must be greater than zero.")

        components: dict[str, TrendComponent] = {}

        # 1) Price vs SMA200, normalized by ATR.
        distance_sma200_atr = (latest_close - latest_sma_200) / latest_atr
        score_price_sma200 = linear_score(
            distance_sma200_atr,
            [
                (-4.0, -100.0),
                (-3.0, -80.0),
                (-2.0, -60.0),
                (-1.0, -40.0),
                (-0.25, -10.0),
                (0.0, 0.0),
                (0.25, 10.0),
                (1.0, 40.0),
                (2.0, 60.0),
                (3.0, 80.0),
                (4.0, 100.0),
            ],
        )
        components["price_vs_sma200"] = TrendComponent(
            name="price_vs_sma200",
            score=score_price_sma200,
            weight=self.WEIGHTS["price_vs_sma200"],
            value=round(distance_sma200_atr, 4),
            state=self._direction(score_price_sma200),
        )

        # 2) SMA50 vs SMA200 with spread-momentum modifier.
        spread_pct = ((latest_sma_50 - latest_sma_200) / latest_sma_200) * 100
        base_spread_score = linear_score(
            spread_pct,
            [
                (-10.0, -90.0),
                (-6.0, -75.0),
                (-3.0, -55.0),
                (0.0, 0.0),
                (3.0, 55.0),
                (6.0, 75.0),
                (10.0, 90.0),
            ],
        )

        spread_10 = self._spread_pct_at_offset(sma_50, sma_200, 10)
        spread_change = None if spread_10 is None else spread_pct - spread_10
        modifier = self._spread_momentum_modifier(
            current_spread=spread_pct,
            spread_change=spread_change,
        )
        score_ma_structure = clamp_score(base_spread_score + modifier)

        components["sma50_vs_sma200"] = TrendComponent(
            name="sma50_vs_sma200",
            score=score_ma_structure,
            weight=self.WEIGHTS["sma50_vs_sma200"],
            value=round(spread_pct, 4),
            state=self._direction(score_ma_structure),
        )

        # 3) 20-session slope of SMA200.
        sma200_20 = self._value_at_offset(sma_200, 20)
        if sma200_20 is None or sma200_20 == 0:
            slope_pct = 0.0
            slope_score = 0.0
        else:
            slope_pct = ((latest_sma_200 - sma200_20) / sma200_20) * 100
            slope_score = linear_score(
                slope_pct,
                [
                    (-5.0, -100.0),
                    (-3.0, -80.0),
                    (-1.5, -60.0),
                    (-0.5, -35.0),
                    (0.0, 0.0),
                    (0.5, 35.0),
                    (1.5, 60.0),
                    (3.0, 80.0),
                    (5.0, 100.0),
                ],
            )

        components["sma200_slope"] = TrendComponent(
            name="sma200_slope",
            score=slope_score,
            weight=self.WEIGHTS["sma200_slope"],
            value=round(slope_pct, 4),
            state=self._direction(slope_score),
        )

        # 4) Price vs EMA20, normalized by ATR. The score is capped at
        # +/-80 because extreme short-term extension is not automatically
        # equivalent to higher trend quality.
        distance_ema20_atr = (latest_close - latest_ema_20) / latest_atr
        score_price_ema20 = linear_score(
            distance_ema20_atr,
            [
                (-3.0, -80.0),
                (-2.0, -70.0),
                (-1.0, -50.0),
                (-0.25, -15.0),
                (0.0, 0.0),
                (0.25, 15.0),
                (1.0, 50.0),
                (2.0, 70.0),
                (3.0, 80.0),
            ],
        )

        components["price_vs_ema20"] = TrendComponent(
            name="price_vs_ema20",
            score=score_price_ema20,
            weight=self.WEIGHTS["price_vs_ema20"],
            value=round(distance_ema20_atr, 4),
            state=self._direction(score_price_ema20),
        )

        # 5) Market structure. Version 1 detects directional consistency
        # from recent rolling swing highs/lows. A dedicated Structure Engine
        # will replace/extend this component later without changing the
        # Trend Score public contract.
        structure_score, structure_state = self._market_structure_score(
            market_data
        )
        components["market_structure"] = TrendComponent(
            name="market_structure",
            score=structure_score,
            weight=self.WEIGHTS["market_structure"],
            value=None,
            state=structure_state,
        )

        total_score = clamp_score(
            sum(component.contribution for component in components.values())
        )

        return TrendScoreResult(
            score=total_score,
            direction=self._classify_direction(total_score),
            data_quality=self._data_quality(market_data, components),
            components=components,
            observations_available=len(market_data),
        )

    @staticmethod
    def _validate_market_data(market_data: pd.DataFrame) -> None:
        if not isinstance(market_data, pd.DataFrame):
            raise TrendScoringError("market_data must be a pandas DataFrame.")

        required = {"High", "Low", "Close"}
        missing = required.difference(market_data.columns)
        if missing:
            raise TrendScoringError(
                "Trend Score requires columns: " + ", ".join(sorted(missing))
            )

        if len(market_data) < TrendScoreEngine.MIN_OBSERVATIONS:
            raise TrendScoringError(
                "Trend Score requires at least "
                f"{TrendScoreEngine.MIN_OBSERVATIONS} observations; "
                f"received {len(market_data)}."
            )

    @staticmethod
    def _latest(series: pd.Series) -> float | None:
        valid = pd.to_numeric(series, errors="coerce").dropna()
        if valid.empty:
            return None
        return float(valid.iloc[-1])

    @staticmethod
    def _value_at_offset(series: pd.Series, offset: int) -> float | None:
        valid = pd.to_numeric(series, errors="coerce").dropna()
        if len(valid) <= offset:
            return None
        return float(valid.iloc[-1 - offset])

    def _spread_pct_at_offset(
        self,
        sma_50: pd.Series,
        sma_200: pd.Series,
        offset: int,
    ) -> float | None:
        value_50 = self._value_at_offset(sma_50, offset)
        value_200 = self._value_at_offset(sma_200, offset)

        if value_50 is None or value_200 in (None, 0):
            return None

        return ((value_50 - value_200) / value_200) * 100

    @staticmethod
    def _spread_momentum_modifier(
        current_spread: float,
        spread_change: float | None,
    ) -> float:
        if spread_change is None or math.isclose(spread_change, 0.0, abs_tol=0.05):
            return 0.0

        # Positive return value means the existing directional structure is
        # strengthening; negative means it is converging/deteriorating.
        directional_change = spread_change if current_spread >= 0 else -spread_change
        magnitude = abs(directional_change)

        if magnitude >= 2.0:
            modifier = 10.0
        elif magnitude >= 0.75:
            modifier = 5.0
        else:
            modifier = 2.5

        return modifier if directional_change > 0 else -modifier

    @staticmethod
    def _market_structure_score(
        market_data: pd.DataFrame,
        pivot_window: int = 5,
        lookback: int = 120,
    ) -> tuple[float, str]:
        data = market_data.tail(lookback).copy()
        high = pd.to_numeric(data["High"], errors="coerce")
        low = pd.to_numeric(data["Low"], errors="coerce")

        rolling_high = high.rolling(
            window=(pivot_window * 2) + 1,
            center=True,
        ).max()
        rolling_low = low.rolling(
            window=(pivot_window * 2) + 1,
            center=True,
        ).min()

        swing_highs = high[high.eq(rolling_high)].dropna().tail(3)
        swing_lows = low[low.eq(rolling_low)].dropna().tail(3)

        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return 0.0, "insufficient_structure"

        high_changes = swing_highs.diff().dropna()
        low_changes = swing_lows.diff().dropna()

        higher_high_ratio = float((high_changes > 0).mean())
        lower_high_ratio = float((high_changes < 0).mean())
        higher_low_ratio = float((low_changes > 0).mean())
        lower_low_ratio = float((low_changes < 0).mean())

        bullish = (higher_high_ratio + higher_low_ratio) / 2
        bearish = (lower_high_ratio + lower_low_ratio) / 2
        raw = (bullish - bearish) * 100

        if bullish >= 0.75:
            return clamp_score(max(raw, 75.0)), "HH_HL"
        if bearish >= 0.75:
            return clamp_score(min(raw, -75.0)), "LH_LL"
        if bullish > bearish:
            return clamp_score(raw * 0.6), "bullish_mixed"
        if bearish > bullish:
            return clamp_score(raw * 0.6), "bearish_mixed"
        return 0.0, "range_mixed"

    @staticmethod
    def _direction(score: float) -> str:
        if score > 10:
            return "bullish"
        if score < -10:
            return "bearish"
        return "neutral"

    @staticmethod
    def _classify_direction(score: float) -> str:
        if score >= 60:
            return "STRONG_BULL"
        if score >= 25:
            return "BULL"
        if score <= -60:
            return "STRONG_BEAR"
        if score <= -25:
            return "BEAR"
        return "NEUTRAL"

    @classmethod
    def _data_quality(
        cls,
        market_data: pd.DataFrame,
        components: dict[str, TrendComponent],
    ) -> float:
        required_columns = ["High", "Low", "Close"]
        valid_ratio = (
            market_data[required_columns]
            .apply(pd.to_numeric, errors="coerce")
            .notna()
            .all(axis=1)
            .mean()
        )

        structure = components.get("market_structure")
        structure_factor = (
            0.85
            if structure is not None
            and structure.state == "insufficient_structure"
            else 1.0
        )

        observation_factor = min(len(market_data) / cls.MIN_OBSERVATIONS, 1.0)
        quality = 100 * valid_ratio * structure_factor * observation_factor
        return max(0.0, min(100.0, float(quality)))


trend_score_engine = TrendScoreEngine()
