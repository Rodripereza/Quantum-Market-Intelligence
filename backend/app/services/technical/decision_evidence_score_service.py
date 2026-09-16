from __future__ import annotations
from typing import Any


class DecisionEvidenceScoreService:
    """DE-DI-014 — Decision Evidence Score.

    Aggregates live confidence and historical validation into a 0..100 evidence
    score. Evaluator only: it never changes posture, weights, thresholds,
    permissions or execution.
    """

    ENGINE_ID = "DE-DI-014"
    VERSION = "0.1.0"

    def analyze(
        self,
        *,
        confidence_decomposition: dict[str, Any] | None,
        historical_edge: dict[str, Any] | None,
        evidence_alignment: dict[str, Any] | None,
    ) -> dict[str, Any]:
        confidence = (confidence_decomposition or {}).get("decision_confidence_decomposition") or {}
        edge = (historical_edge or {}).get("historical_edge") or {}
        alignment = (evidence_alignment or {}).get("decision_evidence_alignment") or {}

        live = self._live_components(confidence)
        live_values = [v for v in live.values() if v is not None]
        live_score = sum(live_values) / len(live_values) if live_values else None

        edge_score = self._num(edge.get("edge_score"))
        similarity = self._num(edge.get("average_similarity"))
        historical_quality = str(edge.get("evidence") or "INSUFFICIENT_HISTORY").upper()
        alignment_state = str(alignment.get("alignment") or "UNAVAILABLE").upper()
        alignment_confidence = self._num(alignment.get("alignment_confidence"))

        historical_available = edge_score is not None and bool(edge.get("available"))
        historical_support = self._historical_support(
            edge_score=edge_score,
            alignment_state=alignment_state,
            alignment_confidence=alignment_confidence,
            similarity=similarity,
            quality=historical_quality,
        ) if historical_available else None

        # Historical evidence only earns material weight as its maturity grows.
        historical_weight = {
            "MATURE": 0.35,
            "DEVELOPING": 0.25,
            "EARLY": 0.12,
        }.get(historical_quality, 0.0)

        if live_score is None and historical_support is None:
            return self._empty(live)

        if live_score is None:
            final = historical_support
            live_weight = 0.0
            historical_weight = 1.0
        elif historical_support is None or historical_weight <= 0:
            final = live_score
            live_weight = 1.0
            historical_weight = 0.0
        else:
            live_weight = 1.0 - historical_weight
            final = live_score * live_weight + historical_support * historical_weight

        final = max(0.0, min(100.0, float(final or 0.0)))
        quality = self._quality(final, historical_quality, historical_available)
        support = self._support_statement(final, alignment_state, historical_available)

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_evidence_score": {
                "available": True,
                "score": round(final, 1),
                "quality": quality,
                "support": support,
                "live_evidence": {
                    "score": round(live_score, 1) if live_score is not None else None,
                    "weight_pct": round(live_weight * 100.0, 1),
                    "components": live,
                },
                "historical_evidence": {
                    "available": historical_available,
                    "support_score": round(historical_support, 1) if historical_support is not None else None,
                    "weight_pct": round(historical_weight * 100.0, 1),
                    "edge_score": round(edge_score, 1) if edge_score is not None else None,
                    "similarity": round(similarity, 1) if similarity is not None else None,
                    "quality": historical_quality,
                },
                "alignment": {
                    "state": alignment_state,
                    "confidence": round(alignment_confidence, 1) if alignment_confidence is not None else None,
                },
                "scope": {
                    "evaluator_only": True,
                    "automatic_decision_changes": False,
                    "automatic_weight_changes": False,
                    "automatic_threshold_changes": False,
                    "automatic_execution_changes": False,
                },
            },
        }

    def _live_components(self, confidence):
        components = confidence.get("components") or {}
        return {
            "technical_agreement": self._component(components, "technical_agreement", confidence),
            "driver_consistency": self._component(components, "driver_consistency", confidence),
            "state_stability": self._component(components, "state_stability", confidence),
            "transition_certainty": self._component(components, "transition_certainty", confidence),
            "execution_confidence": self._component(components, "execution_confidence", confidence),
        }

    def _component(self, components, key, confidence):
        value = components.get(key)
        if isinstance(value, dict):
            value = value.get("score")
        number = self._num(value)
        if number is not None:
            return round(max(0.0, min(100.0, number)), 1)
        fallback = confidence.get(key)
        if isinstance(fallback, dict):
            fallback = fallback.get("score")
        number = self._num(fallback)
        return round(max(0.0, min(100.0, number)), 1) if number is not None else None

    def _historical_support(self, *, edge_score, alignment_state, alignment_confidence, similarity, quality):
        magnitude = min(100.0, abs(float(edge_score or 0.0)))
        align = max(0.0, min(100.0, float(alignment_confidence or 0.0)))
        sim = max(0.0, min(100.0, float(similarity or 0.0)))
        maturity = {"MATURE": 1.0, "DEVELOPING": 0.8, "EARLY": 0.55}.get(quality, 0.35)

        if alignment_state == "CONFIRMED":
            directional_support = 70.0 + magnitude * 0.30
        elif alignment_state == "CONFLICT":
            directional_support = max(0.0, 45.0 - magnitude * 0.35)
        else:
            directional_support = 50.0

        score = directional_support * 0.55 + align * 0.25 + sim * 0.20
        return max(0.0, min(100.0, score * maturity + 50.0 * (1.0 - maturity)))

    @staticmethod
    def _quality(score, historical_quality, historical_available):
        if score >= 80 and (not historical_available or historical_quality in {"DEVELOPING", "MATURE"}):
            return "STRONG"
        if score >= 65:
            return "GOOD"
        if score >= 50:
            return "MODERATE"
        return "WEAK"

    @staticmethod
    def _support_statement(score, alignment_state, historical_available):
        if not historical_available:
            return "Live evidence is available; historical evidence is not mature enough yet."
        if alignment_state == "CONFIRMED":
            return "Live and historical evidence support the current QMI decision."
        if alignment_state == "CONFLICT":
            return "Historical evidence conflicts with the current QMI decision; total evidence is reduced."
        return "Historical evidence is mixed relative to the current QMI decision."

    def _empty(self, live):
        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_evidence_score": {
                "available": False,
                "score": None,
                "quality": "INSUFFICIENT_EVIDENCE",
                "support": "Decision Evidence Score requires live confidence or historical evidence.",
                "live_evidence": {"score": None, "weight_pct": 0.0, "components": live},
                "historical_evidence": {"available": False, "support_score": None, "weight_pct": 0.0},
                "alignment": {"state": "UNAVAILABLE", "confidence": None},
                "scope": {"evaluator_only": True, "automatic_decision_changes": False},
            },
        }

    @staticmethod
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None
