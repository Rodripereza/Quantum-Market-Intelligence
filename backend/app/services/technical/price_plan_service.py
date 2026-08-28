from __future__ import annotations

from typing import Any


class TechnicalPricePlanService:
    """
    DE-TA-016.1 — Technical Price Plan Engine

    Converts an already-qualified DE-TA-016.0 setup plus DE-TA-006.1
    structural support/resistance zones into deterministic watch/action
    price levels.

    It does not relax upstream gates. If the setup is not actionable,
    levels are returned as WATCH levels rather than authorized entries.
    """

    def analyze(
        self,
        *,
        setup_response: dict[str, Any],
        support_resistance_response: dict[str, Any],
    ) -> dict[str, Any]:
        setup = setup_response.get("technical_setup") or {}

        if not setup.get("available", False):
            return self._unavailable("Technical setup is not available.")

        current_price = self._number(
            support_resistance_response.get("current_price")
        )
        atr = self._number(
            support_resistance_response.get("atr14")
        )

        if current_price <= 0:
            return self._unavailable(
                "Support/resistance current price is not available."
            )

        summary = support_resistance_response.get("summary") or {}
        supports = support_resistance_response.get("support_zones") or []
        resistances = support_resistance_response.get("resistance_zones") or []

        nearest_support = summary.get("nearest_support")
        nearest_resistance = summary.get("nearest_resistance")
        active_zone = summary.get("active_zone")

        setup_status = str(
            setup.get("setup_status") or "NO_SETUP"
        ).upper()
        setup_type = str(
            setup.get("setup_type") or "NONE"
        ).upper()
        direction = str(
            setup.get("direction") or "NEUTRAL"
        ).upper()
        timing = str(
            setup.get("timing") or "MONITOR"
        ).upper()
        quality = self._number(setup.get("setup_quality"))

        gates = setup.get("gates") or {}
        hard_gate_passed = bool(gates.get("hard_gate_passed", False))
        enter_gate = str(gates.get("ENTER") or "UNKNOWN").upper()
        add_gate = str(gates.get("ADD") or "UNKNOWN").upper()

        authorization = self._authorization(
            setup_status=setup_status,
            hard_gate_passed=hard_gate_passed,
            enter_gate=enter_gate,
            add_gate=add_gate,
        )

        if direction == "LONG":
            plan = self._long_plan(
                current_price=current_price,
                atr=atr,
                nearest_support=nearest_support,
                nearest_resistance=nearest_resistance,
                supports=supports,
                resistances=resistances,
                active_zone=active_zone,
            )
        elif direction in {"BEARISH_WATCH", "DEFENSIVE"}:
            plan = self._bearish_watch_plan(
                current_price=current_price,
                atr=atr,
                nearest_support=nearest_support,
                nearest_resistance=nearest_resistance,
                supports=supports,
                resistances=resistances,
                active_zone=active_zone,
            )
        else:
            plan = self._neutral_plan(
                current_price=current_price,
                nearest_support=nearest_support,
                nearest_resistance=nearest_resistance,
            )

        rr = self._risk_reward(
            direction=direction,
            entry=plan.get("entry_reference"),
            invalidation=plan.get("invalidation"),
            target=plan.get("primary_target"),
        )

        return {
            "engine": "QMI Technical Price Plan Engine",
            "engine_id": "DE-TA-016.1",
            "version": "0.1.0",
            "status": "operational",
            "technical_price_plan": {
                "available": True,
                "authorization": authorization,
                "setup_status": setup_status,
                "setup_type": setup_type,
                "direction": direction,
                "setup_quality": round(quality, 1),
                "timing": timing,
                "current_price": round(current_price, 6),
                "atr14": round(atr, 6),
                "trigger": plan.get("trigger"),
                "entry_zone": plan.get("entry_zone"),
                "entry_reference": plan.get("entry_reference"),
                "invalidation": plan.get("invalidation"),
                "primary_target": plan.get("primary_target"),
                "secondary_target": plan.get("secondary_target"),
                "risk_reward": rr,
                "structural_context": {
                    "nearest_support": nearest_support,
                    "nearest_resistance": nearest_resistance,
                    "active_zone": active_zone,
                },
                "gates": {
                    "hard_gate_passed": hard_gate_passed,
                    "ENTER": enter_gate,
                    "ADD": add_gate,
                    "gate_preservation": True,
                },
                "notes": plan.get("notes", []),
                "scope": {
                    "technical_only": True,
                    "structural_levels_only": True,
                    "automatic_execution": False,
                    "portfolio_allocation": False,
                    "gate_preservation": True,
                },
            },
        }

    def _long_plan(
        self, *, current_price, atr, nearest_support, nearest_resistance,
        supports, resistances, active_zone,
    ):
        support = nearest_support or self._nearest_below(supports, current_price)
        resistance = nearest_resistance or self._nearest_above(
            resistances, current_price
        )

        entry_zone = self._zone_payload(
            active_zone if self._zone_type(active_zone) == "SUPPORT" else support
        )

        trigger = None
        if resistance:
            trigger = {
                "type": "RESISTANCE_BREAK",
                "price": self._number(resistance.get("upper")),
                "zone": self._zone_payload(resistance),
                "condition": "Close above structural resistance.",
            }

        invalidation = None
        if support:
            buffer_ = max(atr * 0.25, current_price * 0.003)
            invalidation = round(
                max(0.0, self._number(support.get("lower")) - buffer_), 6
            )

        primary = self._zone_center(resistance)
        secondary_zone = self._next_above(
            resistances, primary if primary else current_price
        )
        secondary = self._zone_center(secondary_zone)

        entry_ref = (
            self._zone_center(entry_zone)
            if entry_zone
            else current_price
        )

        return {
            "trigger": trigger,
            "entry_zone": entry_zone,
            "entry_reference": entry_ref,
            "invalidation": invalidation,
            "primary_target": primary,
            "secondary_target": secondary,
            "notes": [
                "Long levels are structural references, not an authorization.",
                "Entry remains subject to DE-TA-016.0 and upstream gates.",
            ],
        }

    def _bearish_watch_plan(
        self, *, current_price, atr, nearest_support, nearest_resistance,
        supports, resistances, active_zone,
    ):
        support = nearest_support or self._nearest_below(supports, current_price)
        resistance = nearest_resistance or self._nearest_above(
            resistances, current_price
        )

        trigger = None
        if support:
            trigger = {
                "type": "SUPPORT_BREAK",
                "price": self._number(support.get("lower")),
                "zone": self._zone_payload(support),
                "condition": "Close below structural support.",
            }

        # For a bearish watch, this is the zone where downside continuation
        # would be structurally confirmed. It is not a short-sale instruction.
        entry_zone = self._zone_payload(support)

        invalidation = None
        if resistance:
            buffer_ = max(atr * 0.25, current_price * 0.003)
            invalidation = round(
                self._number(resistance.get("upper")) + buffer_, 6
            )

        primary_zone = self._next_below(
            supports,
            self._number(support.get("lower")) if support else current_price,
        )
        primary = self._zone_center(primary_zone)

        secondary_zone = self._next_below(
            supports,
            self._number(primary_zone.get("lower"))
            if primary_zone else (
                self._number(support.get("lower"))
                if support else current_price
            ),
        )
        secondary = self._zone_center(secondary_zone)

        entry_ref = (
            self._number(support.get("lower"))
            if support
            else current_price
        )

        return {
            "trigger": trigger,
            "entry_zone": entry_zone,
            "entry_reference": entry_ref,
            "invalidation": invalidation,
            "primary_target": primary,
            "secondary_target": secondary,
            "notes": [
                "Bearish-watch levels describe downside structural risk.",
                "They are not an instruction to open a short position.",
                "Any long entry remains controlled by upstream ENTER/ADD gates.",
            ],
        }

    def _neutral_plan(
        self, *, current_price, nearest_support, nearest_resistance,
    ):
        return {
            "trigger": None,
            "entry_zone": None,
            "entry_reference": current_price,
            "invalidation": None,
            "primary_target": None,
            "secondary_target": None,
            "notes": [
                "No directional price plan is active.",
                "Nearest structural zones are retained for monitoring.",
            ],
        }

    @staticmethod
    def _authorization(
        *, setup_status, hard_gate_passed, enter_gate, add_gate,
    ):
        allowed = {"PERMITTED", "READY", "ACTIVE", "ELIGIBLE", "PREFERRED"}
        if (
            hard_gate_passed
            and setup_status in {"VALID", "HIGH_CONVICTION"}
            and (enter_gate in allowed or add_gate in allowed)
        ):
            return "ACTIONABLE"
        if setup_status == "DEVELOPING":
            return "WATCH_ONLY"
        return "BLOCKED"

    def _risk_reward(self, *, direction, entry, invalidation, target):
        entry = self._number(entry, None)
        invalidation = self._number(invalidation, None)
        target = self._number(target, None)

        if entry is None or invalidation is None or target is None:
            return {
                "available": False,
                "ratio": None,
                "risk_per_share": None,
                "reward_per_share": None,
            }

        if direction == "LONG":
            risk = entry - invalidation
            reward = target - entry
        elif direction in {"BEARISH_WATCH", "DEFENSIVE"}:
            risk = invalidation - entry
            reward = entry - target
        else:
            return {
                "available": False,
                "ratio": None,
                "risk_per_share": None,
                "reward_per_share": None,
            }

        if risk <= 0 or reward <= 0:
            return {
                "available": False,
                "ratio": None,
                "risk_per_share": round(risk, 6),
                "reward_per_share": round(reward, 6),
            }

        return {
            "available": True,
            "ratio": round(reward / risk, 2),
            "risk_per_share": round(risk, 6),
            "reward_per_share": round(reward, 6),
        }

    def _nearest_below(self, zones, price):
        candidates = [
            z for z in zones
            if self._number(z.get("upper")) < price
        ]
        return min(
            candidates,
            key=lambda z: self._number(z.get("distance_pct"), 999999.0),
            default=None,
        )

    def _nearest_above(self, zones, price):
        candidates = [
            z for z in zones
            if self._number(z.get("lower")) > price
        ]
        return min(
            candidates,
            key=lambda z: self._number(z.get("distance_pct"), 999999.0),
            default=None,
        )

    def _next_below(self, zones, price):
        candidates = [
            z for z in zones
            if self._number(z.get("upper")) < price
        ]
        return max(
            candidates,
            key=lambda z: self._number(z.get("upper")),
            default=None,
        )

    def _next_above(self, zones, price):
        candidates = [
            z for z in zones
            if self._number(z.get("lower")) > price
        ]
        return min(
            candidates,
            key=lambda z: self._number(z.get("lower")),
            default=None,
        )

    def _zone_payload(self, zone):
        if not isinstance(zone, dict):
            return None
        return {
            "type": zone.get("type"),
            "lower": self._number(zone.get("lower"), None),
            "center": self._number(zone.get("center"), None),
            "upper": self._number(zone.get("upper"), None),
            "strength": self._number(zone.get("strength"), None),
            "quality": zone.get("quality"),
            "touches": zone.get("touches"),
            "distance_pct": self._number(zone.get("distance_pct"), None),
            "relation": zone.get("relation"),
        }

    def _zone_center(self, zone):
        if not isinstance(zone, dict):
            return None
        return self._number(zone.get("center"), None)

    @staticmethod
    def _zone_type(zone):
        return str(zone.get("type") or "").upper() if isinstance(zone, dict) else ""

    @staticmethod
    def _number(value, default=0.0):
        if value is None:
            return default
        try:
            return float(value)
        except (TypeError, ValueError):
            return default

    @staticmethod
    def _unavailable(reason):
        return {
            "engine": "QMI Technical Price Plan Engine",
            "engine_id": "DE-TA-016.1",
            "version": "0.1.0",
            "status": "insufficient_context",
            "technical_price_plan": {
                "available": False,
                "authorization": "BLOCKED",
                "reason": reason,
            },
        }
