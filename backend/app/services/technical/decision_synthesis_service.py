from __future__ import annotations

from typing import Any


class TechnicalDecisionSynthesisService:
    """
    DE-TA-015.0 — Technical Decision Synthesis Engine
    PERF revision 0.1.1

    Final deterministic synthesis layer for the technical pipeline.

    This revision consumes DE-TA-014.4 only. DE-TA-014.4 already evaluates
    execution, action and risk upstream, and exposes the minimum context needed
    by this synthesis layer. This avoids recalculating DE-TA-013.0 a second time.

    IMPORTANT:
    - This engine does not execute trades.
    - This engine does not mutate persistent state.
    - This engine must not relax upstream technical gates.
    """

    def analyze(
        self,
        *,
        confirmation_response: dict[str, Any],
    ) -> dict[str, Any]:
        confirmation = (
            confirmation_response.get("transition_confirmation") or {}
        )

        if not confirmation.get("available", False):
            return {
                "engine": "QMI Technical Decision Synthesis Engine",
                "engine_id": "DE-TA-015.0",
                "version": "0.1.1",
                "status": "insufficient_history",
                "technical_decision_synthesis": {
                    "available": False,
                    "final_posture": "WAIT",
                    "reason": confirmation.get(
                        "reason",
                        "Insufficient transition-confirmation history.",
                    ),
                    "scope": self._scope(),
                },
            }

        decision = str(
            confirmation.get("decision") or "WATCH"
        ).upper()

        confirmation_score = self._number(
            confirmation.get("confirmation_score"),
            0.0,
        )

        current_state = str(
            confirmation.get("current_state") or "UNKNOWN"
        ).upper()

        target_state = str(
            confirmation.get("target_state") or current_state
        ).upper()

        blockers = (
            confirmation.get("blockers")
            if isinstance(confirmation.get("blockers"), list)
            else []
        )

        source_context = confirmation.get("source_context") or {}
        state_change = confirmation.get("state_change") or {}
        action_permissions = source_context.get("action_permissions") or {}

        risk_state = str(
            source_context.get("risk_state") or "UNKNOWN"
        ).upper()

        execution_state = str(
            source_context.get("execution_state") or "UNKNOWN"
        ).upper()

        maturity_phase = str(
            source_context.get("maturity_phase") or "EARLY"
        ).upper()

        transition_probability = self._number(
            source_context.get("transition_probability"),
            state_change.get("transition_probability"),
        )

        transition_readiness = self._number(
            source_context.get("transition_readiness"),
            state_change.get("transition_readiness"),
        )

        persistence_score = self._number(
            source_context.get("persistence_score"),
            0.0,
        )

        stability_score = self._number(
            source_context.get("stability_score"),
            0.0,
        )

        execution_confidence = self._number(
            source_context.get("execution_confidence"),
            0.0,
        )

        primary_scenario = (
            source_context.get("primary_scenario") or "--"
        )

        direction_score = self._number(
            source_context.get("direction_score"),
            0.0,
        )

        posture = self._final_posture(
            confirmation_decision=decision,
            confirmation_score=confirmation_score,
            risk_state=risk_state,
            execution_state=execution_state,
            action_permissions=action_permissions,
            blockers=blockers,
            current_state=current_state,
            target_state=target_state,
        )

        conviction = self._conviction(
            posture=posture,
            confirmation_score=confirmation_score,
            transition_probability=transition_probability,
            transition_readiness=transition_readiness,
            persistence_score=persistence_score,
            stability_score=stability_score,
            execution_confidence=execution_confidence,
            blockers=blockers,
        )

        timing = self._timing(
            confirmation_decision=decision,
            maturity_phase=maturity_phase,
            transition_probability=transition_probability,
            transition_readiness=transition_readiness,
        )

        rationale = self._rationale(
            posture=posture,
            confirmation_decision=decision,
            risk_state=risk_state,
            execution_state=execution_state,
            current_state=current_state,
            target_state=target_state,
            primary_scenario=primary_scenario,
            blockers=blockers,
        )

        return {
            "engine": "QMI Technical Decision Synthesis Engine",
            "engine_id": "DE-TA-015.0",
            "version": "0.1.1",
            "status": "operational",
            "technical_decision_synthesis": {
                "available": True,
                "final_posture": posture,
                "conviction": round(conviction, 1),
                "timing": timing,
                "risk_state": risk_state,
                "execution_state": execution_state,
                "transition": {
                    "decision": decision,
                    "current_state": current_state,
                    "target_state": target_state,
                    "confirmation_score": round(
                        confirmation_score, 1
                    ),
                    "probability": round(
                        transition_probability, 1
                    ),
                    "readiness": round(
                        transition_readiness, 1
                    ),
                    "maturity_phase": maturity_phase,
                    "persistence_score": round(
                        persistence_score, 1
                    ),
                    "stability_score": round(
                        stability_score, 1
                    ),
                },
                "market_context": {
                    "primary_scenario": primary_scenario,
                    "direction_score": round(
                        direction_score, 1
                    ),
                    "execution_confidence": round(
                        execution_confidence, 1
                    ),
                },
                "rationale": rationale,
                "blockers": blockers,
                "decision_trace": {
                    "final_posture": posture,
                    "confirmation_decision": decision,
                    "action_permissions": {
                        key: str(
                            action_permissions.get(key) or "UNKNOWN"
                        ).upper()
                        for key in (
                            "WAIT",
                            "ENTER",
                            "ADD",
                            "REDUCE",
                            "EXIT",
                        )
                    },
                    "blocker_count": len(blockers),
                    "gate_preservation": True,
                    "execution_recomputed": False,
                },
                "scope": self._scope(),
            },
        }

    def _final_posture(
        self,
        *,
        confirmation_decision: str,
        confirmation_score: float,
        risk_state: str,
        execution_state: str,
        action_permissions: dict[str, Any],
        blockers: list[Any],
        current_state: str,
        target_state: str,
    ) -> str:
        wait_state = self._permission(action_permissions, "WAIT")
        enter_state = self._permission(action_permissions, "ENTER")
        add_state = self._permission(action_permissions, "ADD")
        reduce_state = self._permission(action_permissions, "REDUCE")
        exit_state = self._permission(action_permissions, "EXIT")

        severe_risk = risk_state in {"CRITICAL", "EXTREME"}

        if exit_state in {"REQUIRED", "TRIGGERED", "ACTIVE"}:
            return "EXIT"

        if (
            reduce_state in {"REQUIRED", "TRIGGERED"}
            or (
                severe_risk
                and reduce_state in {"PERMITTED", "PREFERRED", "ACTIVE"}
            )
        ):
            return "REDUCE"

        if confirmation_decision == "BLOCKED":
            return "WAIT"

        if confirmation_decision == "HOLD_STATE":
            if execution_state in {
                "ENTRY_ACTIVE",
                "LONG_ACTIVE",
                "CONSTRUCTIVE",
            }:
                return "WATCH"
            return "WAIT"

        if confirmation_decision == "WATCH":
            return "WATCH"

        if confirmation_decision == "PRECONFIRMED":
            return "PREPARE"

        if confirmation_decision == "CONFIRMED":
            if enter_state in {
                "PERMITTED",
                "READY",
                "ACTIVE",
                "ELIGIBLE",
                "PREFERRED",
            }:
                return "ENTER"

            if add_state in {
                "PERMITTED",
                "READY",
                "ACTIVE",
                "ELIGIBLE",
                "PREFERRED",
            }:
                return "ADD"

            return "PREPARE"

        if wait_state in {"PREFERRED", "ACTIVE", "REQUIRED", "PRIMARY"}:
            return "WAIT"

        if target_state != current_state and confirmation_score >= 50:
            return "WATCH"

        return "WAIT"

    def _conviction(
        self,
        *,
        posture: str,
        confirmation_score: float,
        transition_probability: float,
        transition_readiness: float,
        persistence_score: float,
        stability_score: float,
        execution_confidence: float,
        blockers: list[Any],
    ) -> float:
        score = (
            confirmation_score * 0.35
            + transition_probability * 0.15
            + transition_readiness * 0.15
            + persistence_score * 0.10
            + stability_score * 0.10
            + execution_confidence * 0.15
        )

        if posture in {"WAIT", "REDUCE", "EXIT"} and blockers:
            score = max(
                score,
                min(92.0, 55.0 + len(blockers) * 5.0),
            )

        return max(0.0, min(100.0, score))

    def _timing(
        self,
        *,
        confirmation_decision: str,
        maturity_phase: str,
        transition_probability: float,
        transition_readiness: float,
    ) -> str:
        if confirmation_decision == "CONFIRMED":
            return "ACTIONABLE"

        if confirmation_decision == "PRECONFIRMED":
            return "NEAR_TERM"

        if confirmation_decision == "BLOCKED":
            return "BLOCKED"

        if maturity_phase in {"EARLY", "DEVELOPING"}:
            return "EARLY"

        if (
            transition_probability >= 60
            and transition_readiness >= 65
        ):
            return "DEVELOPING"

        return "MONITOR"

    def _rationale(
        self,
        *,
        posture: str,
        confirmation_decision: str,
        risk_state: str,
        execution_state: str,
        current_state: str,
        target_state: str,
        primary_scenario: Any,
        blockers: list[Any],
    ) -> str:
        scenario = str(primary_scenario or "--").replace("_", " ")

        if posture == "EXIT":
            return (
                "Technical exit conditions are active. Capital protection "
                "has priority over transition signals."
            )

        if posture == "REDUCE":
            return (
                "Technical risk remains elevated and reduction is permitted "
                "or required by the execution layer."
            )

        if posture == "ENTER":
            return (
                f"Transition from {current_state} to {target_state} is "
                "confirmed and the execution layer permits new exposure."
            )

        if posture == "ADD":
            return (
                f"Transition toward {target_state} is confirmed and the "
                "execution layer permits incremental exposure."
            )

        if posture == "PREPARE":
            return (
                f"Transition toward {target_state} is preconfirmed, but "
                "execution gates are not yet sufficient for entry."
            )

        if posture == "WATCH":
            return (
                f"QMI is monitoring a possible transition from "
                f"{current_state} to {target_state}. Confirmation remains "
                f"{confirmation_decision}; primary scenario: {scenario}."
            )

        blocker_note = (
            f" {len(blockers)} active blocker(s) remain."
            if blockers
            else ""
        )

        return (
            f"Maintain defensive technical posture. Risk is {risk_state}, "
            f"execution state is {execution_state}, and transition "
            f"confirmation is {confirmation_decision}.{blocker_note}"
        )

    @staticmethod
    def _permission(
        action_permissions: dict[str, Any],
        action_name: str,
    ) -> str:
        return str(
            action_permissions.get(action_name) or "UNKNOWN"
        ).upper()

    @staticmethod
    def _scope() -> dict[str, Any]:
        return {
            "technical_only": True,
            "portfolio_allocation": False,
            "persistent_state_mutation": False,
            "automatic_execution": False,
            "buy_hold_sell_signal": False,
            "note": (
                "DE-TA-015.0 synthesizes the technical pipeline into a "
                "final posture. It does not execute trades or override "
                "portfolio-level risk constraints."
            ),
        }

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
