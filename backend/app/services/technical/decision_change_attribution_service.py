from __future__ import annotations

from typing import Any


class DecisionChangeAttributionService:
    """
    DE-DI-004 — Decision Change Attribution Engine

    Explains which persisted technical drivers and aggregate state metrics are
    pushing the current decision toward improvement or deterioration.
    """

    ENGINE = "QMI Decision Change Attribution Engine"
    ENGINE_ID = "DE-DI-004"
    VERSION = "0.1.0"
    DRIVER_THRESHOLD = 2.0

    def analyze(
        self,
        *,
        symbol: str,
        decision_evolution_response: dict[str, Any] | None,
        current_posture: str | None,
        previous_driver_snapshot: dict[str, Any] | None,
    ) -> dict[str, Any]:
        evolution = (decision_evolution_response or {}).get("decision_evolution") or {}
        driver_evolution = evolution.get("driver_evolution") or {}
        drivers = driver_evolution.get("drivers") or []
        previous_posture = self._previous_posture(previous_driver_snapshot)

        causes = []
        for driver in drivers:
            delta = self._num(driver.get("delta"))
            if delta is None:
                continue
            contribution_before = self._num(driver.get("previous_contribution"))
            contribution_now = self._num(driver.get("current_contribution"))
            contribution_delta = self._delta(contribution_before, contribution_now)
            weight = self._num(driver.get("current_weight_pct")) or 0.0

            # Score movement is the primary signal. Weight makes attribution
            # reflect actual Confluence relevance without inventing causality.
            impact = delta * max(weight, 1.0) / 100.0
            direction = (
                "IMPROVING" if delta > self.DRIVER_THRESHOLD
                else "DETERIORATING" if delta < -self.DRIVER_THRESHOLD
                else "STABLE"
            )
            causes.append({
                "type": "DRIVER",
                "engine": driver.get("engine"),
                "direction": direction,
                "score_delta": round(delta, 2),
                "contribution_delta": contribution_delta,
                "effective_weight_pct": round(weight, 2),
                "impact_score": round(impact, 3),
                "previous_score": driver.get("previous_score"),
                "current_score": driver.get("current_score"),
            })

        metric_causes = self._metric_causes(evolution)
        improving = sorted(
            [x for x in causes if x["direction"] == "IMPROVING"],
            key=lambda x: abs(x["impact_score"]),
            reverse=True,
        )
        deteriorating = sorted(
            [x for x in causes if x["direction"] == "DETERIORATING"],
            key=lambda x: abs(x["impact_score"]),
            reverse=True,
        )

        driver_net = round(sum(x["impact_score"] for x in causes), 3) if causes else 0.0
        metric_net = round(sum(x["impact_score"] for x in metric_causes), 3)
        net_pressure = round(driver_net + metric_net, 3)

        if net_pressure > 0.75:
            pressure = "IMPROVING"
        elif net_pressure < -0.75:
            pressure = "DETERIORATING"
        elif improving and deteriorating:
            pressure = "MIXED"
        else:
            pressure = "STABLE"

        posture_changed = bool(
            previous_posture
            and current_posture
            and str(previous_posture).upper() != str(current_posture).upper()
        )

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "symbol": str(symbol).strip().upper(),
            "decision_change_attribution": {
                "available": bool(causes or metric_causes),
                "posture_change": {
                    "detectable": previous_posture is not None,
                    "changed": posture_changed,
                    "previous": previous_posture,
                    "current": current_posture,
                },
                "pressure": {
                    "state": pressure,
                    "net_score": net_pressure,
                    "driver_component": driver_net,
                    "metric_component": metric_net,
                },
                "primary_improvement": improving[0] if improving else None,
                "primary_deterioration": deteriorating[0] if deteriorating else None,
                "improving_causes": improving[:4],
                "deteriorating_causes": deteriorating[:4],
                "metric_causes": metric_causes,
                "summary": self._summary(
                    previous_posture=previous_posture,
                    current_posture=current_posture,
                    posture_changed=posture_changed,
                    pressure=pressure,
                    improving=improving,
                    deteriorating=deteriorating,
                ),
                "scope": {
                    "technical_only": True,
                    "deterministic": True,
                    "automatic_execution": False,
                    "method": "persisted_driver_delta_x_effective_weight_plus_state_metric_pressure",
                },
            },
        }

    def _metric_causes(self, evolution: dict[str, Any]) -> list[dict[str, Any]]:
        deltas = evolution.get("deltas") or {}
        signals = evolution.get("signals") or {}
        specs = [
            ("Direction", "direction_score", "direction", 0.35),
            ("Readiness", "transition_readiness", "transition_readiness", 0.25),
            ("Transition Probability", "transition_probability", "transition_probability", 0.20),
            ("Risk", "risk_score", "risk", 0.20),
        ]
        result = []
        for label, delta_key, signal_key, weight in specs:
            delta = self._num(deltas.get(delta_key))
            signal = str((signals.get(signal_key) or {}).get("state") or "UNAVAILABLE").upper()
            if delta is None or signal == "UNAVAILABLE":
                continue
            signed = abs(delta) * weight
            if signal == "DETERIORATING":
                signed *= -1
            elif signal == "STABLE":
                signed = 0.0
            result.append({
                "type": "METRIC",
                "metric": label,
                "direction": signal,
                "delta": round(delta, 2),
                "weight": weight,
                "impact_score": round(signed, 3),
            })
        return result

    @staticmethod
    def _previous_posture(snapshot: dict[str, Any] | None) -> str | None:
        if not snapshot:
            return None
        posture = snapshot.get("decision_posture")
        if posture:
            return str(posture).upper()
        for row in snapshot.get("drivers") or []:
            posture = row.get("decision_posture")
            if posture:
                return str(posture).upper()
        return None

    @staticmethod
    def _summary(*, previous_posture, current_posture, posture_changed, pressure, improving, deteriorating):
        if posture_changed:
            prefix = f"Decision posture changed from {previous_posture} to {current_posture}."
        elif previous_posture and current_posture:
            prefix = f"Decision posture remains {current_posture}."
        else:
            prefix = f"Current posture is {current_posture or 'UNKNOWN'}; a prior posture baseline is not yet available."

        parts = [prefix, f"Net technical pressure is {pressure.lower()}."]
        if improving:
            top = improving[0]
            parts.append(f"Largest improving driver is {str(top.get('engine') or 'unknown').title()} ({top.get('score_delta'):+.1f}).")
        if deteriorating:
            top = deteriorating[0]
            parts.append(f"Largest deteriorating driver is {str(top.get('engine') or 'unknown').title()} ({top.get('score_delta'):+.1f}).")
        return " ".join(parts)

    @staticmethod
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _delta(previous, current):
        if previous is None or current is None:
            return None
        return round(current - previous, 3)
