from __future__ import annotations

from typing import Any


class DecisionValidationMomentumService:
    """DE-DI-017 — Validation Momentum.

    Reads persisted DE-DI-016 validation observations and measures whether
    validation evidence is accelerating, stable or losing momentum.
    Diagnostic only: never changes the live decision or execution.
    """

    ENGINE_ID = "DE-DI-017"
    VERSION = "0.1.0"
    MIN_POINTS = 3

    def analyze(
        self,
        *,
        validation_state: dict[str, Any] | None,
        validation_history: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        current = (validation_state or {}).get("decision_validation_state") or {}
        history = list(validation_history or [])

        # History arrives newest-first. Current DE-DI-016 observation has already
        # been persisted, so use persisted rows as the canonical time series.
        chronological = list(reversed(history))
        scores = [self._num(row.get("evidence_score")) for row in chronological]
        scores = [v for v in scores if v is not None]

        available = len(scores) >= self.MIN_POINTS
        if not available:
            return {
                "engine_id": self.ENGINE_ID,
                "version": self.VERSION,
                "status": "operational",
                "decision_validation_momentum": {
                    "available": False,
                    "state": "INSUFFICIENT_HISTORY",
                    "momentum_score": None,
                    "recent_slope": None,
                    "previous_slope": None,
                    "acceleration": None,
                    "point_count": len(scores),
                    "minimum_points": self.MIN_POINTS,
                    "assessment": f"Validation Momentum activates after {self.MIN_POINTS} persisted validation observations.",
                    "scope": self._scope(),
                },
            }

        recent = scores[-min(5, len(scores)):]
        recent_slope = self._slope(recent)

        if len(scores) >= 5:
            prior_window = scores[-min(8, len(scores)):-2]
            previous_slope = self._slope(prior_window) if len(prior_window) >= 2 else 0.0
        else:
            previous_slope = self._slope(scores[:-1]) if len(scores[:-1]) >= 2 else 0.0

        acceleration = recent_slope - previous_slope
        momentum_score = max(-100.0, min(100.0, recent_slope * 12.0 + acceleration * 8.0))
        state = self._state(momentum_score, recent_slope)

        posture = str(current.get("decision_posture") or "UNKNOWN").upper()
        validation = str(current.get("validation_state") or "UNVALIDATED").upper()

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_validation_momentum": {
                "available": True,
                "decision_posture": posture,
                "validation_state": validation,
                "state": state,
                "momentum_score": round(momentum_score, 1),
                "recent_slope": round(recent_slope, 2),
                "previous_slope": round(previous_slope, 2),
                "acceleration": round(acceleration, 2),
                "point_count": len(scores),
                "score_series": [round(v, 1) for v in scores[-12:]],
                "assessment": self._assessment(posture, validation, state, recent_slope, acceleration),
                "scope": self._scope(),
            },
        }

    @staticmethod
    def _slope(values: list[float]) -> float:
        if len(values) < 2:
            return 0.0
        n = len(values)
        x_mean = (n - 1) / 2
        y_mean = sum(values) / n
        denom = sum((i - x_mean) ** 2 for i in range(n))
        if denom == 0:
            return 0.0
        return sum((i - x_mean) * (v - y_mean) for i, v in enumerate(values)) / denom

    @staticmethod
    def _state(momentum: float, slope: float) -> str:
        if momentum >= 20.0 and slope > 0:
            return "ACCELERATING"
        if momentum >= 5.0:
            return "STRENGTHENING"
        if momentum <= -20.0 and slope < 0:
            return "DETERIORATING"
        if momentum <= -5.0:
            return "WEAKENING"
        return "STABLE"

    @staticmethod
    def _assessment(posture: str, validation: str, state: str, slope: float, acceleration: float) -> str:
        p = posture.title()
        v = validation.replace("_", " ").lower()
        if state == "ACCELERATING":
            return f"{p} remains {v}; validation evidence is strengthening at an accelerating rate."
        if state == "STRENGTHENING":
            return f"{p} remains {v}; validation evidence is strengthening."
        if state == "DETERIORATING":
            return f"{p} remains {v}; validation evidence is deteriorating with negative momentum."
        if state == "WEAKENING":
            return f"{p} remains {v}; validation evidence is weakening."
        return f"{p} remains {v}; validation momentum is stable."

    @staticmethod
    def _scope():
        return {
            "diagnostic_only": True,
            "automatic_decision_changes": False,
            "automatic_permission_changes": False,
            "automatic_execution_changes": False,
        }

    @staticmethod
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None
