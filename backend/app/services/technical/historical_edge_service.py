from __future__ import annotations

from typing import Any


class HistoricalEdgeService:
    """DE-DI-012 — Historical Edge Engine.

    Converts DE-DI-011 historical outcome evidence into a normalized -100..+100
    contextual edge score. Advisory only: it does not change decisions, weights,
    thresholds, permissions or execution.
    """

    ENGINE_ID = "DE-DI-012"
    VERSION = "0.1.0"
    HORIZON_WEIGHTS = {"1D": 0.50, "5D": 0.30, "20D": 0.20}

    def analyze(self, *, historical_outcome_memory: dict[str, Any] | None) -> dict[str, Any]:
        outcome = (historical_outcome_memory or {}).get("historical_outcome_memory") or {}
        horizons = outcome.get("horizons") or []

        usable = []
        for row in horizons:
            if not isinstance(row, dict) or not row.get("sample_size"):
                continue
            label = str(row.get("horizon") or "")
            bull = self._num(row.get("bullish_pct"))
            bear = self._num(row.get("bearish_pct"))
            avg_return = self._num(row.get("average_return_pct"))
            n = int(row.get("sample_size") or 0)
            if bull is None or bear is None or avg_return is None:
                continue

            directional = max(-100.0, min(100.0, bull - bear))
            return_component = max(-100.0, min(100.0, avg_return * 10.0))
            raw_edge = directional * 0.70 + return_component * 0.30
            sample_factor = min(1.0, n / 5.0)
            edge = raw_edge * (0.60 + 0.40 * sample_factor)

            usable.append({
                "horizon": label,
                "sample_size": n,
                "average_return_pct": round(avg_return, 2),
                "bullish_pct": round(bull, 1),
                "bearish_pct": round(bear, 1),
                "edge_score": round(edge, 1),
                "bias": self._bias(edge),
                "weight": self.HORIZON_WEIGHTS.get(label, 0.10),
            })

        if not usable:
            return self._empty()

        weighted_sum = sum(x["edge_score"] * x["weight"] for x in usable)
        weight_sum = sum(x["weight"] for x in usable) or 1.0
        base_edge = weighted_sum / weight_sum

        similarity = self._num(outcome.get("average_similarity")) or 0.0
        similarity_factor = max(0.50, min(1.0, similarity / 100.0))
        final_edge = max(-100.0, min(100.0, base_edge * similarity_factor))

        total_samples = sum(x["sample_size"] for x in usable)
        consistency = self._consistency(usable)
        quality = self._quality(total_samples, similarity, consistency)

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "historical_edge": {
                "available": True,
                "edge_score": round(final_edge, 1),
                "bias": self._bias(final_edge),
                "evidence": quality,
                "average_similarity": round(similarity, 1) if similarity else None,
                "total_completed_samples": total_samples,
                "directional_consistency": consistency,
                "horizons": usable,
                "summary": self._summary(final_edge, quality, usable),
                "scope": {
                    "contextual_evidence_only": True,
                    "persisted_observations_only": True,
                    "synthetic_backfill": False,
                    "automatic_decision_changes": False,
                    "automatic_weight_changes": False,
                    "automatic_threshold_changes": False,
                    "automatic_execution_changes": False,
                },
            },
        }

    @staticmethod
    def _bias(score: float) -> str:
        if score >= 20.0:
            return "BULLISH"
        if score <= -20.0:
            return "BEARISH"
        return "NEUTRAL"

    @staticmethod
    def _consistency(rows: list[dict[str, Any]]) -> str:
        signs = [1 if x["edge_score"] > 10 else -1 if x["edge_score"] < -10 else 0 for x in rows]
        nonzero = [x for x in signs if x]
        if not nonzero:
            return "LOW"
        dominant = max(nonzero.count(1), nonzero.count(-1)) / len(nonzero)
        if dominant >= 0.80:
            return "HIGH"
        if dominant >= 0.60:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _quality(samples: int, similarity: float, consistency: str) -> str:
        if samples >= 10 and similarity >= 85.0 and consistency == "HIGH":
            return "MATURE"
        if samples >= 5 and similarity >= 75.0:
            return "DEVELOPING"
        if samples >= 1:
            return "EARLY"
        return "INSUFFICIENT_HISTORY"

    @staticmethod
    def _summary(score: float, quality: str, rows: list[dict[str, Any]]) -> str:
        bias = HistoricalEdgeService._bias(score)
        return (
            f"Historical edge is {score:+.1f} ({bias}) with {quality.lower()} evidence "
            f"across {len(rows)} completed evaluation horizon(s)."
        )

    def _empty(self) -> dict[str, Any]:
        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "historical_edge": {
                "available": False,
                "edge_score": None,
                "bias": "UNAVAILABLE",
                "evidence": "INSUFFICIENT_HISTORY",
                "average_similarity": None,
                "total_completed_samples": 0,
                "directional_consistency": "UNAVAILABLE",
                "horizons": [],
                "summary": "Historical Edge activates when comparable configurations complete evaluation horizons.",
                "scope": {
                    "contextual_evidence_only": True,
                    "persisted_observations_only": True,
                    "synthetic_backfill": False,
                    "automatic_decision_changes": False,
                },
            },
        }

    @staticmethod
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None
