"""QMI Market Regime Engine.

This layer combines the directional Trend Score with the non-directional
Trend Strength Score. Volatility and Market Phase are deliberately excluded
from this version and will be integrated in later Decision Engine stages.
"""

from __future__ import annotations

from app.services.technical.scoring.models import (
    RegimeResult,
    StrengthScoreResult,
    TrendScoreResult,
)


class RegimeScoringError(ValueError):
    """Raised when a market regime cannot be classified."""


class MarketRegimeEngine:
    """Classify the primary market regime from Trend + Strength."""

    CONFLICT_CONFIDENCE_PENALTY = 20.0

    def calculate(
        self,
        trend: TrendScoreResult,
        strength: StrengthScoreResult,
    ) -> RegimeResult:
        if trend is None or strength is None:
            raise RegimeScoringError(
                "Trend and Strength results are required."
            )

        trend_score = float(trend.score)
        strength_score = float(strength.score)

        direction = self._direction(trend_score)
        primary_regime = self._classify_regime(
            trend_score=trend_score,
            strength_score=strength_score,
            conflict=strength.regime_conflict,
        )

        trend_agreement = self._trend_agreement(trend)
        strength_quality = self._strength_quality(strength)
        structure_quality = self._structure_quality(
            trend=trend,
            strength=strength,
        )
        temporal_stability = self._temporal_stability(
            trend=trend,
            strength=strength,
        )

        confidence = (
            0.35 * trend_agreement
            + 0.30 * strength_quality
            + 0.20 * structure_quality
            + 0.15 * temporal_stability
        )

        if strength.regime_conflict:
            confidence -= self.CONFLICT_CONFIDENCE_PENALTY

        confidence = max(0.0, min(100.0, confidence))

        return RegimeResult(
            primary_regime=primary_regime,
            direction=direction,
            trend_score=trend_score,
            strength_score=strength_score,
            strength=strength.strength,
            dmi_direction=strength.dmi_direction,
            regime_conflict=bool(strength.regime_conflict),
            confidence=confidence,
            trend_agreement=trend_agreement,
            strength_quality=strength_quality,
            structure_quality=structure_quality,
            temporal_stability=temporal_stability,
            transition_state=self._transition_state(
                trend_score=trend_score,
                strength_score=strength_score,
                conflict=strength.regime_conflict,
                dmi_direction=strength.dmi_direction,
            ),
            # Reserved for the later temporal-state layer. We do not invent
            # an age from a single snapshot.
            regime_age=None,
        )

    @staticmethod
    def _direction(trend_score: float) -> str:
        if trend_score >= 25:
            return "BULLISH"
        if trend_score <= -25:
            return "BEARISH"
        return "NEUTRAL"

    @staticmethod
    def _classify_regime(
        trend_score: float,
        strength_score: float,
        conflict: bool,
    ) -> str:
        # A strong directional disagreement with DMI gets a dedicated
        # regime label rather than silently forcing a bull/bear label.
        if conflict and strength_score >= 35:
            return "REGIME_CONFLICT"

        if trend_score >= 60 and strength_score >= 60:
            return "STRONG_BULL"
        if trend_score >= 25 and strength_score >= 35:
            return "BULL"
        if trend_score >= 25 and strength_score < 35:
            return "WEAK_BULL"

        if -25 < trend_score < 25:
            if strength_score < 40:
                return "RANGE"
            return "TRANSITION"

        if trend_score <= -60 and strength_score >= 60:
            return "STRONG_BEAR"
        if trend_score <= -25 and strength_score >= 35:
            return "BEAR"
        if trend_score <= -25 and strength_score < 35:
            return "WEAK_BEAR"

        return "TRANSITION"

    @staticmethod
    def _trend_agreement(trend: TrendScoreResult) -> float:
        """
        Measure agreement between the directional Trend Score components.

        Full-directional components receive 1.0, neutral components 0.5,
        contradictory components 0.0.
        """
        if not trend.components:
            return 0.0

        sign = 1 if trend.score > 0 else -1 if trend.score < 0 else 0
        if sign == 0:
            neutral_count = sum(
                1 for component in trend.components.values()
                if abs(float(component.score)) < 10
            )
            return 100.0 * neutral_count / len(trend.components)

        agreement = 0.0
        total_weight = 0.0
        for component in trend.components.values():
            weight = float(component.weight)
            score = float(component.score)
            total_weight += weight

            if abs(score) < 10:
                agreement += 0.5 * weight
            elif (score > 0 and sign > 0) or (score < 0 and sign < 0):
                agreement += 1.0 * weight

        if total_weight <= 0:
            return 0.0
        return 100.0 * agreement / total_weight

    @staticmethod
    def _strength_quality(strength: StrengthScoreResult) -> float:
        """
        Strength quality is not simply the raw Strength Score.

        It blends raw strength with data quality so a strong result based on
        incomplete data cannot receive full confidence.
        """
        raw = max(0.0, min(100.0, float(strength.score)))
        quality = max(0.0, min(100.0, float(strength.data_quality)))
        return 0.8 * raw + 0.2 * quality

    @staticmethod
    def _structure_quality(
        trend: TrendScoreResult,
        strength: StrengthScoreResult,
    ) -> float:
        trend_structure = trend.components.get("market_structure")
        persistence = strength.components.get("structure_persistence")

        values: list[float] = []
        if trend_structure is not None:
            values.append(abs(float(trend_structure.score)))
        if persistence is not None:
            values.append(float(persistence.score))

        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def _temporal_stability(
        trend: TrendScoreResult,
        strength: StrengthScoreResult,
    ) -> float:
        """
        First snapshot-based proxy for temporal stability.

        The true multi-session regime-age/hysteresis layer will be added
        later. For now we use signals already derived from temporal data:
        MA slope consistency, structure persistence and SMA200 slope.
        """
        values: list[float] = []

        slope_consistency = strength.components.get("slope_consistency")
        persistence = strength.components.get("structure_persistence")
        sma200_slope = trend.components.get("sma200_slope")

        if slope_consistency is not None:
            values.append(float(slope_consistency.score))
        if persistence is not None:
            values.append(float(persistence.score))
        if sma200_slope is not None:
            values.append(abs(float(sma200_slope.score)))

        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def _transition_state(
        trend_score: float,
        strength_score: float,
        conflict: bool,
        dmi_direction: str,
    ) -> str:
        if conflict:
            return "DIRECTIONAL_CONFLICT"

        if 20 <= trend_score < 35:
            return "BULL_TRANSITION"
        if -35 < trend_score <= -20:
            return "BEAR_TRANSITION"

        if abs(trend_score) < 25 and strength_score >= 40:
            return "HIGH_STRENGTH_TRANSITION"

        if trend_score >= 25 and strength_score < 35:
            return "WEAK_BULL_CONFIRMATION"
        if trend_score <= -25 and strength_score < 35:
            return "WEAK_BEAR_CONFIRMATION"

        if dmi_direction == "NEUTRAL":
            return "DMI_NEUTRAL"

        return "NONE"


market_regime_engine = MarketRegimeEngine()
