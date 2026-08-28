from __future__ import annotations

from typing import Any


class TechnicalRegimeMaturityService:
    """
    DE-TA-014.3 — Regime Maturity & Transition Probability Engine

    Consumes DE-TA-014.2 persistence output and converts it into:
    - regime maturity phase
    - regime age interpretation
    - persistence assessment
    - transition pressure
    - explicit transition probability
    - next-state confidence
    """

    MATURITY_ORDER = [
        "EARLY",
        "DEVELOPING",
        "MATURE",
        "EXHAUSTING",
        "TRANSITION",
    ]

    def analyze(
        self,
        *,
        persistence_response: dict[str, Any],
        transition_response: dict[str, Any],
    ) -> dict[str, Any]:
        persistence = (
            persistence_response.get("state_persistence") or {}
        )
        transition = (
            transition_response.get("technical_state_transition") or {}
        )

        if not persistence.get("available", False):
            return {
                "engine": "QMI Regime Maturity & Transition Probability Engine",
                "engine_id": "DE-TA-014.3",
                "version": "0.1.0",
                "status": "insufficient_history",
                "regime_maturity": {
                    "available": False,
                    "reason": persistence.get(
                        "reason",
                        "Insufficient persistence history.",
                    ),
                },
            }

        current_state = persistence.get("current_state") or {}
        persistence_strength = (
            persistence.get("persistence_strength") or {}
        )
        stability = persistence.get("regime_stability") or {}
        readiness = (
            persistence.get("transition_readiness_dynamics") or {}
        )
        pressure = persistence.get("next_state_pressure") or {}
        history_context = persistence.get("history_context") or {}

        current_transition = transition.get("current_state") or {}
        next_candidate = transition.get("next_state_candidate") or {}
        transition_readiness = (
            transition.get("transition_readiness") or {}
        )

        consecutive = int(
            current_state.get("consecutive_snapshots") or 0
        )
        duration = current_state.get("duration") or {}
        duration_hours = self._number(
            duration.get("hours"), 0.0
        )

        persistence_score = self._number(
            persistence_strength.get("score"), 0.0
        )
        stability_score = self._number(
            stability.get("score"), 0.0
        )
        readiness_score = self._number(
            readiness.get("latest"), 0.0
        )
        pressure_score = self._number(
            pressure.get("score"), 0.0
        )
        next_probability = self._number(
            pressure.get("next_state_probability"),
            next_candidate.get("probability"),
        )

        readiness_trend = (
            readiness.get("trend") or {}
        )
        probability_trend = (
            pressure.get("probability_trend") or {}
        )

        maturity = self._maturity_phase(
            consecutive=consecutive,
            duration_hours=duration_hours,
            persistence_score=persistence_score,
            stability_score=stability_score,
            pressure_score=pressure_score,
            readiness_score=readiness_score,
            readiness_trend=readiness_trend,
            probability_trend=probability_trend,
        )

        transition_probability = self._transition_probability(
            next_probability=next_probability,
            pressure_score=pressure_score,
            readiness_score=readiness_score,
            readiness_trend=readiness_trend,
            probability_trend=probability_trend,
            stability_score=stability_score,
            maturity=maturity,
        )

        maturity_score = self._maturity_score(
            consecutive=consecutive,
            duration_hours=duration_hours,
            persistence_score=persistence_score,
            stability_score=stability_score,
            pressure_score=pressure_score,
        )

        next_state_confidence = self._next_state_confidence(
            transition_probability=transition_probability,
            pressure_score=pressure_score,
            transition_readiness_score=self._number(
                transition_readiness.get("score"),
                readiness_score,
            ),
        )

        interpretation = self._interpretation(
            current_state=str(
                current_state.get("state") or "UNKNOWN"
            ),
            maturity=maturity,
            transition_probability=transition_probability,
            target_state=str(
                pressure.get("target_state")
                or next_candidate.get("state")
                or "UNKNOWN"
            ),
        )

        return {
            "engine": "QMI Regime Maturity & Transition Probability Engine",
            "engine_id": "DE-TA-014.3",
            "version": "0.1.0",
            "status": "operational",
            "regime_maturity": {
                "available": True,
                "current_regime": {
                    "state": current_state.get("state"),
                    "maturity_phase": maturity,
                    "maturity_score": round(maturity_score, 1),
                    "consecutive_snapshots": consecutive,
                    "duration": duration,
                    "persistence_score": round(
                        persistence_score, 1
                    ),
                    "stability_score": round(
                        stability_score, 1
                    ),
                },
                "transition_assessment": {
                    "target_state": (
                        pressure.get("target_state")
                        or next_candidate.get("state")
                    ),
                    "transition_probability": round(
                        transition_probability, 1
                    ),
                    "transition_pressure": round(
                        pressure_score, 1
                    ),
                    "transition_readiness": round(
                        readiness_score, 1
                    ),
                    "confidence": next_state_confidence,
                    "status": self._transition_status(
                        transition_probability
                    ),
                },
                "trend_context": {
                    "readiness_trend": readiness_trend,
                    "probability_trend": probability_trend,
                    "state_score_trend": (
                        persistence.get(
                            "state_score_dynamics"
                        ) or {}
                    ).get("trend"),
                },
                "history_context": {
                    "total_snapshots": history_context.get(
                        "total_snapshots"
                    ),
                    "total_transitions": history_context.get(
                        "total_transitions"
                    ),
                    "current_state_share_pct": (
                        history_context.get(
                            "current_state_share_pct"
                        )
                    ),
                },
                "interpretation": interpretation,
                "source_context": {
                    "state_transition_engine_id": (
                        transition_response.get("engine_id")
                    ),
                    "persistence_engine_id": (
                        persistence_response.get("engine_id")
                    ),
                    "execution_state": (
                        current_transition.get(
                            "execution_state"
                        )
                    ),
                    "risk_state": (
                        current_transition.get("risk_state")
                    ),
                },
                "scope": {
                    "technical_only": True,
                    "predictive_model": False,
                    "deterministic_probability": True,
                    "automatic_execution": False,
                    "note": (
                        "Transition probability is a deterministic composite "
                        "derived from persistence, readiness, pressure and "
                        "regime stability. It is not a trained ML probability."
                    ),
                },
            },
        }

    def _maturity_phase(
        self,
        *,
        consecutive: int,
        duration_hours: float,
        persistence_score: float,
        stability_score: float,
        pressure_score: float,
        readiness_score: float,
        readiness_trend: dict[str, Any],
        probability_trend: dict[str, Any],
    ) -> str:
        rising_pressure = (
            str(readiness_trend.get("direction")).upper()
            == "RISING"
            or str(
                probability_trend.get("direction")
            ).upper()
            == "RISING"
        )

        if (
            pressure_score >= 75
            and readiness_score >= 75
        ):
            return "TRANSITION"

        if (
            pressure_score >= 60
            and rising_pressure
            and persistence_score >= 55
        ):
            return "EXHAUSTING"

        if (
            consecutive >= 6
            or duration_hours >= 12
            or (
                persistence_score >= 65
                and stability_score >= 65
            )
        ):
            return "MATURE"

        if (
            consecutive >= 3
            or duration_hours >= 2
            or persistence_score >= 45
        ):
            return "DEVELOPING"

        return "EARLY"

    def _transition_probability(
        self,
        *,
        next_probability: float,
        pressure_score: float,
        readiness_score: float,
        readiness_trend: dict[str, Any],
        probability_trend: dict[str, Any],
        stability_score: float,
        maturity: str,
    ) -> float:
        score = (
            next_probability * 0.35
            + pressure_score * 0.30
            + readiness_score * 0.20
            + (100.0 - stability_score) * 0.05
        )

        if (
            str(readiness_trend.get("direction")).upper()
            == "RISING"
        ):
            score += 5.0
        elif (
            str(readiness_trend.get("direction")).upper()
            == "FALLING"
        ):
            score -= 4.0

        if (
            str(probability_trend.get("direction")).upper()
            == "RISING"
        ):
            score += 5.0
        elif (
            str(probability_trend.get("direction")).upper()
            == "FALLING"
        ):
            score -= 4.0

        if maturity == "TRANSITION":
            score += 10.0
        elif maturity == "EXHAUSTING":
            score += 6.0
        elif maturity == "MATURE":
            score += 2.0

        return max(0.0, min(100.0, score))

    def _maturity_score(
        self,
        *,
        consecutive: int,
        duration_hours: float,
        persistence_score: float,
        stability_score: float,
        pressure_score: float,
    ) -> float:
        count_component = min(
            100.0,
            consecutive * 12.5,
        )

        duration_component = min(
            100.0,
            duration_hours * 6.0,
        )

        score = (
            count_component * 0.25
            + duration_component * 0.15
            + persistence_score * 0.30
            + stability_score * 0.20
            + pressure_score * 0.10
        )

        return max(0.0, min(100.0, score))

    def _next_state_confidence(
        self,
        *,
        transition_probability: float,
        pressure_score: float,
        transition_readiness_score: float,
    ) -> dict[str, Any]:
        score = (
            transition_probability * 0.50
            + pressure_score * 0.25
            + transition_readiness_score * 0.25
        )

        if score >= 80:
            state = "VERY_HIGH"
        elif score >= 65:
            state = "HIGH"
        elif score >= 50:
            state = "MODERATE"
        else:
            state = "LOW"

        return {
            "score": round(score, 1),
            "state": state,
        }

    def _transition_status(
        self,
        probability: float,
    ) -> str:
        if probability >= 80:
            return "IMMINENT"
        if probability >= 65:
            return "HIGH_WATCH"
        if probability >= 45:
            return "WATCH"
        return "LOW"

    def _interpretation(
        self,
        *,
        current_state: str,
        maturity: str,
        transition_probability: float,
        target_state: str,
    ) -> str:
        if maturity == "TRANSITION":
            return (
                f"{current_state} is in active transition toward "
                f"{target_state}."
            )

        if maturity == "EXHAUSTING":
            return (
                f"{current_state} remains active but transition pressure "
                f"is rising toward {target_state}."
            )

        if maturity == "MATURE":
            return (
                f"{current_state} is established and mature. "
                f"Transition probability is "
                f"{transition_probability:.1f}%."
            )

        if maturity == "DEVELOPING":
            return (
                f"{current_state} is developing but is not yet a mature "
                f"regime."
            )

        return (
            f"{current_state} is still early in its persistent history. "
            f"More observations are required."
        )

    @staticmethod
    def _number(
        value: Any,
        default: Any,
    ) -> float:
        try:
            if value is None:
                return float(default or 0.0)
            return float(value)
        except (TypeError, ValueError):
            try:
                return float(default or 0.0)
            except (TypeError, ValueError):
                return 0.0
