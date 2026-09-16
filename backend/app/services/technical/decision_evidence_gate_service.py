from __future__ import annotations
from typing import Any


class DecisionEvidenceGateService:
    """DE-DI-015 — Decision Evidence Gate.

    Formal validation layer over the current QMI decision and DE-DI-014 evidence.
    It returns PASSED / CONDITIONAL / BLOCKED, but never changes the decision,
    permissions, weights, thresholds or execution.
    """

    ENGINE_ID = "DE-DI-015"
    VERSION = "0.1.0"

    PASS_SCORE = 75.0
    CONDITIONAL_SCORE = 55.0
    MIN_LIVE_SCORE = 60.0

    def analyze(
        self,
        *,
        decision_synthesis: dict[str, Any] | None,
        decision_evidence_score: dict[str, Any] | None,
        evidence_alignment: dict[str, Any] | None,
        historical_edge: dict[str, Any] | None,
    ) -> dict[str, Any]:
        synthesis = decision_synthesis or {}
        evidence = (decision_evidence_score or {}).get("decision_evidence_score") or {}
        alignment = (evidence_alignment or {}).get("decision_evidence_alignment") or {}
        edge = (historical_edge or {}).get("historical_edge") or {}

        posture = self._posture(synthesis)
        score = self._num(evidence.get("score"))
        live_score = self._num((evidence.get("live_evidence") or {}).get("score"))
        alignment_state = str(alignment.get("alignment") or "UNAVAILABLE").upper()
        historical_available = bool(edge.get("available"))
        historical_quality = str(edge.get("evidence") or "INSUFFICIENT_HISTORY").upper()
        historical_edge_score = self._num(edge.get("edge_score"))

        checks = [
            self._check(
                "decision_evidence",
                "Decision evidence sufficient",
                score is not None and score >= self.PASS_SCORE,
                score is not None and score >= self.CONDITIONAL_SCORE,
                f"Evidence Score {score:.1f}" if score is not None else "Evidence Score unavailable",
            ),
            self._check(
                "live_evidence",
                "Live evidence sufficient",
                live_score is not None and live_score >= self.MIN_LIVE_SCORE,
                live_score is not None and live_score >= 50.0,
                f"Live Evidence {live_score:.1f}" if live_score is not None else "Live Evidence unavailable",
            ),
            self._historical_check(
                historical_available=historical_available,
                alignment_state=alignment_state,
                historical_quality=historical_quality,
                edge_score=historical_edge_score,
            ),
            self._conflict_check(alignment_state, historical_available),
        ]

        hard_fail = any(x["state"] == "FAIL" and x["key"] in {"decision_evidence", "live_evidence", "evidence_conflict"} for x in checks)
        conditional = any(x["state"] in {"CONDITIONAL", "PENDING"} for x in checks)

        if score is None or live_score is None:
            gate = "BLOCKED"
        elif hard_fail:
            gate = "BLOCKED"
        elif score >= self.PASS_SCORE and live_score >= self.MIN_LIVE_SCORE and not conditional:
            gate = "PASSED"
        elif score >= self.CONDITIONAL_SCORE and live_score >= 50.0:
            gate = "CONDITIONAL"
        else:
            gate = "BLOCKED"

        strength = self._strength(gate, score, live_score, historical_quality)
        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_evidence_gate": {
                "available": score is not None and live_score is not None,
                "decision_posture": posture,
                "gate": gate,
                "validation_strength": strength,
                "evidence_score": round(score, 1) if score is not None else None,
                "live_evidence_score": round(live_score, 1) if live_score is not None else None,
                "historical_alignment": alignment_state,
                "historical_edge_score": round(historical_edge_score, 1) if historical_edge_score is not None else None,
                "historical_maturity": historical_quality,
                "checks": checks,
                "assessment": self._assessment(posture, gate, strength, alignment_state, historical_available),
                "scope": {
                    "validation_only": True,
                    "automatic_decision_changes": False,
                    "automatic_permission_changes": False,
                    "automatic_weight_changes": False,
                    "automatic_threshold_changes": False,
                    "automatic_execution_changes": False,
                },
            },
        }

    @staticmethod
    def _check(key, label, passed, conditional, detail):
        state = "PASS" if passed else "CONDITIONAL" if conditional else "FAIL"
        return {"key": key, "label": label, "state": state, "detail": detail}

    def _historical_check(self, *, historical_available, alignment_state, historical_quality, edge_score):
        if not historical_available:
            return {
                "key": "historical_support",
                "label": "Historical evidence supports decision",
                "state": "PENDING",
                "detail": "Historical evidence not mature enough yet",
            }
        if alignment_state == "CONFIRMED":
            return {
                "key": "historical_support",
                "label": "Historical evidence supports decision",
                "state": "PASS",
                "detail": f"{historical_quality.title()} evidence · Edge {edge_score:+.1f}" if edge_score is not None else historical_quality.title(),
            }
        if alignment_state == "CONFLICT":
            return {
                "key": "historical_support",
                "label": "Historical evidence supports decision",
                "state": "FAIL",
                "detail": "Historical evidence conflicts with live decision",
            }
        return {
            "key": "historical_support",
            "label": "Historical evidence supports decision",
            "state": "CONDITIONAL",
            "detail": "Historical evidence is mixed",
        }

    @staticmethod
    def _conflict_check(alignment_state, historical_available):
        if not historical_available:
            return {
                "key": "evidence_conflict",
                "label": "No major evidence conflict",
                "state": "PENDING",
                "detail": "Awaiting qualified historical evidence",
            }
        if alignment_state == "CONFLICT":
            return {
                "key": "evidence_conflict",
                "label": "No major evidence conflict",
                "state": "FAIL",
                "detail": "Live and historical evidence disagree",
            }
        return {
            "key": "evidence_conflict",
            "label": "No major evidence conflict",
            "state": "PASS",
            "detail": "No material live/history conflict detected",
        }

    @staticmethod
    def _strength(gate, score, live_score, historical_quality):
        if gate == "BLOCKED":
            return "INSUFFICIENT"
        if gate == "PASSED" and score is not None and score >= 85 and live_score is not None and live_score >= 75:
            return "VERY_STRONG" if historical_quality == "MATURE" else "STRONG"
        if gate == "PASSED":
            return "STRONG"
        return "DEVELOPING"

    @staticmethod
    def _assessment(posture, gate, strength, alignment_state, historical_available):
        pretty_posture = posture.title()
        if gate == "PASSED":
            return f"Current {pretty_posture} decision is validated with {strength.replace('_', ' ').lower()} evidence."
        if gate == "CONDITIONAL":
            suffix = " Historical evidence is still developing." if not historical_available else ""
            return f"Current {pretty_posture} decision has usable evidence but remains conditionally validated.{suffix}"
        if alignment_state == "CONFLICT":
            return f"Current {pretty_posture} decision is not validated because live and historical evidence conflict."
        return f"Current {pretty_posture} decision does not yet have sufficient evidence to pass the validation gate."

    @staticmethod
    def _posture(synthesis):
        candidates = [synthesis.get("final_posture"), synthesis.get("posture"), synthesis.get("decision")]
        nested = synthesis.get("decision_synthesis")
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
