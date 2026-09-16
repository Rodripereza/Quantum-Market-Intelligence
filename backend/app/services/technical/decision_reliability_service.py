from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class DecisionReliabilityService:
    """
    DE-DI-006 — Decision Reliability Engine

    Measures whether persisted directional technical states were subsequently
    confirmed by price. It never fabricates observations: only persisted
    snapshots separated by a completed evaluation horizon are scored.
    """

    ENGINE = "QMI Decision Reliability Engine"
    ENGINE_ID = "DE-DI-006"
    VERSION = "0.1.0"

    HORIZONS = (
        ("1D", 24.0),
        ("5D", 120.0),
        ("20D", 480.0),
    )
    DIRECTION_NEUTRAL_BAND = 20.0
    MIN_MOVE_PCT = 0.25

    def analyze(self, *, symbol: str, state_history: list[dict[str, Any]] | None) -> dict[str, Any]:
        rows = [row for row in (state_history or []) if self._valid(row)]
        rows.sort(key=lambda row: self._dt(row.get("created_at")))

        horizon_results = [
            self._evaluate_horizon(rows, label=label, hours=hours)
            for label, hours in self.HORIZONS
        ]
        completed = [h for h in horizon_results if h["evaluations"] > 0]
        total = sum(h["evaluations"] for h in completed)
        correct = sum(h["correct"] for h in completed)

        reliability = round((correct / total) * 100.0, 1) if total else None
        if reliability is None:
            quality = "INSUFFICIENT_HISTORY"
        elif total < 5:
            quality = "EARLY"
        elif reliability >= 70:
            quality = "HIGH"
        elif reliability >= 55:
            quality = "MEDIUM"
        else:
            quality = "LOW"

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_reliability": {
                "available": total > 0,
                "reliability_pct": reliability,
                "quality": quality,
                "sample_size": total,
                "correct": correct,
                "incorrect": total - correct,
                "horizons": horizon_results,
                "latest_evaluations": self._latest_evaluations(rows),
                "methodology": {
                    "basis": "persisted_technical_state_vs_subsequent_persisted_price",
                    "direction_source": "direction_score",
                    "bullish_threshold": self.DIRECTION_NEUTRAL_BAND,
                    "bearish_threshold": -self.DIRECTION_NEUTRAL_BAND,
                    "minimum_price_move_pct": self.MIN_MOVE_PCT,
                    "horizons_hours": {label: hours for label, hours in self.HORIZONS},
                    "note": "A snapshot is scored only when a later persisted snapshot reaches the requested horizon.",
                },
                "scope": {
                    "technical_only": True,
                    "historical_measurement": True,
                    "predictive_claim": False,
                    "automatic_execution": False,
                },
            },
        }

    def _evaluate_horizon(self, rows: list[dict[str, Any]], *, label: str, hours: float) -> dict[str, Any]:
        evaluations = []
        for index, source in enumerate(rows[:-1]):
            target = self._target(rows, index, hours)
            if target is None:
                continue
            result = self._score(source, target)
            if result is not None:
                evaluations.append(result)

        correct = sum(1 for item in evaluations if item["correct"])
        count = len(evaluations)
        return {
            "horizon": label,
            "hours": hours,
            "evaluations": count,
            "correct": correct,
            "incorrect": count - correct,
            "hit_rate_pct": round(correct / count * 100.0, 1) if count else None,
        }

    def _latest_evaluations(self, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        results = []
        for label, hours in self.HORIZONS:
            for index in range(len(rows) - 2, -1, -1):
                target = self._target(rows, index, hours)
                if target is None:
                    continue
                scored = self._score(rows[index], target)
                if scored is not None:
                    scored["horizon"] = label
                    results.append(scored)
                    break
        return results

    def _target(self, rows: list[dict[str, Any]], source_index: int, hours: float) -> dict[str, Any] | None:
        source_time = self._dt(rows[source_index].get("created_at"))
        for candidate in rows[source_index + 1:]:
            elapsed = (self._dt(candidate.get("created_at")) - source_time).total_seconds() / 3600.0
            if elapsed >= hours:
                return candidate
        return None

    def _score(self, source: dict[str, Any], target: dict[str, Any]) -> dict[str, Any] | None:
        direction = self._num(source.get("direction_score"))
        p0 = self._num(source.get("current_price"))
        p1 = self._num(target.get("current_price"))
        if direction is None or p0 is None or p1 is None or p0 <= 0:
            return None

        move = (p1 / p0 - 1.0) * 100.0
        expected = "BULLISH" if direction >= self.DIRECTION_NEUTRAL_BAND else (
            "BEARISH" if direction <= -self.DIRECTION_NEUTRAL_BAND else "NEUTRAL"
        )
        if expected == "BULLISH":
            correct = move >= self.MIN_MOVE_PCT
        elif expected == "BEARISH":
            correct = move <= -self.MIN_MOVE_PCT
        else:
            correct = abs(move) < self.MIN_MOVE_PCT

        return {
            "source_snapshot_id": source.get("id"),
            "source_at": source.get("created_at"),
            "target_snapshot_id": target.get("id"),
            "target_at": target.get("created_at"),
            "direction_score": round(direction, 2),
            "expected_direction": expected,
            "start_price": round(p0, 4),
            "end_price": round(p1, 4),
            "price_return_pct": round(move, 2),
            "correct": bool(correct),
        }

    @staticmethod
    def _valid(row: dict[str, Any]) -> bool:
        return bool(row and row.get("created_at") and row.get("current_price") is not None)

    @staticmethod
    def _num(value: Any) -> float | None:
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _dt(value: Any) -> datetime:
        text = str(value or "").replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
