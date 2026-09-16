from __future__ import annotations
from typing import Any


class DecisionIntelligenceQualityControlService:
    """DE-DI-020 — Decision Intelligence Quality Control.

    Final integrity/governance layer for Decision Intelligence v1.0.
    It verifies cross-engine availability and detects impossible or materially
    inconsistent states. It never modifies live decisions or execution.
    """

    ENGINE_ID = "DE-DI-020"
    VERSION = "0.1.0"

    def analyze(
        self,
        *,
        decision_synthesis: dict[str, Any] | None,
        execution_plan: dict[str, Any] | None,
        evidence_score: dict[str, Any] | None,
        evidence_gate: dict[str, Any] | None,
        validation_state: dict[str, Any] | None,
        validation_momentum: dict[str, Any] | None,
        contradiction_guard: dict[str, Any] | None,
        shadow_adaptive_decision: dict[str, Any] | None,
    ) -> dict[str, Any]:
        synthesis = decision_synthesis or {}
        execution = execution_plan or {}
        evidence = (evidence_score or {}).get("decision_evidence_score") or {}
        gate = (evidence_gate or {}).get("decision_evidence_gate") or {}
        validation = (validation_state or {}).get("decision_validation_state") or {}
        momentum = (validation_momentum or {}).get("decision_validation_momentum") or {}
        guard = (contradiction_guard or {}).get("decision_contradiction_guard") or {}
        shadow = (shadow_adaptive_decision or {}).get("shadow_adaptive_decision") or {}

        posture = self._posture(synthesis)
        checks: list[dict[str, Any]] = []

        # Availability / integrity checks.
        checks.append(self._check("DECISION_AVAILABLE", "Decision available", posture != "UNKNOWN",
                                  f"Live posture: {posture.title()}" if posture != "UNKNOWN" else "Live posture unavailable"))
        checks.append(self._check("EXECUTION_AVAILABLE", "Execution plan available", bool(execution),
                                  "Execution plan received" if execution else "Execution plan unavailable"))
        checks.append(self._check("EVIDENCE_AVAILABLE", "Evidence score available", self._num(evidence.get("score")) is not None,
                                  self._score_detail("Evidence", evidence.get("score"))))
        checks.append(self._check("GATE_AVAILABLE", "Evidence gate available", bool(gate.get("gate")),
                                  f"Gate: {str(gate.get('gate') or 'Unavailable').title()}"))
        checks.append(self._check("VALIDATION_AVAILABLE", "Validation state available", bool(validation.get("validation_state")),
                                  f"Validation: {str(validation.get('validation_state') or 'Unavailable').replace('_',' ').title()}"))
        checks.append(self._check("GUARD_AVAILABLE", "Contradiction guard available", bool(guard.get("guard_state")),
                                  f"Guard: {str(guard.get('guard_state') or 'Unavailable').replace('_',' ').title()}"))
        checks.append(self._check("SHADOW_AVAILABLE", "Shadow engine available", bool(shadow),
                                  "Shadow result received" if shadow else "Shadow result unavailable"))

        # Logical consistency checks.
        gate_state = str(gate.get("gate") or "").upper()
        validation_name = str(validation.get("validation_state") or "").upper()
        guard_state = str(guard.get("guard_state") or "").upper()
        live_shadow = str(shadow.get("live_posture") or "").upper()
        shadow_posture = str(shadow.get("shadow_posture") or "").upper()
        adaptive_eligible = bool(shadow.get("adaptive_eligible"))

        gate_validation_ok = not (
            (gate_state == "BLOCKED" and validation_name in {"VALIDATED", "STRONGLY_VALIDATED"})
            or (gate_state == "PASSED" and validation_name == "UNVALIDATED")
        )
        checks.append(self._check(
            "GATE_VALIDATION_COHERENCE", "Gate and validation state coherent", gate_validation_ok,
            f"{gate_state or 'Unavailable'} → {validation_name or 'Unavailable'}"
        ))

        shadow_live_ok = not live_shadow or live_shadow == posture
        checks.append(self._check(
            "SHADOW_LIVE_COHERENCE", "Shadow references current live decision", shadow_live_ok,
            f"Decision {posture.title()} · Shadow live {(live_shadow or 'Unavailable').title()}"
        ))

        guard_shadow_ok = not (
            guard_state in {"HARD_CONFLICT", "CONFLICT_REVIEW"} and adaptive_eligible
        )
        checks.append(self._check(
            "GUARD_SHADOW_COHERENCE", "Guard correctly controls shadow eligibility", guard_shadow_ok,
            f"Guard {guard_state.replace('_',' ').title() or 'Unavailable'} · Eligible {'Yes' if adaptive_eligible else 'No'}"
        ))

        # Shadow is simulation-only. A changed shadow posture is valid; changing
        # the live posture is not.
        scope = shadow.get("scope") if isinstance(shadow.get("scope"), dict) else {}
        shadow_isolation_ok = bool(scope.get("shadow_only")) and bool(scope.get("live_decision_unchanged"))
        checks.append(self._check(
            "SHADOW_ISOLATION", "Shadow remains isolated from production decision", shadow_isolation_ok,
            f"Live {posture.title()} · Shadow {(shadow_posture or posture).title()}"
        ))

        failures = [c for c in checks if c["state"] == "FAIL"]
        critical_codes = {"DECISION_AVAILABLE", "GATE_VALIDATION_COHERENCE", "SHADOW_LIVE_COHERENCE",
                          "GUARD_SHADOW_COHERENCE", "SHADOW_ISOLATION"}
        critical_failures = [c for c in failures if c["code"] in critical_codes]

        total = len(checks)
        passed = total - len(failures)
        quality_score = round((passed / total) * 100.0, 1) if total else 0.0

        if critical_failures:
            state = "FAILED"
        elif failures:
            state = "DEGRADED"
        elif quality_score >= 100.0:
            state = "READY"
        else:
            state = "OPERATIONAL"

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_intelligence_quality_control": {
                "available": True,
                "release_target": "Decision Intelligence v1.0",
                "quality_state": state,
                "quality_score": quality_score,
                "checks_passed": passed,
                "checks_total": total,
                "failure_count": len(failures),
                "critical_failure_count": len(critical_failures),
                "checks": checks,
                "assessment": self._assessment(state, passed, total),
                "scope": {
                    "quality_control_only": True,
                    "automatic_decision_changes": False,
                    "automatic_permission_changes": False,
                    "automatic_execution_changes": False,
                },
            },
        }

    @staticmethod
    def _check(code: str, label: str, passed: bool, detail: str) -> dict[str, Any]:
        return {"code": code, "label": label, "state": "PASS" if passed else "FAIL", "detail": detail}

    @staticmethod
    def _score_detail(label: str, value: Any) -> str:
        try:
            return f"{label}: {float(value):.1f}"
        except (TypeError, ValueError):
            return f"{label}: unavailable"

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
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _assessment(state: str, passed: int, total: int) -> str:
        if state == "READY":
            return f"Decision Intelligence passed all {total} quality-control checks."
        if state == "DEGRADED":
            return f"Decision Intelligence passed {passed}/{total} checks; non-critical integration gaps remain."
        if state == "FAILED":
            return f"Decision Intelligence passed {passed}/{total} checks; at least one critical coherence rule failed."
        return f"Decision Intelligence is operational with {passed}/{total} checks passed."
