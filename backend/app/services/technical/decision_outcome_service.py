from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class DecisionOutcomeService:
    """DE-DI-008 — Decision Outcome Engine.

    Evaluates persisted QMI postures against later persisted prices.
    This is descriptive historical measurement only; it does not execute trades.
    """

    ENGINE_ID = "DE-DI-008"
    VERSION = "0.1.0"
    HORIZONS = (("1D", 24.0), ("5D", 120.0), ("20D", 480.0))
    MIN_MOVE_PCT = 0.25

    def analyze(self, *, symbol: str, state_history: list[dict[str, Any]] | None) -> dict[str, Any]:
        rows = [r for r in (state_history or []) if self._valid(r)]
        rows.sort(key=lambda r: self._dt(r["created_at"]))

        evaluations: list[dict[str, Any]] = []
        for i, source in enumerate(rows[:-1]):
            posture = self._posture(source)
            if not posture:
                continue
            for label, hours in self.HORIZONS:
                target = self._target(rows, i, hours)
                if target is None:
                    continue
                scored = self._score(source, target, posture, label)
                if scored:
                    evaluations.append(scored)

        completed_1d = [e for e in evaluations if e["horizon"] == "1D"]
        by_posture = [self._summary(completed_1d, p) for p in ("WAIT", "ENTER", "ADD", "REDUCE", "EXIT")]
        active = [x for x in by_posture if x["evaluations"] > 0]

        total = len(completed_1d)
        successful = sum(1 for e in completed_1d if e["successful"])
        quality_score = round(successful / total * 100.0, 1) if total else None

        latest = []
        for label, _ in self.HORIZONS:
            candidates = [e for e in evaluations if e["horizon"] == label]
            if candidates:
                latest.append(candidates[-1])

        best = max(active, key=lambda x: x["success_rate_pct"], default=None)
        weakest = min(active, key=lambda x: x["success_rate_pct"], default=None)

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_outcome": {
                "available": total > 0,
                "quality_score": quality_score,
                "quality": self._quality(quality_score, total),
                "sample_size": total,
                "successful": successful,
                "unsuccessful": total - successful,
                "by_posture": by_posture,
                "latest_completed_outcomes": latest,
                "best_posture": best,
                "weakest_posture": weakest,
                "methodology": {
                    "evaluation_basis": "persisted_decision_posture_vs_subsequent_persisted_price",
                    "primary_score_horizon": "1D",
                    "horizons_hours": {label: hours for label, hours in self.HORIZONS},
                    "minimum_move_pct": self.MIN_MOVE_PCT,
                    "posture_logic": {
                        "ENTER": "success when subsequent price rises by at least minimum move",
                        "ADD": "success when subsequent price rises by at least minimum move",
                        "REDUCE": "success when subsequent price falls by at least minimum move",
                        "EXIT": "success when subsequent price falls by at least minimum move",
                        "WAIT": "success when subsequent absolute move remains below minimum move",
                    },
                },
                "scope": {
                    "historical_measurement": True,
                    "technical_only": True,
                    "automatic_execution": False,
                    "predictive_claim": False,
                },
            },
        }

    def _score(self, source, target, posture, horizon):
        p0 = self._num(source.get("current_price"))
        p1 = self._num(target.get("current_price"))
        if p0 is None or p1 is None or p0 <= 0:
            return None
        move = (p1 / p0 - 1.0) * 100.0

        if posture in {"ENTER", "ADD"}:
            successful = move >= self.MIN_MOVE_PCT
            outcome_pct = move
        elif posture in {"REDUCE", "EXIT"}:
            successful = move <= -self.MIN_MOVE_PCT
            outcome_pct = -move  # positive = downside avoided
        elif posture == "WAIT":
            successful = abs(move) < self.MIN_MOVE_PCT
            outcome_pct = -abs(move)
        else:
            return None

        return {
            "source_snapshot_id": source.get("id"),
            "source_at": source.get("created_at"),
            "target_snapshot_id": target.get("id"),
            "target_at": target.get("created_at"),
            "posture": posture,
            "horizon": horizon,
            "start_price": round(p0, 4),
            "end_price": round(p1, 4),
            "price_return_pct": round(move, 2),
            "decision_outcome_pct": round(outcome_pct, 2),
            "successful": bool(successful),
        }

    @staticmethod
    def _summary(items, posture):
        rows = [x for x in items if x["posture"] == posture]
        n = len(rows)
        hits = sum(1 for x in rows if x["successful"])
        avg = round(sum(x["decision_outcome_pct"] for x in rows) / n, 2) if n else None
        return {
            "posture": posture,
            "evaluations": n,
            "successful": hits,
            "unsuccessful": n - hits,
            "success_rate_pct": round(hits / n * 100.0, 1) if n else None,
            "average_outcome_pct": avg,
        }

    def _target(self, rows, source_index, hours):
        source_time = self._dt(rows[source_index]["created_at"])
        for candidate in rows[source_index + 1:]:
            elapsed = (self._dt(candidate["created_at"]) - source_time).total_seconds() / 3600.0
            if elapsed >= hours:
                return candidate
        return None

    @staticmethod
    def _posture(row):
        value = str(row.get("decision_posture") or "").strip().upper()
        return value if value in {"WAIT", "ENTER", "ADD", "REDUCE", "EXIT"} else None

    @staticmethod
    def _quality(score, sample):
        if score is None:
            return "INSUFFICIENT_HISTORY"
        if sample < 5:
            return "EARLY"
        if score >= 70:
            return "HIGH"
        if score >= 55:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _valid(row):
        return bool(row and row.get("created_at") and row.get("current_price") is not None)

    @staticmethod
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _dt(value):
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
