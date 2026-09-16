from __future__ import annotations

from typing import Any


class DecisionCalibrationService:
    """DE-DI-009 — Adaptive Decision Calibration.

    Produces evidence-based calibration observations from historical reliability
    and outcome measurements. Version 0.1 is advisory only: it NEVER changes
    Confluence weights or execution permissions automatically.
    """

    ENGINE_ID = "DE-DI-009"
    VERSION = "0.1.0"
    MIN_SEGMENT_SAMPLE = 5
    HIGH_EDGE = 70.0
    LOW_EDGE = 50.0

    def analyze(
        self,
        *,
        reliability_breakdown: dict[str, Any] | None,
        decision_outcome: dict[str, Any] | None,
    ) -> dict[str, Any]:
        rb = (reliability_breakdown or {}).get("reliability_breakdown") or {}
        oc = (decision_outcome or {}).get("decision_outcome") or {}

        segments = []
        for item in (rb.get("by_direction") or []) + (rb.get("by_strength") or []):
            n = int(item.get("evaluations") or 0)
            rate = self._num(item.get("hit_rate_pct"))
            if n >= self.MIN_SEGMENT_SAMPLE and rate is not None:
                segments.append({
                    "type": "RELIABILITY_SEGMENT",
                    "name": item.get("segment"),
                    "sample_size": n,
                    "score": rate,
                    "signal": self._signal(rate),
                })

        postures = []
        for item in oc.get("by_posture") or []:
            n = int(item.get("evaluations") or 0)
            rate = self._num(item.get("success_rate_pct"))
            if n >= self.MIN_SEGMENT_SAMPLE and rate is not None:
                postures.append({
                    "type": "DECISION_POSTURE",
                    "name": item.get("posture"),
                    "sample_size": n,
                    "score": rate,
                    "average_outcome_pct": self._num(item.get("average_outcome_pct")),
                    "signal": self._signal(rate),
                })

        evidence = segments + postures
        positive = sorted(
            [x for x in evidence if x["signal"] == "POSITIVE_EDGE"],
            key=lambda x: (x["score"], x["sample_size"]),
            reverse=True,
        )
        weak = sorted(
            [x for x in evidence if x["signal"] == "WEAK_EDGE"],
            key=lambda x: (x["score"], -x["sample_size"]),
        )

        readiness = self._readiness(evidence)
        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_calibration": {
                "available": bool(evidence),
                "readiness": readiness,
                "qualified_evidence_count": len(evidence),
                "minimum_segment_sample": self.MIN_SEGMENT_SAMPLE,
                "positive_edges": positive[:5],
                "weak_edges": weak[:5],
                "strongest_evidence": positive[0] if positive else None,
                "weakest_evidence": weak[0] if weak else None,
                "recommendation": self._recommendation(readiness, positive, weak),
                "guardrails": {
                    "automatic_weight_changes": False,
                    "automatic_threshold_changes": False,
                    "automatic_execution_changes": False,
                    "human_review_required": True,
                    "purpose": "diagnostic_calibration_only",
                },
            },
        }

    def _readiness(self, evidence):
        if not evidence:
            return "INSUFFICIENT_HISTORY"
        total_samples = sum(x["sample_size"] for x in evidence)
        if len(evidence) >= 4 and total_samples >= 40:
            return "MATURE"
        if len(evidence) >= 2 and total_samples >= 15:
            return "DEVELOPING"
        return "EARLY"

    def _signal(self, score):
        if score >= self.HIGH_EDGE:
            return "POSITIVE_EDGE"
        if score < self.LOW_EDGE:
            return "WEAK_EDGE"
        return "NEUTRAL"

    @staticmethod
    def _recommendation(readiness, positive, weak):
        if readiness == "INSUFFICIENT_HISTORY":
            return "Collect more completed observations before considering calibration."
        if readiness == "EARLY":
            return "Evidence is early. Observe only; do not alter engine weights."
        if weak and positive:
            return "Review weak and positive segments before any manual calibration proposal."
        if weak:
            return "Review weak segments for possible future manual calibration."
        if positive:
            return "Positive edges are emerging; preserve current settings until evidence matures."
        return "No material calibration edge is currently detected."

    @staticmethod
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None
