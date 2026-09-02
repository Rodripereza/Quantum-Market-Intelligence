from __future__ import annotations

from typing import Any

from app.services.qmi_decision_performance_analytics_service import (
    QMIDecisionPerformanceAnalyticsService,
)


class QMICalibrationLearningService:
    """
    DE-CORE-006.7 — Calibration & Learning Foundation

    Converts observed Decision Performance Analytics into guarded,
    read-only calibration recommendations.

    HARD BOUNDARIES:
    - no model training
    - no Decision Engine weight mutation
    - no threshold mutation
    - no automatic policy calibration
    - no order/execution behavior

    This layer answers:
      "What does the accumulated evidence suggest we should review?"
    It does NOT answer:
      "Change the engine automatically."
    """

    ENGINE = "QMI Calibration & Learning Foundation"
    ENGINE_ID = "DE-CORE-006.7"
    VERSION = "0.1.0"

    INITIAL_SAMPLE = 20
    DEVELOPING_SAMPLE = 50
    ROBUST_SAMPLE = 100

    def __init__(
        self,
        performance_service: QMIDecisionPerformanceAnalyticsService | None = None,
    ) -> None:
        self.performance_service = (
            performance_service or QMIDecisionPerformanceAnalyticsService()
        )

    def analyze_symbol(
        self,
        symbol: str,
        *,
        limit: int = 1000,
    ) -> dict[str, Any]:
        performance = self.performance_service.analyze_symbol(
            symbol,
            limit=limit,
        )
        return self._build_calibration_report(performance)

    def analyze_all(
        self,
        symbols: list[str],
        *,
        limit_per_symbol: int = 1000,
    ) -> dict[str, Any]:
        performance = self.performance_service.analyze_all(
            symbols,
            limit_per_symbol=limit_per_symbol,
        )
        return self._build_calibration_report(performance)

    def _build_calibration_report(
        self,
        performance: dict[str, Any],
    ) -> dict[str, Any]:
        summary = performance.get("summary") or {}
        maturity = summary.get("sample_maturity") or {}
        by_action = performance.get("performance_by_action") or {}
        by_confidence = performance.get("performance_by_confidence") or {}

        action_assessments = {
            action: self._assess_action(action, segment)
            for action, segment in by_action.items()
        }

        confidence_assessments = {
            confidence: self._assess_confidence(confidence, segment)
            for confidence, segment in by_confidence.items()
        }

        actionable = [
            item for item in action_assessments.values()
            if item["recommendation"]["review_allowed"]
        ]

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "scope": performance.get("scope"),
            "symbol": performance.get("symbol"),
            "symbols": performance.get("symbols"),
            "evidence_state": {
                "decision_count": summary.get("decision_count", 0),
                "complete_20d_samples": maturity.get(
                    "complete_20d_samples", 0
                ),
                "sample_maturity": maturity.get(
                    "state", "INSUFFICIENT"
                ),
                "minimum_for_initial_interpretation": self.INITIAL_SAMPLE,
                "calibration_review_allowed": bool(actionable),
            },
            "calibration_by_action": action_assessments,
            "calibration_by_confidence": confidence_assessments,
            "recommendations": actionable,
            "guardrails": {
                "advisory_only": True,
                "auto_training": False,
                "automatic_weight_changes": False,
                "automatic_threshold_changes": False,
                "automatic_policy_calibration": False,
                "minimum_sample_per_action_horizon": self.INITIAL_SAMPLE,
                "note": (
                    "006.7 produces evidence-based review recommendations only. "
                    "Any future parameter change must be explicit, versioned, "
                    "auditable and separately approved."
                ),
            },
            "source": {
                "engine_id": performance.get("engine_id"),
                "performance_version": performance.get("version"),
            },
        }

    def _assess_action(
        self,
        action: str,
        segment: dict[str, Any],
    ) -> dict[str, Any]:
        horizons = segment.get("horizons") or {}
        horizon_assessments = {}

        for horizon in ("1d", "5d", "20d"):
            metrics = horizons.get(horizon) or {}
            horizon_assessments[horizon] = self._assess_horizon(
                action=action,
                horizon=horizon,
                metrics=metrics,
            )

        primary = horizon_assessments["20d"]
        if primary["sample_size"] < self.INITIAL_SAMPLE:
            recommendation = {
                "state": "COLLECT_MORE_DATA",
                "review_allowed": False,
                "target": None,
                "message": (
                    f"{action} has insufficient +20D evidence for calibration. "
                    f"Need at least {self.INITIAL_SAMPLE} scored observations."
                ),
            }
        else:
            favorable = primary.get("favorable_rate_pct")
            avg_return = primary.get("average_return_pct")
            direction = self._direction(action)

            if direction == 0:
                recommendation = {
                    "state": "NON_DIRECTIONAL_ACTION",
                    "review_allowed": False,
                    "target": None,
                    "message": (
                        f"{action} is not directionally scored in 006.7. "
                        "A dedicated opportunity-cost / drawdown framework is "
                        "required before calibrating this action."
                    ),
                }
            elif favorable is None:
                recommendation = {
                    "state": "INSUFFICIENT_DIRECTIONAL_EVIDENCE",
                    "review_allowed": False,
                    "target": None,
                    "message": (
                        f"{action} has no directionally scored +20D evidence."
                    ),
                }
            elif favorable >= 65:
                recommendation = {
                    "state": "SUPPORT_CURRENT_CALIBRATION",
                    "review_allowed": True,
                    "target": "ACTION_POLICY",
                    "message": (
                        f"{action} shows supportive +20D directional evidence. "
                        "Preserve current calibration pending broader samples."
                    ),
                }
            elif favorable < 45:
                recommendation = {
                    "state": "REVIEW_CALIBRATION",
                    "review_allowed": True,
                    "target": "ACTION_POLICY",
                    "message": (
                        f"{action} shows weak +20D directional evidence. "
                        "Review thresholds/conditions; do not change them automatically."
                    ),
                }
            else:
                recommendation = {
                    "state": "MIXED_EVIDENCE",
                    "review_allowed": True,
                    "target": "ACTION_POLICY",
                    "message": (
                        f"{action} shows mixed +20D evidence. "
                        "Collect more observations before proposing parameter changes."
                    ),
                }

        return {
            "action": action,
            "decision_count": segment.get("decision_count", 0),
            "evidence": horizon_assessments,
            "excursion_20d": segment.get("excursion_20d") or {},
            "recommendation": recommendation,
        }

    def _assess_confidence(
        self,
        confidence: str,
        segment: dict[str, Any],
    ) -> dict[str, Any]:
        horizons = segment.get("horizons") or {}
        coverage = {}

        for horizon in ("1d", "5d", "20d"):
            metrics = horizons.get(horizon) or {}
            n = int(metrics.get("sample_size") or 0)
            coverage[horizon] = {
                "sample_size": n,
                "evidence_grade": self._evidence_grade(n),
                "average_return_pct": metrics.get("average_return_pct"),
                "median_return_pct": metrics.get("median_return_pct"),
            }

        n20 = coverage["20d"]["sample_size"]
        return {
            "confidence": confidence,
            "decision_count": segment.get("decision_count", 0),
            "coverage": coverage,
            "interpretation_allowed": n20 >= self.INITIAL_SAMPLE,
            "note": (
                "Confidence calibration remains descriptive in 006.7; "
                "confidence thresholds are not modified."
            ),
        }

    def _assess_horizon(
        self,
        *,
        action: str,
        horizon: str,
        metrics: dict[str, Any],
    ) -> dict[str, Any]:
        n = int(metrics.get("sample_size") or 0)
        return {
            "horizon": horizon,
            "sample_size": n,
            "evidence_grade": self._evidence_grade(n),
            "average_return_pct": metrics.get("average_return_pct"),
            "median_return_pct": metrics.get("median_return_pct"),
            "favorable_rate_pct": metrics.get("favorable_rate_pct"),
            "directionally_scored_n": metrics.get(
                "directionally_scored_n", 0
            ),
            "interpretation_allowed": n >= self.INITIAL_SAMPLE,
            "action_direction": self._direction_label(action),
        }

    def _evidence_grade(self, sample_size: int) -> str:
        if sample_size >= self.ROBUST_SAMPLE:
            return "ROBUST"
        if sample_size >= self.DEVELOPING_SAMPLE:
            return "DEVELOPING"
        if sample_size >= self.INITIAL_SAMPLE:
            return "EARLY"
        return "INSUFFICIENT"

    @staticmethod
    def _direction(action: str) -> int:
        action = str(action or "").upper()
        if action in {"ACCUMULATE", "BUY", "INCREASE", "ADD", "STRONG_BUY"}:
            return 1
        if action in {"REDUCE", "SELL", "DECREASE", "TRIM", "STRONG_SELL"}:
            return -1
        return 0

    def _direction_label(self, action: str) -> str:
        direction = self._direction(action)
        if direction > 0:
            return "POSITIVE_RETURN_FAVORABLE"
        if direction < 0:
            return "NEGATIVE_RETURN_FAVORABLE"
        return "NON_DIRECTIONAL"
