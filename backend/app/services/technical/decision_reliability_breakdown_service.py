from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class DecisionReliabilityBreakdownService:
    """DE-DI-007 — Reliability Breakdown Engine."""

    ENGINE_ID = "DE-DI-007"
    VERSION = "0.1.0"
    HORIZON_HOURS = 24.0
    MIN_MOVE_PCT = 0.25

    def analyze(self, *, symbol: str, state_history: list[dict[str, Any]] | None) -> dict[str, Any]:
        rows = [r for r in (state_history or []) if r.get("created_at") and r.get("current_price") is not None]
        rows.sort(key=lambda r: self._dt(r["created_at"]))
        samples = []

        for i, source in enumerate(rows[:-1]):
            target = self._target(rows, i)
            if not target:
                continue
            scored = self._score(source, target)
            if scored:
                samples.append(scored)

        by_direction = [self._group(samples, "BULLISH"), self._group(samples, "NEUTRAL"), self._group(samples, "BEARISH")]
        by_strength = [self._strength_group(samples, "MODERATE", 20, 50), self._strength_group(samples, "STRONG", 50, 75), self._strength_group(samples, "EXTREME", 75, 101)]
        best = max((x for x in by_direction + by_strength if x["evaluations"]), key=lambda x: x["hit_rate_pct"], default=None)
        weakest = min((x for x in by_direction + by_strength if x["evaluations"]), key=lambda x: x["hit_rate_pct"], default=None)

        return {
            "engine_id": self.ENGINE_ID, "version": self.VERSION, "status": "operational",
            "reliability_breakdown": {
                "available": bool(samples), "evaluation_horizon": "1D",
                "sample_size": len(samples), "by_direction": by_direction, "by_strength": by_strength,
                "best_segment": best, "weakest_segment": weakest,
                "interpretation": self._interpret(best, weakest, len(samples)),
                "scope": {"technical_only": True, "descriptive": True, "automatic_execution": False},
            },
        }

    def _group(self, samples, label):
        items=[x for x in samples if x["direction"]==label]
        return self._summary(label, items)

    def _strength_group(self, samples, label, lo, hi):
        items=[x for x in samples if lo <= abs(x["direction_score"]) < hi]
        return self._summary(label, items)

    @staticmethod
    def _summary(label, items):
        n=len(items); hits=sum(1 for x in items if x["correct"])
        return {"segment": label, "evaluations": n, "correct": hits,
                "incorrect": n-hits, "hit_rate_pct": round(hits/n*100,1) if n else None}

    def _target(self, rows, i):
        t0=self._dt(rows[i]["created_at"])
        for row in rows[i+1:]:
            if (self._dt(row["created_at"])-t0).total_seconds()/3600 >= self.HORIZON_HOURS:
                return row
        return None

    def _score(self, source, target):
        d=self._num(source.get("direction_score")); p0=self._num(source.get("current_price")); p1=self._num(target.get("current_price"))
        if d is None or p0 is None or p1 is None or p0 <= 0: return None
        move=(p1/p0-1)*100
        direction="BULLISH" if d >= 20 else ("BEARISH" if d <= -20 else "NEUTRAL")
        correct=(move >= self.MIN_MOVE_PCT) if direction=="BULLISH" else ((move <= -self.MIN_MOVE_PCT) if direction=="BEARISH" else abs(move)<self.MIN_MOVE_PCT)
        return {"direction":direction,"direction_score":d,"return_pct":round(move,2),"correct":bool(correct)}

    @staticmethod
    def _interpret(best, weakest, n):
        if not n: return "Insufficient completed 1D observations for segment analysis."
        if not best or not weakest: return "Segment analysis is still developing."
        return f"Best observed segment: {best['segment']} ({best['hit_rate_pct']}%). Weakest observed segment: {weakest['segment']} ({weakest['hit_rate_pct']}%)."

    @staticmethod
    def _num(v):
        try: return None if v is None else float(v)
        except (TypeError,ValueError): return None

    @staticmethod
    def _dt(v):
        dt=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
