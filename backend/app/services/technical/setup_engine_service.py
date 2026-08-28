from __future__ import annotations
from typing import Any


class TechnicalSetupEngineService:
    """DE-TA-016.0 — Technical Opportunity / Setup Qualification Engine."""

    VALID_PERMISSIONS = {"PERMITTED", "READY", "ACTIVE", "ELIGIBLE", "PREFERRED"}

    def analyze(self, *, synthesis_response: dict[str, Any]) -> dict[str, Any]:
        synthesis = synthesis_response.get("technical_decision_synthesis") or {}

        if not synthesis.get("available", False):
            return self._unavailable(synthesis)

        posture = str(synthesis.get("final_posture") or "WAIT").upper()
        conviction = self._number(synthesis.get("conviction"))
        timing = str(synthesis.get("timing") or "MONITOR").upper()
        risk_state = str(synthesis.get("risk_state") or "UNKNOWN").upper()
        execution_state = str(synthesis.get("execution_state") or "UNKNOWN").upper()

        transition = synthesis.get("transition") or {}
        market = synthesis.get("market_context") or {}
        trace = synthesis.get("decision_trace") or {}
        permissions = trace.get("action_permissions") or {}
        blockers = synthesis.get("blockers") if isinstance(synthesis.get("blockers"), list) else []

        confirmation = str(transition.get("decision") or "WATCH").upper()
        confirmation_score = self._number(transition.get("confirmation_score"))
        probability = self._number(transition.get("probability"))
        readiness = self._number(transition.get("readiness"))
        persistence = self._number(transition.get("persistence_score"))
        stability = self._number(transition.get("stability_score"))
        maturity = str(transition.get("maturity_phase") or "EARLY").upper()
        direction_score = self._number(market.get("direction_score"))
        execution_confidence = self._number(market.get("execution_confidence"))

        enter = self._permission(permissions, "ENTER")
        add = self._permission(permissions, "ADD")
        reduce = self._permission(permissions, "REDUCE")
        exit_ = self._permission(permissions, "EXIT")

        direction = self._direction(posture, direction_score, enter, add, reduce, exit_)
        setup_type = self._setup_type(
            direction,
            str(market.get("primary_scenario") or "--"),
            str(transition.get("current_state") or "UNKNOWN").upper(),
            str(transition.get("target_state") or "UNKNOWN").upper(),
        )

        phase_score = {
            "EARLY": 35.0, "DEVELOPING": 55.0, "MATURE": 75.0,
            "LATE": 60.0, "EXHAUSTED": 30.0,
        }.get(maturity, 40.0)
        structure = persistence * 0.40 + stability * 0.35 + phase_score * 0.25

        quality = max(0.0, min(100.0,
            structure * 0.25 + readiness * 0.25 + confirmation_score * 0.20
            + execution_confidence * 0.15 + conviction * 0.15
        ))

        hard_gate = self._hard_gate(
            posture, risk_state, confirmation, enter, add, direction
        )
        setup_status = self._status(
            quality, hard_gate, confirmation, probability, readiness, timing
        )

        reasons = []
        if not hard_gate:
            if risk_state in {"CRITICAL", "EXTREME"}:
                reasons.append(f"Risk state {risk_state} blocks setup validation.")
            if confirmation == "BLOCKED":
                reasons.append("Transition confirmation is BLOCKED.")
            if enter in {"BLOCKED", "PROHIBITED"}:
                reasons.append(f"ENTER gate is {enter}.")
            if posture == "ADD" and add in {"BLOCKED", "PROHIBITED"}:
                reasons.append(f"ADD gate is {add}.")
        if blockers:
            reasons.append(f"{len(blockers)} upstream blocker(s) remain active.")
        if not reasons and setup_status in {"VALID", "HIGH_CONVICTION"}:
            reasons.append("Upstream technical gates permit setup validation.")

        return {
            "engine": "QMI Technical Setup Engine",
            "engine_id": "DE-TA-016.0",
            "version": "0.1.0",
            "status": "operational",
            "technical_setup": {
                "available": True,
                "setup_status": setup_status,
                "setup_type": setup_type,
                "direction": direction,
                "setup_quality": round(quality, 1),
                "timing": timing,
                "qualification": {
                    "structure_readiness": round(structure, 1),
                    "transition_readiness": round(readiness, 1),
                    "confirmation": round(confirmation_score, 1),
                    "execution_confidence": round(execution_confidence, 1),
                    "decision_conviction": round(conviction, 1),
                },
                "context": {
                    "final_posture": posture,
                    "risk_state": risk_state,
                    "execution_state": execution_state,
                    "maturity_phase": maturity,
                    "primary_scenario": market.get("primary_scenario") or "--",
                    "direction_score": round(direction_score, 1),
                    "transition_probability": round(probability, 1),
                },
                "gates": {
                    "hard_gate_passed": hard_gate,
                    "confirmation": confirmation,
                    "ENTER": enter, "ADD": add, "REDUCE": reduce, "EXIT": exit_,
                    "gate_preservation": True,
                },
                "blockers": blockers,
                "gate_reasons": reasons,
                "price_plan": {
                    "available": False, "entry_zone": None, "trigger": None,
                    "invalidation": None, "target": None, "risk_reward": None,
                    "note": "Price-level planning is reserved for DE-TA-016.1.",
                },
                "scope": {
                    "technical_only": True,
                    "setup_qualification_only": True,
                    "price_levels": False,
                    "automatic_execution": False,
                    "portfolio_allocation": False,
                    "gate_preservation": True,
                },
            },
        }

    def _unavailable(self, synthesis):
        return {
            "engine": "QMI Technical Setup Engine", "engine_id": "DE-TA-016.0",
            "version": "0.1.0", "status": "insufficient_context",
            "technical_setup": {
                "available": False, "setup_status": "NO_SETUP",
                "setup_type": "NONE", "direction": "NEUTRAL",
                "setup_quality": 0.0, "timing": "BLOCKED",
                "reason": synthesis.get("reason", "Decision synthesis is not available."),
            },
        }

    def _hard_gate(self, posture, risk, confirmation, enter, add, direction):
        if risk in {"CRITICAL", "EXTREME"} or confirmation == "BLOCKED":
            return False
        if direction == "LONG":
            return (add if posture == "ADD" else enter) in self.VALID_PERMISSIONS
        if direction == "DEFENSIVE":
            return posture in {"REDUCE", "EXIT"}
        return False

    @staticmethod
    def _status(quality, hard_gate, confirmation, probability, readiness, timing):
        if not hard_gate:
            return "DEVELOPING" if max(quality, probability, readiness) >= 35 else "NO_SETUP"
        if quality >= 80 and confirmation == "CONFIRMED" and timing == "ACTIONABLE":
            return "HIGH_CONVICTION"
        if quality >= 60 and confirmation in {"CONFIRMED", "PRECONFIRMED"}:
            return "VALID"
        return "DEVELOPING" if quality >= 35 else "NO_SETUP"

    def _direction(self, posture, score, enter, add, reduce, exit_):
        if posture in {"REDUCE", "EXIT"}:
            return "DEFENSIVE"
        if posture in {"ENTER", "ADD", "PREPARE", "WATCH"}:
            if score > 10: return "LONG"
            if score < -10: return "BEARISH_WATCH"
        if enter in self.VALID_PERMISSIONS or add in self.VALID_PERMISSIONS:
            return "LONG"
        if reduce in {"REQUIRED", "TRIGGERED"} or exit_ in {"REQUIRED", "TRIGGERED"}:
            return "DEFENSIVE"
        return "NEUTRAL"

    @staticmethod
    def _setup_type(direction, scenario, current_state, target_state):
        scenario = scenario.upper()
        if direction == "DEFENSIVE": return "RISK_REDUCTION"
        if direction == "BEARISH_WATCH": return "BEARISH_CONTINUATION_WATCH"
        if direction != "LONG": return "NONE"
        if current_state != target_state: return "TRANSITION"
        if "REVERS" in scenario: return "REVERSAL"
        if "BREAK" in scenario: return "BREAKOUT"
        if "CONTINU" in scenario: return "CONTINUATION"
        return "LONG_SETUP"

    @staticmethod
    def _permission(permissions, name):
        return str(permissions.get(name) or "UNKNOWN").upper()

    @staticmethod
    def _number(value, default=0.0):
        try: return float(default if value is None else value)
        except (TypeError, ValueError): return float(default)
