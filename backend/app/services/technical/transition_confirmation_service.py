from __future__ import annotations

from typing import Any


class TechnicalTransitionConfirmationService:
    """
    DE-TA-014.4 — Transition Confirmation & State Change Engine

    Confirms or rejects a candidate state transition by combining:
    - regime maturity
    - deterministic transition probability
    - transition readiness
    - persistence depth
    - consecutive confirmations
    - critical blockers / risk state

    IMPORTANT:
    - This version does NOT mutate persistent state history directly.
    - It emits a confirmation decision that can be persisted/audited later.
    """

    def analyze(
        self,
        *,
        maturity_response: dict[str, Any],
        persistence_response: dict[str, Any],
        transition_response: dict[str, Any],
        execution_response: dict[str, Any],
        action_response: dict[str, Any],
        risk_response: dict[str, Any],
    ) -> dict[str, Any]:
        maturity = maturity_response.get("regime_maturity") or {}
        persistence = persistence_response.get("state_persistence") or {}
        transition = transition_response.get("technical_state_transition") or {}
        execution = execution_response.get("technical_execution_plan") or {}
        action = action_response.get("technical_action") or {}
        risk = risk_response.get("technical_risk_exposure") or {}

        if not maturity.get("available", False):
            return {
                "engine": "QMI Transition Confirmation & State Change Engine",
                "engine_id": "DE-TA-014.4",
                "version": "0.1.0",
                "status": "insufficient_history",
                "transition_confirmation": {
                    "available": False,
                    "reason": maturity.get(
                        "reason",
                        "Insufficient maturity history.",
                    ),
                },
            }

        current_regime = maturity.get("current_regime") or {}
        assessment = maturity.get("transition_assessment") or {}
        trend_context = maturity.get("trend_context") or {}
        history_context = maturity.get("history_context") or {}

        persistence_strength = persistence.get("persistence_strength") or {}
        stability = persistence.get("regime_stability") or {}
        current_state_persistence = persistence.get("current_state") or {}

        current_transition = transition.get("current_state") or {}
        transition_readiness = transition.get("transition_readiness") or {}
        next_candidate = transition.get("next_state_candidate") or {}

        execution_state = execution.get("execution_state") or {}
        action_matrix = execution.get("action_matrix") or {}

        action_posture = action.get("action_posture") or {}
        action_gates = action.get("confirmation_gates") or []
        action_invalidations = action.get("invalidation_gates") or []

        risk_regime = risk.get("risk_regime") or {}
        risk_flags = risk.get("protective_controls") or []

        current_state = str(
            current_regime.get("state")
            or current_transition.get("state")
            or "UNKNOWN"
        ).upper()

        target_state = str(
            assessment.get("target_state")
            or next_candidate.get("state")
            or current_state
        ).upper()

        transition_probability = self._number(
            assessment.get("transition_probability"), 0.0
        )
        readiness_score = self._number(
            transition_readiness.get("score"),
            assessment.get("transition_readiness"),
        )
        persistence_score = self._number(
            persistence_strength.get("score"), 0.0
        )
        stability_score = self._number(
            stability.get("score"), 0.0
        )

        maturity_phase = str(
            current_regime.get("maturity_phase") or "EARLY"
        ).upper()

        consecutive_snapshots = int(
            current_state_persistence.get("consecutive_snapshots") or 0
        )
        total_snapshots = int(history_context.get("total_snapshots") or 0)

        blockers = self._critical_blockers(
            risk_regime=risk_regime,
            risk_flags=risk_flags,
            execution_state=execution_state,
            action_matrix=action_matrix,
            action_posture=action_posture,
            action_gates=action_gates,
            target_state=target_state,
        )

        evidence = self._evidence(
            transition_probability=transition_probability,
            readiness_score=readiness_score,
            persistence_score=persistence_score,
            stability_score=stability_score,
            maturity_phase=maturity_phase,
            consecutive_snapshots=consecutive_snapshots,
            total_snapshots=total_snapshots,
            trend_context=trend_context,
        )

        decision = self._confirmation_decision(
            evidence=evidence,
            blockers=blockers,
            current_state=current_state,
            target_state=target_state,
        )

        confirmation_score = self._confirmation_score(
            evidence=evidence,
            blockers=blockers,
        )

        state_change = self._state_change_payload(
            decision=decision,
            current_state=current_state,
            target_state=target_state,
            confirmation_score=confirmation_score,
            transition_probability=transition_probability,
            readiness_score=readiness_score,
        )

        return {
            "engine": "QMI Transition Confirmation & State Change Engine",
            "engine_id": "DE-TA-014.4",
            "version": "0.1.0",
            "status": "operational",
            "transition_confirmation": {
                "available": True,
                "current_state": current_state,
                "target_state": target_state,
                "decision": decision,
                "confirmation_score": round(confirmation_score, 1),
                "evidence": evidence,
                "blockers": blockers,
                "state_change": state_change,
                "invalidation_watch": self._invalidation_watch(
                    action_invalidations
                ),
                "source_context": {
                    "maturity_phase": maturity_phase,
                    "transition_probability": round(
                        transition_probability, 1
                    ),
                    "transition_readiness": round(
                        readiness_score, 1
                    ),
                    "persistence_score": round(
                        persistence_score, 1
                    ),
                    "stability_score": round(
                        stability_score, 1
                    ),
                    "consecutive_snapshots": consecutive_snapshots,
                    "risk_state": risk_regime.get("state"),
                    "execution_state": execution_state.get("state"),
                    "execution_confidence": (
                        execution.get("execution_confidence") or {}
                    ).get("score"),
                    "primary_scenario": (
                        execution.get("source_context") or {}
                    ).get("primary_scenario"),
                    "direction_score": (
                        execution.get("source_context") or {}
                    ).get("direction_score"),
                    "action_permissions": {
                        "WAIT": (
                            action_matrix.get("WAIT") or {}
                        ).get("state"),
                        "ENTER": (
                            action_matrix.get("ENTER") or {}
                        ).get("state"),
                        "ADD": (
                            action_matrix.get("ADD") or {}
                        ).get("state"),
                        "REDUCE": (
                            action_matrix.get("REDUCE") or {}
                        ).get("state"),
                        "EXIT": (
                            action_matrix.get("EXIT") or {}
                        ).get("state"),
                    },
                },
                "scope": {
                    "technical_only": True,
                    "persistent_state_mutation": False,
                    "automatic_execution": False,
                    "note": (
                        "DE-TA-014.4 confirms transition eligibility. "
                        "Persistent state mutation/audit remains separate."
                    ),
                },
            },
        }

    def _critical_blockers(
        self,
        *,
        risk_regime: dict[str, Any],
        risk_flags: list[Any],
        execution_state: dict[str, Any],
        action_matrix: dict[str, Any],
        action_posture: dict[str, Any],
        action_gates: list[Any],
        target_state: str,
    ) -> list[dict[str, Any]]:
        blockers: list[dict[str, Any]] = []

        risk_state = str(
            risk_regime.get("state") or ""
        ).upper()

        if target_state in {
            "STABILIZING",
            "WATCH_REVERSAL",
            "ENTRY_ELIGIBLE",
            "CONSTRUCTIVE",
        } and risk_state == "CRITICAL":
            blockers.append({
                "type": "RISK",
                "severity": "CRITICAL",
                "reason": "Risk regime remains CRITICAL.",
            })

        exec_state = str(
            execution_state.get("state") or ""
        ).upper()

        if (
            target_state in {"ENTRY_ELIGIBLE", "CONSTRUCTIVE"}
            and exec_state == "WAIT_DEFENSIVE"
        ):
            blockers.append({
                "type": "EXECUTION",
                "severity": "HIGH",
                "reason": (
                    "Execution state remains WAIT_DEFENSIVE."
                ),
            })

        enter_state = str(
            (action_matrix.get("ENTER") or {}).get("state") or ""
        ).upper()

        if (
            target_state in {"ENTRY_ELIGIBLE", "CONSTRUCTIVE"}
            and enter_state == "BLOCKED"
        ):
            blockers.append({
                "type": "ACTION",
                "severity": "HIGH",
                "reason": "ENTER action remains BLOCKED.",
            })

        posture_state = str(
            action_posture.get("state") or ""
        ).upper()

        if (
            target_state == "CONSTRUCTIVE"
            and posture_state in {
                "DEFENSIVE",
                "DEFENSIVE_RESTRICTED",
            }
        ):
            blockers.append({
                "type": "POSTURE",
                "severity": "HIGH",
                "reason": (
                    "Action posture remains defensive."
                ),
            })

        open_critical_gates = 0
        for gate in action_gates:
            if not isinstance(gate, dict):
                continue

            priority = gate.get("priority")
            status = str(gate.get("status") or "OPEN").upper()

            if priority in {1, 2} and status not in {
                "CLOSED",
                "VALIDATED",
                "CONFIRMED",
            }:
                open_critical_gates += 1

        if target_state in {
            "WATCH_REVERSAL",
            "ENTRY_ELIGIBLE",
            "CONSTRUCTIVE",
        } and open_critical_gates:
            blockers.append({
                "type": "CONFIRMATION_GATES",
                "severity": "HIGH",
                "reason": (
                    f"{open_critical_gates} priority confirmation "
                    "gates remain open."
                ),
            })

        for item in risk_flags:
            if not isinstance(item, dict):
                continue

            state = str(item.get("state") or "").upper()
            control = str(item.get("control") or "")

            if state in {"HARD_BLOCK", "PROHIBITED"}:
                blockers.append({
                    "type": "PROTECTIVE_CONTROL",
                    "severity": "HIGH",
                    "reason": f"{control}: {state}",
                })

        return blockers

    def _evidence(
        self,
        *,
        transition_probability: float,
        readiness_score: float,
        persistence_score: float,
        stability_score: float,
        maturity_phase: str,
        consecutive_snapshots: int,
        total_snapshots: int,
        trend_context: dict[str, Any],
    ) -> dict[str, Any]:
        maturity_points = {
            "EARLY": 20.0,
            "DEVELOPING": 45.0,
            "MATURE": 70.0,
            "EXHAUSTING": 82.0,
            "TRANSITION": 95.0,
        }.get(maturity_phase, 20.0)

        snapshot_depth_score = min(
            100.0,
            consecutive_snapshots * 12.5,
        )

        trend_bonus = 0.0

        readiness_trend = (
            trend_context.get("readiness_trend") or {}
        )
        probability_trend = (
            trend_context.get("probability_trend") or {}
        )

        if str(
            readiness_trend.get("direction")
        ).upper() == "RISING":
            trend_bonus += 8.0

        if str(
            probability_trend.get("direction")
        ).upper() == "RISING":
            trend_bonus += 8.0

        composite = (
            transition_probability * 0.25
            + readiness_score * 0.20
            + persistence_score * 0.15
            + stability_score * 0.10
            + maturity_points * 0.15
            + snapshot_depth_score * 0.15
            + trend_bonus
        )

        composite = max(0.0, min(100.0, composite))

        return {
            "composite_score": round(composite, 1),
            "transition_probability": round(
                transition_probability, 1
            ),
            "transition_readiness": round(
                readiness_score, 1
            ),
            "persistence_score": round(
                persistence_score, 1
            ),
            "stability_score": round(
                stability_score, 1
            ),
            "maturity_phase": maturity_phase,
            "consecutive_snapshots": consecutive_snapshots,
            "total_snapshots": total_snapshots,
            "trend_bonus": round(trend_bonus, 1),
        }

    def _confirmation_decision(
        self,
        *,
        evidence: dict[str, Any],
        blockers: list[dict[str, Any]],
        current_state: str,
        target_state: str,
    ) -> str:
        if target_state == current_state:
            return "HOLD_STATE"

        critical_blocker = any(
            str(item.get("severity")).upper() == "CRITICAL"
            for item in blockers
        )

        if critical_blocker:
            return "BLOCKED"

        score = self._number(
            evidence.get("composite_score"), 0.0
        )
        probability = self._number(
            evidence.get("transition_probability"), 0.0
        )
        readiness = self._number(
            evidence.get("transition_readiness"), 0.0
        )
        consecutive = int(
            evidence.get("consecutive_snapshots") or 0
        )

        if (
            score >= 82
            and probability >= 75
            and readiness >= 75
            and consecutive >= 3
            and not blockers
        ):
            return "CONFIRMED"

        if (
            score >= 68
            and probability >= 60
            and readiness >= 65
            and consecutive >= 2
        ):
            return "PRECONFIRMED"

        return "WATCH"

    def _confirmation_score(
        self,
        *,
        evidence: dict[str, Any],
        blockers: list[dict[str, Any]],
    ) -> float:
        score = self._number(
            evidence.get("composite_score"), 0.0
        )

        penalty = 0.0
        for blocker in blockers:
            severity = str(
                blocker.get("severity") or ""
            ).upper()

            if severity == "CRITICAL":
                penalty += 25.0
            elif severity == "HIGH":
                penalty += 12.0
            elif severity == "MODERATE":
                penalty += 6.0

        return max(0.0, min(100.0, score - penalty))

    def _state_change_payload(
        self,
        *,
        decision: str,
        current_state: str,
        target_state: str,
        confirmation_score: float,
        transition_probability: float,
        readiness_score: float,
    ) -> dict[str, Any]:
        eligible = decision == "CONFIRMED"

        return {
            "eligible": eligible,
            "from_state": current_state,
            "to_state": target_state if eligible else current_state,
            "candidate_state": target_state,
            "decision": decision,
            "confirmation_score": round(
                confirmation_score, 1
            ),
            "transition_probability": round(
                transition_probability, 1
            ),
            "transition_readiness": round(
                readiness_score, 1
            ),
        }

    def _invalidation_watch(
        self,
        invalidations: list[Any],
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []

        for item in invalidations:
            if not isinstance(item, dict):
                continue

            result.append({
                "priority": item.get("priority"),
                "condition": item.get("condition"),
                "status": item.get("status", "MONITOR"),
            })

        return result

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
