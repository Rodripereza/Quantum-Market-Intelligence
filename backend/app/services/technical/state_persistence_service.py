from __future__ import annotations

from datetime import datetime
from statistics import mean
from typing import Any


class TechnicalStatePersistenceService:
    """
    DE-TA-014.2 — State Persistence & Regime Duration Engine

    Interprets persistent DE-TA-014.1 snapshots.

    Produces:
    - current-state duration
    - consecutive snapshot count
    - persistence strength
    - state-score trend
    - transition-readiness trend
    - transition pressure
    - regime stability
    """

    def analyze(
        self,
        *,
        history: list[dict[str, Any]],
        transitions: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not history:
            return {
                "engine": "QMI State Persistence & Regime Duration Engine",
                "engine_id": "DE-TA-014.2",
                "version": "0.1.0",
                "status": "insufficient_history",
                "state_persistence": {
                    "available": False,
                    "reason": "No persistent snapshots available.",
                },
            }

        ordered = sorted(
            history,
            key=lambda item: int(item.get("id") or 0),
        )

        latest = ordered[-1]
        current_state = str(
            latest.get("state") or "UNKNOWN"
        ).upper()

        current_run = []
        for item in reversed(ordered):
            if str(item.get("state") or "").upper() != current_state:
                break
            current_run.append(item)

        current_run.reverse()

        first_current = current_run[0]
        latest_current = current_run[-1]

        duration = self._duration(
            first_current.get("created_at"),
            latest_current.get("created_at"),
        )

        state_scores = [
            self._number(item.get("state_score"))
            for item in current_run
            if self._number(item.get("state_score")) is not None
        ]

        readiness_scores = [
            self._number(item.get("transition_readiness_score"))
            for item in current_run
            if self._number(
                item.get("transition_readiness_score")
            ) is not None
        ]

        next_probabilities = [
            self._number(item.get("next_state_probability"))
            for item in current_run
            if self._number(
                item.get("next_state_probability")
            ) is not None
        ]

        state_score_trend = self._trend(state_scores)
        readiness_trend = self._trend(readiness_scores)
        next_probability_trend = self._trend(next_probabilities)

        persistence_strength = self._persistence_strength(
            consecutive=len(current_run),
            state_scores=state_scores,
            duration_seconds=duration["seconds"],
        )

        stability = self._stability(
            current_run=current_run,
            state_scores=state_scores,
            readiness_scores=readiness_scores,
        )

        transition_pressure = self._transition_pressure(
            latest=latest,
            readiness_scores=readiness_scores,
            next_probabilities=next_probabilities,
            readiness_trend=readiness_trend,
            next_probability_trend=next_probability_trend,
        )

        recent_transition = transitions[0] if transitions else None

        return {
            "engine": "QMI State Persistence & Regime Duration Engine",
            "engine_id": "DE-TA-014.2",
            "version": "0.1.0",
            "status": "operational",
            "state_persistence": {
                "available": True,
                "current_state": {
                    "state": current_state,
                    "consecutive_snapshots": len(current_run),
                    "first_snapshot_id": first_current.get("id"),
                    "latest_snapshot_id": latest_current.get("id"),
                    "entered_at": first_current.get("created_at"),
                    "last_observed_at": latest_current.get("created_at"),
                    "duration": duration,
                },
                "persistence_strength": persistence_strength,
                "regime_stability": stability,
                "state_score_dynamics": {
                    "latest": state_scores[-1] if state_scores else None,
                    "average": round(mean(state_scores), 1)
                    if state_scores else None,
                    "trend": state_score_trend,
                    "observations": len(state_scores),
                },
                "transition_readiness_dynamics": {
                    "latest": readiness_scores[-1]
                    if readiness_scores else None,
                    "average": round(mean(readiness_scores), 1)
                    if readiness_scores else None,
                    "trend": readiness_trend,
                    "observations": len(readiness_scores),
                },
                "next_state_pressure": transition_pressure,
                "recent_transition": recent_transition,
                "history_context": {
                    "total_snapshots": len(ordered),
                    "total_transitions": len(transitions),
                    "current_state_share_pct": round(
                        (
                            sum(
                                1
                                for item in ordered
                                if str(
                                    item.get("state") or ""
                                ).upper()
                                == current_state
                            )
                            / len(ordered)
                        )
                        * 100.0,
                        1,
                    ),
                },
                "scope": {
                    "technical_only": True,
                    "historical_interpretation": True,
                    "automatic_execution": False,
                    "note": (
                        "DE-TA-014.2 interprets persisted technical-state "
                        "history. Reliability improves as additional snapshots "
                        "accumulate over time."
                    ),
                },
            },
        }

    def _persistence_strength(
        self,
        *,
        consecutive: int,
        state_scores: list[float],
        duration_seconds: float,
    ) -> dict[str, Any]:
        count_score = min(100.0, consecutive * 15.0)

        duration_hours = duration_seconds / 3600.0
        duration_score = min(100.0, duration_hours * 8.0)

        average_state = (
            mean(state_scores)
            if state_scores
            else 0.0
        )

        score = (
            count_score * 0.45
            + duration_score * 0.20
            + average_state * 0.35
        )

        if consecutive < 3:
            maturity = "EARLY"
        elif consecutive < 6:
            maturity = "ESTABLISHED"
        else:
            maturity = "PERSISTENT"

        if score >= 80:
            state = "VERY_HIGH"
        elif score >= 65:
            state = "HIGH"
        elif score >= 45:
            state = "MODERATE"
        else:
            state = "LOW"

        return {
            "score": round(score, 1),
            "state": state,
            "maturity": maturity,
        }

    def _stability(
        self,
        *,
        current_run: list[dict[str, Any]],
        state_scores: list[float],
        readiness_scores: list[float],
    ) -> dict[str, Any]:
        if len(current_run) <= 1:
            return {
                "score": 50.0,
                "state": "INSUFFICIENT_DEPTH",
                "state_score_range": 0.0,
                "readiness_range": 0.0,
            }

        state_range = (
            max(state_scores) - min(state_scores)
            if state_scores
            else 0.0
        )

        readiness_range = (
            max(readiness_scores) - min(readiness_scores)
            if readiness_scores
            else 0.0
        )

        volatility_penalty = min(
            100.0,
            state_range * 3.0 + readiness_range * 2.0,
        )

        score = max(0.0, 100.0 - volatility_penalty)

        if score >= 85:
            state = "STABLE"
        elif score >= 65:
            state = "MODERATELY_STABLE"
        else:
            state = "UNSTABLE"

        return {
            "score": round(score, 1),
            "state": state,
            "state_score_range": round(state_range, 1),
            "readiness_range": round(readiness_range, 1),
        }

    def _transition_pressure(
        self,
        *,
        latest: dict[str, Any],
        readiness_scores: list[float],
        next_probabilities: list[float],
        readiness_trend: dict[str, Any],
        next_probability_trend: dict[str, Any],
    ) -> dict[str, Any]:
        latest_readiness = (
            readiness_scores[-1]
            if readiness_scores
            else 0.0
        )

        latest_probability = (
            next_probabilities[-1]
            if next_probabilities
            else 0.0
        )

        trend_bonus = 0.0

        if readiness_trend["direction"] == "RISING":
            trend_bonus += 8.0
        elif readiness_trend["direction"] == "FALLING":
            trend_bonus -= 6.0

        if next_probability_trend["direction"] == "RISING":
            trend_bonus += 8.0
        elif next_probability_trend["direction"] == "FALLING":
            trend_bonus -= 6.0

        score = (
            latest_readiness * 0.50
            + latest_probability * 0.40
            + trend_bonus
        )

        score = max(0.0, min(100.0, score))

        if score >= 75:
            state = "HIGH"
        elif score >= 55:
            state = "MODERATE"
        else:
            state = "LOW"

        return {
            "target_state": latest.get("next_state"),
            "score": round(score, 1),
            "state": state,
            "next_state_probability": self._number(
                latest.get("next_state_probability")
            ),
            "transition_readiness": self._number(
                latest.get("transition_readiness_score")
            ),
            "readiness_trend": readiness_trend,
            "probability_trend": next_probability_trend,
        }

    def _trend(
        self,
        values: list[float],
    ) -> dict[str, Any]:
        if len(values) < 2:
            return {
                "direction": "FLAT",
                "delta": 0.0,
                "slope_per_observation": 0.0,
            }

        delta = values[-1] - values[0]
        slope = delta / max(1, len(values) - 1)

        if delta > 2.0:
            direction = "RISING"
        elif delta < -2.0:
            direction = "FALLING"
        else:
            direction = "FLAT"

        return {
            "direction": direction,
            "delta": round(delta, 1),
            "slope_per_observation": round(slope, 2),
        }

    def _duration(
        self,
        start_value: Any,
        end_value: Any,
    ) -> dict[str, Any]:
        start = self._parse_datetime(start_value)
        end = self._parse_datetime(end_value)

        if not start or not end:
            return {
                "seconds": 0.0,
                "minutes": 0.0,
                "hours": 0.0,
                "days": 0.0,
            }

        seconds = max(0.0, (end - start).total_seconds())

        return {
            "seconds": round(seconds, 1),
            "minutes": round(seconds / 60.0, 1),
            "hours": round(seconds / 3600.0, 2),
            "days": round(seconds / 86400.0, 3),
        }

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not value:
            return None

        try:
            return datetime.fromisoformat(str(value))
        except ValueError:
            return None

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None
