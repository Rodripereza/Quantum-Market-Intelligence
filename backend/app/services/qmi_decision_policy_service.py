from __future__ import annotations

from typing import Any


class QMIDecisionPolicyService:
    """
    DE-CORE-005.2 — Business-Aware Decision Policy / Action Engine

    Converts the cross-engine posture from DE-CORE-004.1 into a deterministic
    operational policy.

    This layer produces:
    - action policy
    - action intensity
    - timing status
    - invalidation conditions
    - upgrade conditions
    - downgrade conditions
    - re-evaluation triggers

    Important scope limits:
    - no order execution
    - no portfolio-size awareness yet
    - no autonomous BUY/HOLD/SELL instruction
    - technical capital-protection gates remain dominant
    """

    ENGINE = "QMI Decision Policy / Action Engine"
    ENGINE_ID = "DE-CORE-005.2"
    VERSION = "0.1.2"

    ACTION_PRIORITY = {
        "EXIT": 5,
        "REDUCE": 4,
        "WAIT": 3,
        "HOLD": 2,
        "ADD": 1,
    }

    def analyze(
        self,
        *,
        symbol: str,
        qmi_decision_response: dict[str, Any],
    ) -> dict[str, Any]:
        qmi = (
            qmi_decision_response.get("qmi_decision")
            if isinstance(qmi_decision_response, dict)
            else {}
        ) or {}

        if not qmi.get("available"):
            return self._insufficient(symbol)

        integrated_posture = str(
            qmi.get("integrated_posture") or "UNKNOWN"
        ).upper()
        timing_gate = str(qmi.get("timing_gate") or "MONITOR").upper()
        combined_score = self._number(qmi.get("combined_score"), 50.0)
        confidence = str(qmi.get("confidence") or "LOW").upper()

        technical = qmi.get("technical") or {}
        fundamental = qmi.get("fundamental") or {}
        business_momentum = qmi.get("business_momentum") or {}
        business_divergence = qmi.get("business_divergence") or {}
        alignment = qmi.get("alignment") or {}

        technical_posture = str(
            technical.get("posture") or "WAIT"
        ).upper()
        technical_risk = str(
            technical.get("risk_state") or "UNKNOWN"
        ).upper()
        technical_timing = str(
            technical.get("timing") or "UNKNOWN"
        ).upper()
        execution_state = str(
            technical.get("execution_state") or "UNKNOWN"
        ).upper()

        fundamental_stance = str(
            fundamental.get("stance") or "UNKNOWN"
        ).upper()
        alignment_state = str(
            alignment.get("state") or "UNKNOWN"
        ).upper()

        business_momentum_score = self._number_or_none(
            business_momentum.get("score")
        )
        business_momentum_regime = str(
            business_momentum.get("regime") or "UNKNOWN"
        ).upper()
        business_momentum_trend = str(
            business_momentum.get("trend") or "UNKNOWN"
        ).upper()
        business_momentum_confidence = str(
            business_momentum.get("confidence") or "LOW"
        ).upper()

        divergence_state = str(
            business_divergence.get("state") or "UNAVAILABLE"
        ).upper()
        divergence_severity = str(
            business_divergence.get("severity") or "NONE"
        ).upper()
        divergence_spread = self._number_or_none(
            business_divergence.get("spread")
        )

        action = self._select_action(
            integrated_posture=integrated_posture,
            timing_gate=timing_gate,
            combined_score=combined_score,
            technical_posture=technical_posture,
            technical_risk=technical_risk,
            fundamental_stance=fundamental_stance,
            business_momentum_score=business_momentum_score,
            business_momentum_trend=business_momentum_trend,
            divergence_state=divergence_state,
            divergence_severity=divergence_severity,
        )

        intensity = self._intensity(
            action=action,
            combined_score=combined_score,
            confidence=confidence,
            technical_risk=technical_risk,
            alignment_state=alignment_state,
            business_momentum_score=business_momentum_score,
            divergence_state=divergence_state,
            divergence_severity=divergence_severity,
        )

        policy_state = self._policy_state(
            action=action,
            timing_gate=timing_gate,
            technical_timing=technical_timing,
            execution_state=execution_state,
        )

        strategic_bias = self._strategic_bias(
            action=action,
            technical_risk=technical_risk,
            business_momentum_score=business_momentum_score,
            business_momentum_regime=business_momentum_regime,
            business_momentum_trend=business_momentum_trend,
            divergence_state=divergence_state,
            divergence_severity=divergence_severity,
        )

        rationale = self._rationale(
            action=action,
            intensity=intensity,
            integrated_posture=integrated_posture,
            timing_gate=timing_gate,
            technical_posture=technical_posture,
            fundamental_stance=fundamental_stance,
            confidence=confidence,
            business_momentum_score=business_momentum_score,
            business_momentum_regime=business_momentum_regime,
            business_momentum_trend=business_momentum_trend,
            divergence_state=divergence_state,
            divergence_severity=divergence_severity,
            strategic_bias=strategic_bias,
        )

        invalidation = self._invalidation_conditions(
            action=action,
            technical_posture=technical_posture,
            technical_risk=technical_risk,
            fundamental_stance=fundamental_stance,
            business_momentum_score=business_momentum_score,
            business_momentum_trend=business_momentum_trend,
        )

        upgrade_conditions = self._upgrade_conditions(
            action=action,
            technical_posture=technical_posture,
            technical_risk=technical_risk,
            fundamental_stance=fundamental_stance,
            alignment_state=alignment_state,
            business_momentum_score=business_momentum_score,
            business_momentum_trend=business_momentum_trend,
            divergence_state=divergence_state,
        )

        downgrade_conditions = self._downgrade_conditions(
            action=action,
            technical_posture=technical_posture,
            technical_risk=technical_risk,
            fundamental_stance=fundamental_stance,
            business_momentum_score=business_momentum_score,
            business_momentum_trend=business_momentum_trend,
            divergence_state=divergence_state,
        )

        reevaluation_triggers = self._reevaluation_triggers(
            action=action,
            timing_gate=timing_gate,
            technical_timing=technical_timing,
            qmi=qmi,
            business_momentum_score=business_momentum_score,
            business_momentum_trend=business_momentum_trend,
            divergence_state=divergence_state,
            divergence_severity=divergence_severity,
        )

        constraints = self._constraints(
            qmi=qmi,
            action=action,
        )

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "symbol": symbol.strip().upper(),
            "action_policy": {
                "available": True,
                "action": action,
                "intensity": intensity,
                "policy_state": policy_state,
                "strategic_bias": strategic_bias,
                "confidence": confidence,
                "combined_score": round(combined_score, 1),
                "integrated_posture": integrated_posture,
                "timing_gate": timing_gate,
                "business_context": {
                    "score": (
                        round(business_momentum_score, 1)
                        if business_momentum_score is not None
                        else None
                    ),
                    "regime": business_momentum_regime,
                    "trend": business_momentum_trend,
                    "confidence": business_momentum_confidence,
                    "divergence_state": divergence_state,
                    "divergence_spread": (
                        round(divergence_spread, 1)
                        if divergence_spread is not None
                        else None
                    ),
                    "divergence_severity": divergence_severity,
                },
                "rationale": rationale,
                "invalidation_conditions": invalidation,
                "upgrade_conditions": upgrade_conditions,
                "downgrade_conditions": downgrade_conditions,
                "reevaluation_triggers": reevaluation_triggers,
                "constraints": constraints,
                "source": {
                    "cross_engine_id": qmi_decision_response.get("engine_id"),
                    "technical_posture": technical_posture,
                    "technical_risk": technical_risk,
                    "technical_timing": technical_timing,
                    "execution_state": execution_state,
                    "fundamental_stance": fundamental_stance,
                    "business_momentum_score": business_momentum_score,
                    "business_momentum_regime": business_momentum_regime,
                    "business_momentum_trend": business_momentum_trend,
                    "business_divergence_state": divergence_state,
                    "business_divergence_severity": divergence_severity,
                    "alignment_state": alignment_state,
                },
                "scope": {
                    "portfolio_aware": False,
                    "position_aware": False,
                    "capital_allocation": False,
                    "automatic_execution": False,
                    "advisory_only": True,
                    "note": (
                        "ADD/HOLD/REDUCE/EXIT/WAIT are policy states only. "
                        "Portfolio-aware sizing and order execution are outside "
                        "DE-CORE-005.2."
                    ),
                },
            },
        }

    def _select_action(
        self,
        *,
        integrated_posture: str,
        timing_gate: str,
        combined_score: float,
        technical_posture: str,
        technical_risk: str,
        fundamental_stance: str,
        business_momentum_score: float | None,
        business_momentum_trend: str,
        divergence_state: str,
        divergence_severity: str,
    ) -> str:
        # Hard technical capital-protection gates always dominate.
        if timing_gate == "CAPITAL_PROTECTION" or technical_posture == "EXIT":
            return "EXIT"

        if timing_gate == "REDUCE_EXPOSURE" or technical_posture == "REDUCE":
            return "REDUCE"

        if timing_gate in {"WAIT", "TECHNICAL_UNAVAILABLE"}:
            return "WAIT"

        if technical_risk == "CRITICAL":
            return "REDUCE"

        # Actionable technical setup + supportive integrated/fundamental/business context.
        if timing_gate == "TECHNICALLY_ACTIONABLE":
            business_supportive = (
                business_momentum_score is None
                or (
                    business_momentum_score >= 60
                    and business_momentum_trend != "DECELERATING"
                )
            )
            business_warning = (
                divergence_state == "NEGATIVE_BUSINESS_DIVERGENCE"
                and divergence_severity == "HIGH"
            )

            if (
                integrated_posture in {"FAVORABLE", "CONSTRUCTIVE"}
                and fundamental_stance in {
                    "VERY_POSITIVE",
                    "POSITIVE",
                    "CONSTRUCTIVE",
                }
                and combined_score >= 65
                and business_supportive
                and not business_warning
            ):
                return "ADD"
            return "HOLD"

        if timing_gate == "PREPARE":
            return "HOLD"

        if integrated_posture in {"DEFENSIVE", "CAUTIOUS"}:
            return "HOLD"

        if integrated_posture in {
            "SELECTIVE",
            "CONSTRUCTIVE",
            "FAVORABLE",
            "CONSTRUCTIVE_BUT_WAIT",
        }:
            return "HOLD"

        return "WAIT"

    @staticmethod
    def _intensity(
        *,
        action: str,
        combined_score: float,
        confidence: str,
        technical_risk: str,
        alignment_state: str,
        business_momentum_score: float | None,
        divergence_state: str,
        divergence_severity: str,
    ) -> str:
        score = 0

        if confidence == "HIGH":
            score += 2
        elif confidence == "MEDIUM":
            score += 1

        if alignment_state in {"STRONG_ALIGNMENT", "ALIGNED"}:
            score += 2
        elif alignment_state == "PARTIAL_ALIGNMENT":
            score += 1

        if technical_risk == "CRITICAL":
            score += 2 if action in {"EXIT", "REDUCE"} else -2
        elif technical_risk in {"HIGH", "ELEVATED"}:
            score += 1 if action in {"EXIT", "REDUCE"} else -1

        if action == "ADD":
            if combined_score >= 78:
                score += 2
            elif combined_score >= 65:
                score += 1

        if action in {"EXIT", "REDUCE"}:
            if combined_score <= 35:
                score += 2
            elif combined_score <= 50:
                score += 1

        # Business context modifies conviction, but never overrides hard gates.
        if action == "ADD":
            if business_momentum_score is not None and business_momentum_score >= 75:
                score += 1
            if (
                divergence_state == "NEGATIVE_BUSINESS_DIVERGENCE"
                and divergence_severity == "HIGH"
            ):
                score -= 2

        if action in {"REDUCE", "EXIT"}:
            # Strong positive business divergence creates a re-entry watch bias.
            # It may soften intensity only when technical risk is NOT critical.
            if (
                technical_risk != "CRITICAL"
                and business_momentum_score is not None
                and business_momentum_score >= 75
                and divergence_state == "POSITIVE_BUSINESS_DIVERGENCE"
            ):
                score -= 1

        if score >= 5:
            return "HIGH"
        if score >= 2:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _policy_state(
        *,
        action: str,
        timing_gate: str,
        technical_timing: str,
        execution_state: str,
    ) -> str:
        if action in {"EXIT", "REDUCE"}:
            return "ACTIVE_RISK_CONTROL"

        if action == "WAIT":
            return "BLOCKED"

        if action == "ADD" and timing_gate == "TECHNICALLY_ACTIONABLE":
            return "ACTIONABLE"

        if technical_timing == "BLOCKED" or "WAIT" in execution_state:
            return "CONDITIONAL"

        if action == "HOLD":
            return "MAINTAIN"

        return "MONITOR"

    @staticmethod
    def _strategic_bias(
        *,
        action: str,
        technical_risk: str,
        business_momentum_score: float | None,
        business_momentum_regime: str,
        business_momentum_trend: str,
        divergence_state: str,
        divergence_severity: str,
    ) -> str:
        if (
            action in {"REDUCE", "EXIT", "WAIT"}
            and business_momentum_score is not None
            and business_momentum_score >= 70
            and business_momentum_trend in {"ACCELERATING", "STABLE"}
            and divergence_state == "POSITIVE_BUSINESS_DIVERGENCE"
        ):
            return "REENTRY_WATCH"

        if (
            action in {"HOLD", "ADD"}
            and divergence_state == "NEGATIVE_BUSINESS_DIVERGENCE"
            and divergence_severity in {"MEDIUM", "HIGH"}
        ):
            return "BUSINESS_CAUTION"

        if technical_risk == "CRITICAL":
            return "RISK_FIRST"

        if business_momentum_regime in {"STRONG_EXPANSION", "EXPANSION"}:
            return "CONSTRUCTIVE_BUSINESS_BIAS"

        return "NEUTRAL"

    @staticmethod
    def _rationale(
        *,
        action: str,
        intensity: str,
        integrated_posture: str,
        timing_gate: str,
        technical_posture: str,
        fundamental_stance: str,
        confidence: str,
        business_momentum_score: float | None,
        business_momentum_regime: str,
        business_momentum_trend: str,
        divergence_state: str,
        divergence_severity: str,
        strategic_bias: str,
    ) -> str:
        business_clause = ""
        if business_momentum_score is not None:
            business_clause = (
                f" Business momentum is {business_momentum_score:.1f}/100 "
                f"({business_momentum_regime.replace('_', ' ')}, "
                f"{business_momentum_trend.replace('_', ' ')})."
            )

        divergence_clause = ""
        if divergence_state != "UNAVAILABLE":
            divergence_clause = (
                f" Business/technical divergence is "
                f"{divergence_state.replace('_', ' ')} "
                f"({divergence_severity})."
            )

        bias_clause = (
            " Strong operating momentum is preserved as a re-entry watch, "
            "but it does not override the active technical protection gate."
            if strategic_bias == "REENTRY_WATCH"
            else f" Strategic bias: {strategic_bias.replace('_', ' ')}."
        )

        return (
            f"QMI policy is {action} with {intensity} intensity. "
            f"Integrated posture is {integrated_posture.replace('_', ' ')}, "
            f"technical posture is {technical_posture}, fundamental stance is "
            f"{fundamental_stance.replace('_', ' ')}, and the active timing "
            f"gate is {timing_gate.replace('_', ' ')}. Confidence: {confidence}."
            f"{business_clause}{divergence_clause}{bias_clause}"
        )

    @staticmethod
    def _invalidation_conditions(
        *,
        action: str,
        technical_posture: str,
        technical_risk: str,
        fundamental_stance: str,
        business_momentum_score: float | None,
        business_momentum_trend: str,
    ) -> list[str]:
        items: list[str] = []

        if action in {"REDUCE", "EXIT"}:
            items.append(
                "Risk-control policy is invalidated if technical posture "
                "recovers above the active protection gate."
            )
            items.append(
                "Technical risk must materially improve before the policy "
                "can be relaxed."
            )

        if action == "ADD":
            items.append(
                "ADD policy is invalidated if technical timing becomes blocked."
            )
            items.append(
                "ADD policy is invalidated if fundamental stance deteriorates "
                "to CAUTIOUS or NEGATIVE."
            )

        if action in {"WAIT", "HOLD"}:
            items.append(
                "Current policy is invalidated by a confirmed technical regime "
                "change that activates a stronger action gate."
            )

        if technical_risk == "CRITICAL":
            items.append(
                "Critical technical risk remains a hard constraint."
            )

        if fundamental_stance == "NEGATIVE":
            items.append(
                "Negative fundamental stance prevents constructive escalation."
            )

        if action == "ADD" and business_momentum_score is not None:
            items.append(
                "ADD policy is invalidated if Business Momentum falls below 60/100."
            )

        if action == "ADD" and business_momentum_trend == "DECELERATING":
            items.append(
                "Decelerating Business Momentum invalidates aggressive escalation."
            )

        return list(dict.fromkeys(items))

    @staticmethod
    def _upgrade_conditions(
        *,
        action: str,
        technical_posture: str,
        technical_risk: str,
        fundamental_stance: str,
        alignment_state: str,
        business_momentum_score: float | None,
        business_momentum_trend: str,
        divergence_state: str,
    ) -> list[str]:
        items: list[str] = []

        if action in {"REDUCE", "EXIT", "WAIT", "HOLD"}:
            items.append(
                "Technical posture improves to PREPARE, ENTER or ADD."
            )
            items.append(
                "Technical risk improves away from CRITICAL/HIGH conditions."
            )

        if fundamental_stance in {"CONSTRUCTIVE", "POSITIVE", "VERY_POSITIVE"}:
            items.append(
                "Fundamental stance remains constructive or improves."
            )
        else:
            items.append(
                "Fundamental stance improves to CONSTRUCTIVE or better."
            )

        if alignment_state not in {"STRONG_ALIGNMENT", "ALIGNED"}:
            items.append(
                "Technical and fundamental engines move into ALIGNED or "
                "STRONG ALIGNMENT."
            )

        if business_momentum_score is not None and business_momentum_score >= 70:
            items.append(
                "Business Momentum remains above 70/100 while technical posture confirms recovery."
            )
        elif business_momentum_score is not None:
            items.append(
                "Business Momentum improves above 70/100 before constructive escalation."
            )

        if business_momentum_trend == "DECELERATING":
            items.append(
                "Business Momentum trend stops decelerating."
            )

        if divergence_state == "POSITIVE_BUSINESS_DIVERGENCE":
            items.append(
                "Positive business divergence begins to close through technical price confirmation."
            )

        return list(dict.fromkeys(items))

    @staticmethod
    def _downgrade_conditions(
        *,
        action: str,
        technical_posture: str,
        technical_risk: str,
        fundamental_stance: str,
        business_momentum_score: float | None,
        business_momentum_trend: str,
        divergence_state: str,
    ) -> list[str]:
        items: list[str] = []

        if technical_posture not in {"REDUCE", "EXIT"}:
            items.append(
                "Technical posture deteriorates to REDUCE or EXIT."
            )

        if technical_risk != "CRITICAL":
            items.append(
                "Technical risk escalates to CRITICAL."
            )

        if fundamental_stance not in {"CAUTIOUS", "NEGATIVE"}:
            items.append(
                "Fundamental stance deteriorates to CAUTIOUS or NEGATIVE."
            )

        if action == "ADD":
            items.append(
                "Execution timing becomes blocked or risk gates reactivate."
            )

        if business_momentum_score is not None and business_momentum_score >= 60:
            items.append(
                "Business Momentum deteriorates below 60/100."
            )

        if business_momentum_trend != "DECELERATING":
            items.append(
                "Business Momentum shifts to DECELERATING."
            )

        if divergence_state != "NEGATIVE_BUSINESS_DIVERGENCE":
            items.append(
                "Business/technical relationship turns into NEGATIVE BUSINESS DIVERGENCE."
            )

        return list(dict.fromkeys(items))

    @staticmethod
    def _reevaluation_triggers(
        *,
        action: str,
        timing_gate: str,
        technical_timing: str,
        qmi: dict[str, Any],
        business_momentum_score: float | None,
        business_momentum_trend: str,
        divergence_state: str,
        divergence_severity: str,
    ) -> list[str]:
        triggers = [
            "Re-evaluate after the next material technical state transition.",
            "Re-evaluate when the fundamental decision score or stance changes.",
            "Re-evaluate when cross-engine alignment changes materially.",
        ]

        if timing_gate in {"REDUCE_EXPOSURE", "CAPITAL_PROTECTION"}:
            triggers.append(
                "Re-evaluate immediately if the active protection gate clears."
            )

        if technical_timing == "BLOCKED":
            triggers.append(
                "Re-evaluate when technical timing is no longer BLOCKED."
            )

        if qmi.get("conflicts"):
            triggers.append(
                "Re-evaluate when the currently reported engine conflicts resolve."
            )

        if business_momentum_score is not None:
            triggers.append(
                "Re-evaluate when Business Momentum changes materially."
            )

        if business_momentum_trend in {"ACCELERATING", "DECELERATING"}:
            triggers.append(
                "Re-evaluate when the Business Momentum trend changes state."
            )

        if divergence_state in {
            "POSITIVE_BUSINESS_DIVERGENCE",
            "NEGATIVE_BUSINESS_DIVERGENCE",
        }:
            triggers.append(
                "Re-evaluate when the Business/Technical divergence materially narrows, widens or changes sign."
            )

        if divergence_severity == "HIGH":
            triggers.append(
                "High-severity business divergence requires continued confirmation monitoring."
            )

        return list(dict.fromkeys(triggers))

    @staticmethod
    def _constraints(
        *,
        qmi: dict[str, Any],
        action: str,
    ) -> list[str]:
        items = [
            "Portfolio exposure and position size are not yet included.",
            "Action is advisory policy only; no order is generated.",
        ]

        if qmi.get("timing_gate") in {
            "REDUCE_EXPOSURE",
            "CAPITAL_PROTECTION",
            "WAIT",
        }:
            items.append(
                "Technical timing gate cannot be overridden by fundamentals."
            )

        for conflict in qmi.get("conflicts") or []:
            if conflict not in items:
                items.append(str(conflict))

        return list(dict.fromkeys(items))[:12]

    @staticmethod
    def _number(value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return float(default)
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def _number_or_none(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    def _insufficient(self, symbol: str) -> dict[str, Any]:
        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "insufficient_data",
            "symbol": symbol.strip().upper(),
            "action_policy": {
                "available": False,
                "action": "WAIT",
                "intensity": "LOW",
                "policy_state": "BLOCKED",
                "confidence": "LOW",
                "reason": (
                    "Cross-engine decision data is not available."
                ),
            },
        }
