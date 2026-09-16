from __future__ import annotations
from typing import Any


class DecisionEvidenceAlignmentService:
    """DE-DI-013 — Decision Evidence Alignment.

    Compares the live QMI decision posture/direction with DE-DI-012 historical
    edge. This is an advisory validation layer only and never changes posture,
    weights, thresholds, permissions or execution.
    """

    ENGINE_ID = "DE-DI-013"
    VERSION = "0.1.0"

    def analyze(
        self,
        *,
        decision_synthesis: dict[str, Any] | None,
        historical_edge: dict[str, Any] | None,
    ) -> dict[str, Any]:
        synthesis = decision_synthesis or {}
        edge = (historical_edge or {}).get("historical_edge") or {}

        posture = self._posture(synthesis)
        live_direction = self._live_direction(posture, synthesis)
        edge_score = self._num(edge.get("edge_score"))
        historical_direction = self._historical_direction(edge_score)

        if edge_score is None or historical_direction == "UNAVAILABLE":
            return self._empty(posture, live_direction)

        alignment = self._alignment(live_direction, historical_direction)
        strength = abs(edge_score)
        evidence = str(edge.get("evidence") or "INSUFFICIENT_HISTORY").upper()
        confidence = self._confidence(alignment, strength, evidence)

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_evidence_alignment": {
                "available": True,
                "live_posture": posture,
                "live_direction": live_direction,
                "historical_direction": historical_direction,
                "historical_edge_score": round(edge_score, 1),
                "alignment": alignment,
                "alignment_confidence": confidence,
                "historical_evidence": evidence,
                "message": self._message(posture, live_direction, historical_direction, alignment, evidence),
                "scope": {
                    "validation_only": True,
                    "automatic_decision_changes": False,
                    "automatic_weight_changes": False,
                    "automatic_threshold_changes": False,
                    "automatic_execution_changes": False,
                },
            },
        }

    @staticmethod
    def _posture(synthesis):
        candidates = [
            synthesis.get("final_posture"),
            synthesis.get("posture"),
            synthesis.get("decision"),
        ]
        nested = synthesis.get("decision_synthesis")
        if isinstance(nested, dict):
            candidates += [nested.get("final_posture"), nested.get("posture"), nested.get("decision")]
        for value in candidates:
            if value:
                return str(value).strip().upper()
        return "UNKNOWN"

    def _live_direction(self, posture, synthesis):
        if posture in {"ENTER", "ADD"}:
            return "BULLISH"
        if posture in {"REDUCE", "EXIT"}:
            return "BEARISH"
        # WAIT is neutral unless a strong live direction score is available.
        score = self._extract_direction_score(synthesis)
        if score is not None:
            if score >= 20:
                return "BULLISH"
            if score <= -20:
                return "BEARISH"
        return "NEUTRAL"

    def _extract_direction_score(self, value):
        if not isinstance(value, dict):
            return None
        for key in ("direction_score", "score"):
            number = self._num(value.get(key))
            if key == "direction_score" and number is not None:
                return number
        for key in ("decision_synthesis", "technical_decision", "decision"):
            nested = value.get(key)
            if isinstance(nested, dict):
                found = self._extract_direction_score(nested)
                if found is not None:
                    return found
        return None

    @staticmethod
    def _historical_direction(score):
        if score is None:
            return "UNAVAILABLE"
        if score >= 20:
            return "BULLISH"
        if score <= -20:
            return "BEARISH"
        return "NEUTRAL"

    @staticmethod
    def _alignment(live, historical):
        if live == "NEUTRAL" or historical == "NEUTRAL":
            return "MIXED"
        return "CONFIRMED" if live == historical else "CONFLICT"

    @staticmethod
    def _confidence(alignment, strength, evidence):
        evidence_factor = {"MATURE": 1.0, "DEVELOPING": 0.8, "EARLY": 0.55}.get(evidence, 0.35)
        raw = min(100.0, strength) * evidence_factor
        if alignment == "MIXED":
            raw *= 0.65
        return round(raw, 1)

    @staticmethod
    def _message(posture, live, historical, alignment, evidence):
        if alignment == "CONFIRMED":
            return f"Historical evidence confirms the live {posture} posture ({live}) with {evidence.lower()} evidence."
        if alignment == "CONFLICT":
            return f"Historical evidence conflicts with the live {posture} posture: live is {live}, history is {historical}."
        return f"Historical evidence is mixed relative to the live {posture} posture."

    def _empty(self, posture, live):
        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_evidence_alignment": {
                "available": False,
                "live_posture": posture,
                "live_direction": live,
                "historical_direction": "UNAVAILABLE",
                "historical_edge_score": None,
                "alignment": "UNAVAILABLE",
                "alignment_confidence": None,
                "historical_evidence": "INSUFFICIENT_HISTORY",
                "message": "Evidence Alignment activates when Historical Edge becomes available.",
                "scope": {"validation_only": True, "automatic_decision_changes": False},
            },
        }

    @staticmethod
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None
