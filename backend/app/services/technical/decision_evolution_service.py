from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class DecisionEvolutionService:
    """DE-DI-003.0 — Decision Evolution Engine."""

    ENGINE = "QMI Decision Evolution Engine"
    ENGINE_ID = "DE-DI-003.0"
    VERSION = "0.1.0"

    def analyze(
        self,
        *,
        symbol: str,
        previous_snapshot: dict[str, Any] | None,
        transition_response: dict[str, Any],
        decision_synthesis_response: dict[str, Any],
        confluence_response: dict[str, Any] | None = None,
        previous_driver_snapshot: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        transition = transition_response.get("technical_state_transition") or {}
        current_state = transition.get("current_state") or {}
        next_state = transition.get("next_state_candidate") or {}
        readiness = transition.get("transition_readiness") or {}
        source = transition.get("source_context") or {}
        synthesis = (
            decision_synthesis_response.get("technical_decision_synthesis") or {}
        )
        confluence = (confluence_response or {}).get("technical_confluence") or {}

        current = {
            "state": current_state.get("state"),
            "posture": synthesis.get("final_posture"),
            "state_score": self._num(current_state.get("state_score")),
            "direction_score": self._num(
                source.get("direction_score", confluence.get("direction_score"))
            ),
            "transition_readiness": self._num(readiness.get("score")),
            "transition_probability": self._num(next_state.get("probability")),
            "risk_score": self._num(source.get("risk_score")),
            "risk_state": current_state.get("risk_state"),
            "next_state": next_state.get("state"),
            "current_price": self._num(transition_response.get("current_price")),
        }

        if not previous_snapshot:
            return self._response(
                symbol=symbol,
                available=False,
                current=current,
                reason="NO_PERSISTED_BASELINE",
            )

        previous = {
            "snapshot_id": previous_snapshot.get("id"),
            "observed_at": previous_snapshot.get("created_at"),
            "state": previous_snapshot.get("state"),
            "state_score": self._num(previous_snapshot.get("state_score")),
            "direction_score": self._num(previous_snapshot.get("direction_score")),
            "transition_readiness": self._num(
                previous_snapshot.get("transition_readiness_score")
            ),
            "transition_probability": self._num(
                previous_snapshot.get("next_state_probability")
            ),
            "risk_score": self._num(previous_snapshot.get("risk_score")),
            "risk_state": previous_snapshot.get("risk_state"),
            "next_state": previous_snapshot.get("next_state"),
            "current_price": self._num(previous_snapshot.get("current_price")),
        }

        deltas = {
            "state_score": self._delta(previous["state_score"], current["state_score"]),
            "direction_score": self._delta(
                previous["direction_score"], current["direction_score"]
            ),
            "transition_readiness": self._delta(
                previous["transition_readiness"], current["transition_readiness"]
            ),
            "transition_probability": self._delta(
                previous["transition_probability"], current["transition_probability"]
            ),
            "risk_score": self._delta(previous["risk_score"], current["risk_score"]),
            "price": self._delta(previous["current_price"], current["current_price"]),
        }

        signals = {
            "direction": self._signal(deltas["direction_score"], True),
            "transition_readiness": self._signal(
                deltas["transition_readiness"], True
            ),
            "transition_probability": self._signal(
                deltas["transition_probability"], True
            ),
            "risk": self._signal(deltas["risk_score"], False),
        }

        trajectory = self._trajectory(signals)
        age = self._age(previous.get("observed_at"))
        driver_evolution = self._driver_evolution(previous_driver_snapshot, confluence)

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "symbol": str(symbol).strip().upper(),
            "decision_evolution": {
                "available": True,
                "trajectory": trajectory,
                "previous": previous,
                "current": current,
                "deltas": deltas,
                "signals": signals,
                "driver_evolution": driver_evolution,
                "baseline": {
                    "type": "LATEST_PERSISTED_TECHNICAL_STATE",
                    "snapshot_id": previous.get("snapshot_id"),
                    "observed_at": previous.get("observed_at"),
                    "age": age,
                    "freshness": self._freshness(age),
                },
                "interpretation": self._interpret(trajectory, previous, current, deltas),
                "scope": {
                    "technical_only": True,
                    "historical_baseline": True,
                    "driver_history_available": bool(driver_evolution.get("available")),
                    "automatic_execution": False,
                    "note": (
                        "Phase 1 compares the live evaluation with the latest persisted "
                        "technical-state snapshot. Historical Confluence driver scores "
                        "are not persisted yet."
                    ),
                },
            },
        }

    def _driver_evolution(self, previous_driver_snapshot, confluence):
        current_rows = ((confluence.get("diagnostics") or {}).get("engine_contributions") or [])
        current = {str(x.get("engine") or "").lower(): x for x in current_rows if isinstance(x, dict) and x.get("available") is not False}
        previous = {str(x.get("engine") or "").lower(): x for x in ((previous_driver_snapshot or {}).get("drivers") or []) if isinstance(x, dict)}
        if not current or not previous:
            return {"available": False, "reason": "NO_PERSISTED_DRIVER_BASELINE", "drivers": []}
        drivers=[]
        for engine, now in current.items():
            before=previous.get(engine)
            if not before: continue
            p=self._num(before.get("score")); c=self._num(now.get("score")); d=self._delta(p,c)
            drivers.append({"engine":engine,"previous_score":p,"current_score":c,"delta":d,
                "state":self._signal(d,True).get("state"),
                "previous_confidence":self._num(before.get("confidence")),"current_confidence":self._num(now.get("confidence")),
                "previous_weight_pct":self._num(before.get("effective_weight_pct")),"current_weight_pct":self._num(now.get("effective_weight_pct")),
                "previous_contribution":self._num(before.get("normalized_contribution")),"current_contribution":self._num(now.get("normalized_contribution"))})
        vals=[x["delta"] for x in drivers if x["delta"] is not None]
        avg=round(sum(vals)/len(vals),2) if vals else None
        improving=[x for x in drivers if x["delta"] is not None and x["delta"]>2]
        worsening=[x for x in drivers if x["delta"] is not None and x["delta"]<-2]
        trajectory="UNAVAILABLE" if avg is None else ("RECOVERING" if avg>2 else "DETERIORATING" if avg<-2 else "MIXED" if improving and worsening else "STABLE")
        return {"available":bool(drivers),"baseline_created_at":(previous_driver_snapshot or {}).get("created_at"),
            "trajectory":trajectory,"average_score_delta":avg,
            "dominant_improvement":max(improving,key=lambda x:x["delta"],default=None),
            "dominant_deterioration":min(worsening,key=lambda x:x["delta"],default=None),"drivers":drivers}

    def _response(self, *, symbol, available, current, reason):
        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "symbol": str(symbol).strip().upper(),
            "decision_evolution": {
                "available": available,
                "reason": reason,
                "current": current,
                "trajectory": {
                    "state": "INSUFFICIENT_HISTORY",
                    "score": 0.0,
                    "improving_signals": 0,
                    "deteriorating_signals": 0,
                },
                "scope": {
                    "technical_only": True,
                    "historical_baseline": False,
                    "driver_history_available": False,
                    "automatic_execution": False,
                },
            },
        }

    def _trajectory(self, signals):
        weights = {
            "direction": 0.35,
            "transition_readiness": 0.25,
            "transition_probability": 0.20,
            "risk": 0.20,
        }
        score = 0.0
        improving = deteriorating = 0

        for key, weight in weights.items():
            state = signals[key]["state"]
            if state == "IMPROVING":
                score += weight
                improving += 1
            elif state == "DETERIORATING":
                score -= weight
                deteriorating += 1

        if score >= 0.30:
            state = "RECOVERING"
        elif score <= -0.30:
            state = "DETERIORATING"
        elif improving and deteriorating:
            state = "MIXED"
        else:
            state = "STABLE"

        return {
            "state": state,
            "score": round(score * 100.0, 1),
            "improving_signals": improving,
            "deteriorating_signals": deteriorating,
        }

    @staticmethod
    def _signal(delta, positive_is_better):
        if delta is None:
            return {"state": "UNAVAILABLE", "delta": None}
        adjusted = delta if positive_is_better else -delta
        if adjusted > 2.0:
            state = "IMPROVING"
        elif adjusted < -2.0:
            state = "DETERIORATING"
        else:
            state = "STABLE"
        return {"state": state, "delta": round(delta, 2)}

    @staticmethod
    def _interpret(trajectory, previous, current, deltas):
        state = trajectory["state"]
        prefix = {
            "RECOVERING": "Technical conditions are improving versus the persisted baseline.",
            "DETERIORATING": "Technical conditions are deteriorating versus the persisted baseline.",
            "MIXED": "Technical evolution is mixed; improving and deteriorating signals coexist.",
            "STABLE": "Technical conditions are broadly stable versus the persisted baseline.",
        }.get(state, "Decision evolution is unavailable.")

        extra = ""
        if previous.get("state") != current.get("state"):
            extra += (
                f" State moved from {previous.get('state') or 'UNKNOWN'} "
                f"to {current.get('state') or 'UNKNOWN'}."
            )

        delta = deltas.get("direction_score")
        if delta is not None and abs(delta) >= 2.0:
            verb = "improved" if delta > 0 else "weakened"
            extra += f" Direction score {verb} by {abs(delta):.1f} points."

        return prefix + extra

    @staticmethod
    def _delta(previous, current):
        if previous is None or current is None:
            return None
        return round(current - previous, 2)

    @staticmethod
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _age(value):
        if not value:
            return {"seconds": None, "hours": None, "days": None}
        try:
            observed = datetime.fromisoformat(str(value))
            if observed.tzinfo is None:
                observed = observed.replace(tzinfo=timezone.utc)
            seconds = max(0.0, (datetime.now(timezone.utc) - observed).total_seconds())
            return {
                "seconds": round(seconds, 1),
                "hours": round(seconds / 3600.0, 2),
                "days": round(seconds / 86400.0, 2),
            }
        except ValueError:
            return {"seconds": None, "hours": None, "days": None}

    @staticmethod
    def _freshness(age):
        days = age.get("days")
        if days is None:
            return "UNKNOWN"
        if days <= 1:
            return "FRESH"
        if days <= 7:
            return "RECENT"
        return "STALE"
