from __future__ import annotations
from typing import Any


class DecisionContradictionGuardService:
    """DE-DI-018 — Contradiction Guard.

    Detects material disagreement between the live decision and QMI's evidence
    layers. Governance only: it never changes decisions or execution.
    """

    ENGINE_ID = "DE-DI-018"
    VERSION = "0.1.0"

    def analyze(
        self,
        *,
        decision_synthesis: dict[str, Any] | None,
        execution_plan: dict[str, Any] | None,
        evidence_alignment: dict[str, Any] | None,
        evidence_gate: dict[str, Any] | None,
        validation_state: dict[str, Any] | None,
        validation_momentum: dict[str, Any] | None,
    ) -> dict[str, Any]:
        synthesis = decision_synthesis or {}
        execution = execution_plan or {}
        alignment = (evidence_alignment or {}).get("decision_evidence_alignment") or {}
        gate = (evidence_gate or {}).get("decision_evidence_gate") or {}
        validation = (validation_state or {}).get("decision_validation_state") or {}
        momentum = (validation_momentum or {}).get("decision_validation_momentum") or {}

        posture = self._posture(synthesis)
        direction = self._direction(posture)
        contradictions: list[dict[str, Any]] = []

        alignment_state = str(alignment.get("alignment") or "UNAVAILABLE").upper()
        if alignment_state == "CONFLICT":
            contradictions.append(self._item(
                "HISTORICAL_ALIGNMENT_CONFLICT", "HIGH",
                "Historical evidence conflicts with the live decision.",
                "Historical Alignment",
            ))

        gate_state = str(gate.get("gate") or "BLOCKED").upper()
        if gate_state == "BLOCKED":
            contradictions.append(self._item(
                "EVIDENCE_GATE_BLOCKED", "HIGH",
                "The current decision does not pass the formal evidence gate.",
                "Decision Evidence Gate",
            ))
        elif gate_state == "CONDITIONAL":
            contradictions.append(self._item(
                "EVIDENCE_GATE_CONDITIONAL", "MEDIUM",
                "The current decision is only conditionally validated.",
                "Decision Evidence Gate",
            ))

        validation_name = str(validation.get("validation_state") or "UNVALIDATED").upper()
        if validation_name == "UNVALIDATED":
            contradictions.append(self._item(
                "DECISION_UNVALIDATED", "HIGH",
                "The persisted validation state does not validate the live decision.",
                "Decision Validation State",
            ))
        elif validation_name == "CONDITIONAL":
            contradictions.append(self._item(
                "DECISION_CONDITIONAL", "MEDIUM",
                "Persisted validation remains conditional.",
                "Decision Validation State",
            ))

        momentum_state = str(momentum.get("state") or "INSUFFICIENT_HISTORY").upper()
        if momentum_state == "DETERIORATING":
            contradictions.append(self._item(
                "VALIDATION_DETERIORATING", "HIGH",
                "Validation evidence is deteriorating with negative momentum.",
                "Validation Momentum",
            ))
        elif momentum_state == "WEAKENING":
            contradictions.append(self._item(
                "VALIDATION_WEAKENING", "MEDIUM",
                "Validation evidence is weakening.",
                "Validation Momentum",
            ))

        execution_state = self._execution_state(execution)
        if direction == "BULLISH" and any(
            token in execution_state
            for token in ("BLOCK", "DEFENSIVE", "WATCH_ONLY", "WAIT_DEFENSIVE")
        ):
            contradictions.append(self._item(
                "EXECUTION_DIRECTION_CONFLICT", "HIGH",
                "Bullish decision direction conflicts with defensive or blocked execution.",
                "Execution Plan",
            ))

        high = sum(item["severity"] == "HIGH" for item in contradictions)
        medium = sum(item["severity"] == "MEDIUM" for item in contradictions)
        low = sum(item["severity"] == "LOW" for item in contradictions)
        penalty = min(100.0, high * 35.0 + medium * 15.0 + low * 5.0)
        coherence = max(0.0, 100.0 - penalty)

        if high >= 2 or coherence < 40.0:
            guard_state = "HARD_CONFLICT"
        elif high >= 1:
            guard_state = "CONFLICT_REVIEW"
        elif medium >= 1:
            guard_state = "WATCH"
        else:
            guard_state = "CLEAR"

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_contradiction_guard": {
                "available": True,
                "decision_posture": posture,
                "decision_direction": direction,
                "guard_state": guard_state,
                "coherence_score": round(coherence, 1),
                "contradiction_count": len(contradictions),
                "high_severity_count": high,
                "medium_severity_count": medium,
                "contradictions": contradictions,
                "assessment": self._assessment(posture, guard_state, len(contradictions)),
                "scope": {
                    "governance_only": True,
                    "automatic_decision_changes": False,
                    "automatic_permission_changes": False,
                    "automatic_execution_changes": False,
                },
            },
        }

    @staticmethod
    def _item(code: str, severity: str, message: str, source: str) -> dict[str, str]:
        return {"code": code, "severity": severity, "message": message, "source": source}

    @staticmethod
    def _posture(payload: dict[str, Any]) -> str:
        candidates = [payload.get("final_posture"), payload.get("posture"), payload.get("decision")]
        nested = payload.get("decision_synthesis")
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
    def _execution_state(payload: dict[str, Any]) -> str:
        core = payload.get("technical_execution_plan") if isinstance(payload, dict) else {}
        if not isinstance(core, dict):
            core = {}
        values = [
            core.get("execution_state"),
            core.get("direction"),
            core.get("price_authorization"),
            payload.get("execution_state") if isinstance(payload, dict) else None,
        ]
        return " ".join(str(v).upper().replace(" ", "_") for v in values if v)

    @staticmethod
    def _assessment(posture: str, guard_state: str, count: int) -> str:
        p = posture.title()
        if guard_state == "CLEAR":
            return f"No material contradictions detected around the current {p} decision."
        if guard_state == "WATCH":
            return f"{p} has {count} non-critical evidence inconsistency/inconsistencies under observation."
        if guard_state == "CONFLICT_REVIEW":
            return f"{p} contains a material contradiction and requires review before future adaptive influence."
        return f"{p} contains multiple or severe contradictions; adaptive influence must remain disabled."
