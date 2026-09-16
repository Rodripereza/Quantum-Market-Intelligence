from __future__ import annotations
from datetime import datetime, timezone
from typing import Any

class HistoricalOutcomeMemoryService:
    """DE-DI-011 — measures what happened after DE-DI-010 historical analogues."""
    ENGINE_ID = "DE-DI-011"
    VERSION = "0.1.0"
    HORIZONS = (("1D", 24.0), ("5D", 120.0), ("20D", 480.0))
    MATERIAL_MOVE_PCT = 0.25

    def analyze(self, *, decision_memory: dict[str, Any] | None,
                state_history: list[dict[str, Any]] | None) -> dict[str, Any]:
        memory = (decision_memory or {}).get("decision_memory") or {}
        matches = memory.get("matches") or []
        rows = [r for r in (state_history or []) if self._valid(r)]
        rows.sort(key=lambda r: self._dt(r["created_at"]))
        if not matches:
            return self._empty("Historical outcomes activate when Decision Memory finds similar persisted configurations.")

        by_id = {r.get("id"): i for i, r in enumerate(rows)}
        horizons = []
        for label, hours in self.HORIZONS:
            obs = []
            for match in matches:
                idx = by_id.get(match.get("snapshot_id"))
                if idx is None: continue
                target = self._target(rows, idx, hours)
                if target is None: continue
                p0, p1 = self._num(rows[idx].get("current_price")), self._num(target.get("current_price"))
                if p0 is None or p1 is None or p0 <= 0: continue
                ret = (p1 / p0 - 1.0) * 100.0
                obs.append({"source_snapshot_id": rows[idx].get("id"),
                            "target_snapshot_id": target.get("id"),
                            "similarity_score": self._num(match.get("similarity_score")),
                            "return_pct": round(ret, 2),
                            "direction": self._direction(ret)})
            horizons.append(self._summarize(label, obs))

        completed = [h for h in horizons if h["sample_size"]]
        primary = next((h for h in completed if h["horizon"] == "1D"), completed[0] if completed else None)
        bias = self._bias(primary)
        readiness = self._readiness(primary, memory)
        return {"engine_id": self.ENGINE_ID, "version": self.VERSION, "status": "operational",
                "historical_outcome_memory": {
                    "available": bool(completed), "readiness": readiness, "historical_bias": bias,
                    "matches_considered": len(matches), "average_similarity": memory.get("average_similarity"),
                    "primary_horizon": primary.get("horizon") if primary else None, "horizons": horizons,
                    "summary": self._summary(primary, bias),
                    "scope": {"persisted_observations_only": True, "synthetic_backfill": False,
                              "contextual_evidence_only": True, "automatic_decision_changes": False,
                              "automatic_weight_changes": False, "automatic_execution_changes": False}}}

    def _summarize(self, label, obs):
        n=len(obs)
        if not n:
            return {"horizon":label,"sample_size":0,"average_return_pct":None,"median_return_pct":None,
                    "bullish_pct":None,"bearish_pct":None,"neutral_pct":None,"observations":[]}
        vals=sorted(x["return_pct"] for x in obs)
        med=vals[n//2] if n%2 else (vals[n//2-1]+vals[n//2])/2
        bull=sum(x["direction"]=="BULLISH" for x in obs)
        bear=sum(x["direction"]=="BEARISH" for x in obs)
        return {"horizon":label,"sample_size":n,"average_return_pct":round(sum(vals)/n,2),
                "median_return_pct":round(med,2),"bullish_pct":round(bull/n*100,1),
                "bearish_pct":round(bear/n*100,1),"neutral_pct":round((n-bull-bear)/n*100,1),
                "observations":obs}

    def _target(self, rows, idx, hours):
        t0=self._dt(rows[idx]["created_at"])
        for row in rows[idx+1:]:
            if (self._dt(row["created_at"])-t0).total_seconds()/3600 >= hours: return row
        return None

    def _direction(self, ret):
        return "BULLISH" if ret >= self.MATERIAL_MOVE_PCT else "BEARISH" if ret <= -self.MATERIAL_MOVE_PCT else "NEUTRAL"

    @staticmethod
    def _bias(p):
        if not p: return "UNAVAILABLE"
        b,u=p.get("bearish_pct") or 0,p.get("bullish_pct") or 0
        return "BEARISH" if b>=u+15 else "BULLISH" if u>=b+15 else "MIXED"

    @staticmethod
    def _readiness(p,memory):
        if not p:return "INSUFFICIENT_HISTORY"
        n=int(p.get("sample_size") or 0); sim=float(memory.get("average_similarity") or 0)
        return "MATURE" if n>=5 and sim>=85 else "DEVELOPING" if n>=3 else "EARLY"

    @staticmethod
    def _summary(p,bias):
        if not p:return "Similar configurations exist, but none has completed an evaluation horizon yet."
        return f"{p['sample_size']} comparable outcome(s) completed {p['horizon']}. Average subsequent return: {p['average_return_pct']:+.2f}%. Historical bias: {bias}."

    def _empty(self,reason):
        return {"engine_id":self.ENGINE_ID,"version":self.VERSION,"status":"operational",
                "historical_outcome_memory":{"available":False,"readiness":"INSUFFICIENT_HISTORY",
                "historical_bias":"UNAVAILABLE","matches_considered":0,"average_similarity":None,
                "primary_horizon":None,"horizons":[self._summarize(x,[]) for x,_ in self.HORIZONS],
                "summary":reason,"scope":{"persisted_observations_only":True,"synthetic_backfill":False,
                "contextual_evidence_only":True,"automatic_decision_changes":False}}}

    @staticmethod
    def _valid(r): return isinstance(r,dict) and r.get("created_at") and r.get("current_price") is not None
    @staticmethod
    def _num(v):
        try:return None if v is None else float(v)
        except (TypeError,ValueError):return None
    @staticmethod
    def _dt(v):
        d=datetime.fromisoformat(str(v).replace("Z","+00:00"))
        if d.tzinfo is None:d=d.replace(tzinfo=timezone.utc)
        return d.astimezone(timezone.utc)
