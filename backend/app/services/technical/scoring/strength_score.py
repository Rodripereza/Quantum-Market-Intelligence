"""QMI Trend Strength Score Engine."""

from __future__ import annotations

import pandas as pd

from app.indicators import calculate_ema, calculate_sma
from app.indicators.strength import calculate_adx_dmi
from app.services.technical.scoring.models import (
    StrengthComponent,
    StrengthScoreResult,
)
from app.services.technical.scoring.normalization import linear_score


class StrengthScoringError(ValueError):
    """Raised when QMI Trend Strength cannot be calculated."""


class StrengthScoreEngine:
    """Measure trend strength independently from trend direction."""

    WEIGHTS = {
        "adx": 0.50,
        "di_separation": 0.20,
        "slope_consistency": 0.15,
        "structure_persistence": 0.15,
    }
    MIN_OBSERVATIONS = 220

    def calculate(
        self,
        market_data: pd.DataFrame,
        trend_score: float,
    ) -> StrengthScoreResult:
        self._validate(market_data)

        dmi = calculate_adx_dmi(market_data, period=14)
        adx = self._latest(dmi["ADX_14"])
        plus_di = self._latest(dmi["PLUS_DI_14"])
        minus_di = self._latest(dmi["MINUS_DI_14"])
        if adx is None or plus_di is None or minus_di is None:
            raise StrengthScoringError("Insufficient data for ADX/DMI.")

        adx_score = linear_score(
            adx,
            [
                (12, 0), (15, 10), (20, 25), (25, 45),
                (35, 65), (50, 85), (60, 100),
            ],
        )
        adx_score = max(0.0, min(100.0, adx_score))

        di_gap = abs(plus_di - minus_di)
        di_base = linear_score(
            di_gap,
            [(0, 0), (3, 20), (5, 40), (10, 60), (15, 80), (25, 100)],
        )
        di_base = max(0.0, min(100.0, di_base))

        dmi_direction = (
            "BULLISH" if plus_di > minus_di
            else "BEARISH" if minus_di > plus_di
            else "NEUTRAL"
        )
        trend_direction = (
            "BULLISH" if trend_score > 0
            else "BEARISH" if trend_score < 0
            else "NEUTRAL"
        )

        # A contradictory DMI does not erase ADX strength, but it removes
        # the directional-confirmation contribution and raises a conflict.
        if trend_direction == "NEUTRAL" or dmi_direction == "NEUTRAL":
            confirmation = 0.5
        elif trend_direction == dmi_direction:
            confirmation = 1.0
        else:
            confirmation = 0.0

        di_score = di_base * confirmation
        regime_conflict = (
            adx > 25
            and trend_direction != "NEUTRAL"
            and dmi_direction != "NEUTRAL"
            and trend_direction != dmi_direction
        )

        slope_score, slope_state = self._slope_consistency(
            market_data, trend_direction
        )
        persistence_score, persistence_state = self._structure_persistence(
            market_data, trend_direction
        )

        components = {
            "adx": StrengthComponent(
                name="adx",
                score=adx_score,
                weight=self.WEIGHTS["adx"],
                value=round(adx, 4),
                state=self._adx_state(adx),
            ),
            "di_separation": StrengthComponent(
                name="di_separation",
                score=di_score,
                weight=self.WEIGHTS["di_separation"],
                value=round(di_gap, 4),
                state=f"{dmi_direction}_{'CONFIRMED' if confirmation == 1 else 'CONFLICT' if confirmation == 0 else 'NEUTRAL'}",
            ),
            "slope_consistency": StrengthComponent(
                name="slope_consistency",
                score=slope_score,
                weight=self.WEIGHTS["slope_consistency"],
                value=None,
                state=slope_state,
            ),
            "structure_persistence": StrengthComponent(
                name="structure_persistence",
                score=persistence_score,
                weight=self.WEIGHTS["structure_persistence"],
                value=None,
                state=persistence_state,
            ),
        }

        total = sum(c.contribution for c in components.values())
        total = max(0.0, min(100.0, total))

        return StrengthScoreResult(
            score=total,
            strength=self._classify_strength(total),
            dmi_direction=dmi_direction,
            regime_conflict=regime_conflict,
            data_quality=self._data_quality(market_data, components),
            components=components,
            observations_available=len(market_data),
        )

    @staticmethod
    def _validate(market_data: pd.DataFrame) -> None:
        if not isinstance(market_data, pd.DataFrame):
            raise StrengthScoringError("market_data must be a pandas DataFrame.")
        required = {"High", "Low", "Close"}
        missing = required.difference(market_data.columns)
        if missing:
            raise StrengthScoringError(
                "Strength Score requires columns: " + ", ".join(sorted(missing))
            )
        if len(market_data) < StrengthScoreEngine.MIN_OBSERVATIONS:
            raise StrengthScoringError(
                f"Strength Score requires at least {StrengthScoreEngine.MIN_OBSERVATIONS} observations; "
                f"received {len(market_data)}."
            )

    @staticmethod
    def _latest(series: pd.Series) -> float | None:
        valid = pd.to_numeric(series, errors="coerce").dropna()
        return None if valid.empty else float(valid.iloc[-1])

    @staticmethod
    def _slope_consistency(
        market_data: pd.DataFrame,
        trend_direction: str,
    ) -> tuple[float, str]:
        ema20 = calculate_ema(market_data, period=20)
        sma50 = calculate_sma(market_data, period=50)
        sma200 = calculate_sma(market_data, period=200)

        series_list = [ema20, sma50, sma200]
        aligned = 0
        available = 0
        for series in series_list:
            valid = pd.to_numeric(series, errors="coerce").dropna()
            if len(valid) <= 20:
                continue
            available += 1
            delta = float(valid.iloc[-1] - valid.iloc[-21])
            if trend_direction == "BULLISH" and delta > 0:
                aligned += 1
            elif trend_direction == "BEARISH" and delta < 0:
                aligned += 1

        if available == 0 or trend_direction == "NEUTRAL":
            return 0.0, "NO_DIRECTION"
        mapping = {0: 0.0, 1: 35.0, 2: 70.0, 3: 100.0}
        score = mapping.get(aligned, (aligned / available) * 100.0)
        return score, f"{aligned}_OF_{available}_ALIGNED"

    @staticmethod
    def _structure_persistence(
        market_data: pd.DataFrame,
        trend_direction: str,
    ) -> tuple[float, str]:
        high = pd.to_numeric(market_data["High"], errors="coerce")
        low = pd.to_numeric(market_data["Low"], errors="coerce")

        # Five non-overlapping 5-session swing blocks give a stable,
        # deterministic first implementation without look-ahead pivots.
        window = 5
        blocks = 6  # six extrema produce five transitions
        if len(market_data) < window * blocks or trend_direction == "NEUTRAL":
            return 0.0, "INSUFFICIENT_STRUCTURE"

        recent_highs = []
        recent_lows = []
        for i in range(blocks, 0, -1):
            start = len(market_data) - i * window
            end = start + window
            recent_highs.append(float(high.iloc[start:end].max()))
            recent_lows.append(float(low.iloc[start:end].min()))

        coherent = 0
        total = blocks - 1
        for i in range(1, blocks):
            if trend_direction == "BULLISH":
                if recent_highs[i] > recent_highs[i - 1] and recent_lows[i] > recent_lows[i - 1]:
                    coherent += 1
            elif trend_direction == "BEARISH":
                if recent_highs[i] < recent_highs[i - 1] and recent_lows[i] < recent_lows[i - 1]:
                    coherent += 1

        score = (coherent / total) * 100.0
        return score, f"{coherent}_OF_{total}_SWINGS_COHERENT"

    @staticmethod
    def _adx_state(adx: float) -> str:
        if adx < 15:
            return "VERY_WEAK"
        if adx < 20:
            return "WEAK"
        if adx < 25:
            return "TRANSITION"
        if adx < 35:
            return "TRENDING"
        if adx < 50:
            return "STRONG"
        return "VERY_STRONG"

    @staticmethod
    def _classify_strength(score: float) -> str:
        if score < 20:
            return "NO_TREND"
        if score < 35:
            return "WEAK"
        if score < 55:
            return "MODERATE"
        if score < 75:
            return "STRONG"
        return "VERY_STRONG"

    @staticmethod
    def _data_quality(
        market_data: pd.DataFrame,
        components: dict[str, StrengthComponent],
    ) -> float:
        required = market_data[["High", "Low", "Close"]].apply(
            pd.to_numeric, errors="coerce"
        )
        completeness = 100.0 * (1.0 - required.isna().mean().mean())
        component_quality = 100.0 * sum(
            1 for c in components.values() if c.state is not None
        ) / max(1, len(components))
        return max(0.0, min(100.0, 0.7 * completeness + 0.3 * component_quality))


strength_score_engine = StrengthScoreEngine()
