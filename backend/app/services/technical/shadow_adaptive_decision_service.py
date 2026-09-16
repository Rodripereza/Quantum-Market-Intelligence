from __future__ import annotations
from typing import Any


class ShadowAdaptiveDecisionService:
    """DE-DI-019 — Shadow Adaptive Decision.

    Calculates what an adaptive historical overlay would suggest without
    changing the live QMI decision, permissions, thresholds or execution.
    """

    ENGINE_ID = "DE-DI-019"
    VERSION = "0.1.0"

    def analyze(
        self,
        *,
        decision_synthesis: dict[str, Any] | None,
        historical_edge: dict[str, Any] | None,
        evidence_score: dict[str, Any] | None,
        evidence_gate: dict[str, Any] | None,
        contradiction_guard: dict[str, Any] | None,
        validation_momentum: dict[str, Any] | None,
    ) -> dict[str, Any]:
        posture = self._posture(decision_synthesis or {})
        live_direction = self._direction(posture)
        edge = (historical_edge or {}).get("historical_edge") or {}
        evidence = (evidence_score or {}).get("decision_evidence_score") or {}
        gate = (evidence_gate or {}).get("decision_evidence_gate") or {}
        guard = (contradiction_guard or {}).get("decision_contradiction_guard") or {}
        momentum = (validation_momentum or {}).get("decision_validation_momentum") or {}

        edge_available = bool(edge.get("available"))
        edge_score = self._num(edge.get("edge_score"))
        evidence_value = self._num(evidence.get("score"))
        gate_state = str(gate.get("gate") or "BLOCKED").upper()
        guard_state = str(guard.get("guard_state") or "CLEAR").upper()
        momentum_state = str(momentum.get("state") or "INSUFFICIENT_HISTORY").upper()
        maturity = str(edge.get("evidence") or "INSUFFICIENT_HISTORY").upper()

        eligible = (
            edge_available
            and edge_score is not None
            and evidence_value is not None
            and gate_state in {"PASSED", "CONDITIONAL"}
            and guard_state in {"CLEAR", "WATCH"}
        )

        historical_direction = self._edge_direction(edge_score)
        shadow_posture = posture
        influence = "NONE"
        reason = "Historical evidence is not yet eligible for shadow influence."

        if eligible:
            if historical_direction == "BULLISH":
                if posture in {"REDUCE", "EXIT"}:
                    shadow_posture = "WAIT"
                    influence = "MODERATE"
                    reason = "Historical edge opposes the bearish live posture; shadow mode would soften it to WAIT."
                elif posture == "WAIT" and edge_score >= 50 and evidence_value >= 70:
                    shadow_posture = "ENTER"
                    influence = "MODERATE"
                    reason = "Strong bullish historical edge and sufficient evidence would promote WAIT to ENTER in shadow mode."
                else:
                    shadow_posture = posture
                    influence = "SUPPORTIVE"
                    reason = "Historical edge supports or does not materially alter the live posture."
            elif historical_direction == "BEARISH":
                if posture in {"ENTER", "ADD"}:
                    shadow_posture = "WAIT"
                    influence = "MODERATE"
                    reason = "Historical edge opposes the bullish live posture; shadow mode would soften it to WAIT."
                elif posture == "WAIT" and edge_score <= -50 and evidence_value >= 70:
                    shadow_posture = "REDUCE"
                    influence = "MODERATE"
                    reason = "Strong bearish historical edge and sufficient evidence would promote WAIT to REDUCE in shadow mode."
                else:
                    shadow_posture = posture
                    influence = "SUPPORTIVE"
                    reason = "Historical edge supports or does not materially alter the live posture."
            else:
                influence = "NEUTRAL"
                reason = "Historical edge is neutral; shadow mode preserves the live posture."

        if guard_state == "HARD_CONFLICT":
            eligible = False
            shadow_posture = posture
            influence = "DISABLED"
            reason = "Contradiction Guard reports HARD CONFLICT; adaptive influence is disabled."
        elif guard_state == "CONFLICT_REVIEW":
            eligible = False
            shadow_posture = posture
            influence = "DISABLED"
            reason = "Contradiction Guard requires review; adaptive influence is disabled."

        changed = shadow_posture != posture
        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "shadow_adaptive_decision": {
                "available": True,
                "adaptive_eligible": eligible,
                "live_posture": posture,
                "live_direction": live_direction,
                "shadow_posture": shadow_posture,
                "shadow_changed": changed,
                "historical_direction": historical_direction,
                "historical_edge_score": round(edge_score, 1) if edge_score is not None else None,
                "historical_maturity": maturity,
                "evidence_score": round(evidence_value, 1) if evidence_value is not None else None,
                "evidence_gate": gate_state,
                "contradiction_guard": guard_state,
                "validation_momentum": momentum_state,
                "influence": influence,
                "reason": reason,
                "assessment": self._assessment(posture, shadow_posture, eligible, changed),
                "scope": {
                    "shadow_only": True,
                    "live_decision_unchanged": True,
                    "automatic_decision_changes": False,
                    "automatic_permission_changes": False,
                    "automatic_weight_changes": False,
                    "automatic_threshold_changes": False,
                    "automatic_execution_changes": False,
                },
            },
        }

    @staticmethod
    def _posture(payload: dict[str, Any]) -> str:
        candidates = [payload.get("final_posture"), payload.get("posture"), payload.get("decision")]
        nested = payload.get("technical_decision_synthesis") or payload.get("decision_synthesis")
        if isinstance(nested, dict):
            candidates += [nested.get("final_posture"), nested.get("posture"), nested.get("decision")]
        for value in candidates:
            if value:
                return str(value).strip().upper()
        return "UNKNOWN"

    @staticmethod
    def _direction(posture: str) -> str:
        if posture in {"ENTER", "ADD"}:
            return "BULLISH"
        if posture in {"REDUCE", "EXIT"}:
            return "BEARISH"
        return "NEUTRAL"

    @staticmethod
    def _edge_direction(score: float | None) -> str:
        if score is None:
            return "UNAVAILABLE"
        if score >= 20:
            return "BULLISH"
        if score <= -20:
            return "BEARISH"
        return "NEUTRAL"

    @staticmethod
    def _assessment(live: str, shadow: str, eligible: bool, changed: bool) -> str:
        if not eligible:
            return f"Shadow mode preserves {live.title()}; adaptive historical influence is not currently eligible."
        if changed:
            return f"Live decision remains {live.title()}. Shadow adaptive analysis would test {shadow.title()} without changing production behavior."
        return f"Shadow adaptive analysis agrees with the current {live.title()} decision."

    @staticmethod
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None
