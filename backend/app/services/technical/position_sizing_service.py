from __future__ import annotations

from typing import Any


class TechnicalPositionSizingService:
    """
    DE-TA-012.0 — Technical Position Sizing & Capital Allocation

    Converts the technical risk/exposure envelope into a technical-only
    allocation framework.

    IMPORTANT:
    - This is NOT final portfolio position sizing.
    - This does NOT use account equity, portfolio concentration or cash.
    - This does NOT issue BUY / HOLD / SELL.
    - All allocation bands are technical permission envelopes only.
    """

    def analyze(
        self,
        *,
        risk_exposure_response: dict[str, Any],
        action_response: dict[str, Any],
        decision_response: dict[str, Any],
        scenario_response: dict[str, Any],
    ) -> dict[str, Any]:
        risk_root = (
            risk_exposure_response.get("technical_risk_exposure") or {}
        )
        action = action_response.get("technical_action") or {}
        decision = decision_response.get("technical_decision") or {}
        scenarios = scenario_response.get("technical_scenarios") or {}

        risk_regime = risk_root.get("risk_regime") or {}
        exposure_gate = risk_root.get("exposure_gate") or {}
        technical_budget = risk_root.get("technical_budget") or {}
        source_context = risk_root.get("source_context") or {}

        risk_state = str(risk_regime.get("state") or "UNKNOWN").upper()
        risk_score = self._number(risk_regime.get("score"), 0.0)
        direction_score = self._number(
            source_context.get("direction_score"),
            decision.get("direction_score"),
        )
        action_readiness = self._number(
            source_context.get("action_readiness"),
            (action.get("action_readiness") or {}).get("score"),
        )

        primary = scenarios.get("primary_scenario") or {}
        primary_direction = str(
            primary.get("direction") or "NEUTRAL"
        ).upper()
        primary_score = self._number(
            primary.get("plausibility_score"),
            0.0,
        )

        allocation_regime = self._allocation_regime(
            risk_state=risk_state,
            primary_direction=primary_direction,
            direction_score=direction_score,
        )

        max_technical_exposure = self._max_technical_exposure(
            technical_budget=technical_budget,
            risk_state=risk_state,
        )

        entry_allocation = self._entry_allocation(
            exposure_gate=exposure_gate,
            risk_state=risk_state,
        )

        add_on_capacity = self._add_on_capacity(
            exposure_gate=exposure_gate,
            risk_state=risk_state,
        )

        cash_preference = self._cash_preference(
            risk_state=risk_state,
            allocation_regime=allocation_regime,
        )

        sizing_confidence = self._sizing_confidence(
            risk_score=risk_score,
            action_readiness=action_readiness,
            primary_score=primary_score,
        )

        reduction_policy = self._reduction_policy(
            exposure_gate=exposure_gate,
            risk_state=risk_state,
        )

        return {
            "engine": "QMI Technical Position Sizing & Capital Allocation",
            "engine_id": "DE-TA-012.0",
            "version": "0.1.0",
            "status": "operational",
            "technical_position_sizing": {
                "allocation_regime": allocation_regime,
                "maximum_technical_exposure": max_technical_exposure,
                "new_entry_allocation": entry_allocation,
                "add_on_capacity": add_on_capacity,
                "risk_reduction": reduction_policy,
                "cash_preference": cash_preference,
                "leverage": exposure_gate.get(
                    "technical_leverage",
                    "NOT_EVALUATED",
                ),
                "sizing_confidence": sizing_confidence,
                "source_context": {
                    "risk_state": risk_state,
                    "risk_score": round(risk_score, 1),
                    "direction_score": round(direction_score, 1),
                    "action_readiness": round(action_readiness, 1),
                    "primary_scenario": primary.get("name"),
                    "primary_direction": primary_direction,
                    "primary_score": round(primary_score, 1),
                },
                "scope": {
                    "technical_only": True,
                    "portfolio_equity_used": False,
                    "portfolio_concentration_used": False,
                    "cash_balance_used": False,
                    "execution_instruction": False,
                    "buy_hold_sell_signal": False,
                    "note": (
                        "This engine produces technical allocation envelopes "
                        "only. Final position sizing requires portfolio-level "
                        "capital, concentration and risk-budget inputs."
                    ),
                },
            },
        }

    def _allocation_regime(
        self,
        *,
        risk_state: str,
        primary_direction: str,
        direction_score: float,
    ) -> dict[str, Any]:
        if risk_state in {"CRITICAL", "HIGH"}:
            state = "CAPITAL_PRESERVATION"
        elif primary_direction == "BEARISH" or direction_score < -20:
            state = "DEFENSIVE_ALLOCATION"
        elif primary_direction == "BULLISH" and direction_score > 20:
            state = "SELECTIVE_RISK_ON"
        else:
            state = "NEUTRAL_ALLOCATION"

        return {
            "state": state,
            "priority": (
                "VERY_HIGH"
                if risk_state == "CRITICAL"
                else "HIGH"
                if risk_state == "HIGH"
                else "MODERATE"
            ),
        }

    def _max_technical_exposure(
        self,
        *,
        technical_budget: dict[str, Any],
        risk_state: str,
    ) -> dict[str, Any]:
        band = technical_budget.get("technical_gross_exposure_band")

        if not band:
            band = (
                "0-15%"
                if risk_state == "CRITICAL"
                else "0-25%"
                if risk_state == "HIGH"
                else "0-40%"
                if risk_state == "ELEVATED"
                else "0-60%"
            )

        return {
            "band": band,
            "type": "UPPER_TECHNICAL_ENVELOPE",
            "capital_preservation_priority": technical_budget.get(
                "capital_preservation_priority"
            ),
        }

    def _entry_allocation(
        self,
        *,
        exposure_gate: dict[str, Any],
        risk_state: str,
    ) -> dict[str, Any]:
        permission = str(
            exposure_gate.get("new_long_permission") or "WAIT"
        ).upper()

        band = exposure_gate.get("new_long_technical_band") or "0%"

        if permission == "BLOCKED_TECHNICALLY":
            recommended_band = "0%"
            state = "NO_NEW_ENTRY"
        elif permission == "RESTRICTED":
            recommended_band = band
            state = "MINIMAL_ONLY"
        elif permission in {
            "CONDITIONAL",
            "PERMITTED_WITH_CONFIRMATION",
        }:
            recommended_band = band
            state = "CONDITIONAL_ENTRY"
        else:
            recommended_band = band
            state = "WAIT"

        return {
            "state": state,
            "permission": permission,
            "technical_band": recommended_band,
        }

    def _add_on_capacity(
        self,
        *,
        exposure_gate: dict[str, Any],
        risk_state: str,
    ) -> dict[str, Any]:
        permission = str(
            exposure_gate.get("add_long_permission") or "WAIT"
        ).upper()

        band = exposure_gate.get("add_long_technical_band") or "0%"

        if permission == "BLOCKED_TECHNICALLY":
            state = "NO_ADD_ON"
            capacity = "0%"
        elif permission == "RESTRICTED":
            state = "RESTRICTED"
            capacity = band
        elif permission in {
            "CONDITIONAL",
            "PERMITTED_WITH_CONFIRMATION",
        }:
            state = "CONDITIONAL"
            capacity = band
        else:
            state = "WAIT"
            capacity = band

        return {
            "state": state,
            "permission": permission,
            "technical_band": capacity,
        }

    def _cash_preference(
        self,
        *,
        risk_state: str,
        allocation_regime: dict[str, Any],
    ) -> dict[str, Any]:
        if risk_state == "CRITICAL":
            state = "VERY_HIGH"
        elif risk_state == "HIGH":
            state = "HIGH"
        elif risk_state == "ELEVATED":
            state = "MODERATE_HIGH"
        elif allocation_regime["state"] == "SELECTIVE_RISK_ON":
            state = "MODERATE"
        else:
            state = "NORMAL"

        return {
            "state": state,
            "rationale": allocation_regime["state"],
        }

    def _sizing_confidence(
        self,
        *,
        risk_score: float,
        action_readiness: float,
        primary_score: float,
    ) -> dict[str, Any]:
        score = (
            min(100.0, risk_score) * 0.35
            + min(100.0, action_readiness) * 0.35
            + min(100.0, primary_score) * 0.30
        )

        if score >= 85:
            state = "HIGH"
        elif score >= 70:
            state = "MODERATE"
        else:
            state = "LOW"

        return {
            "score": round(score, 1),
            "state": state,
        }

    def _reduction_policy(
        self,
        *,
        exposure_gate: dict[str, Any],
        risk_state: str,
    ) -> dict[str, Any]:
        permission = exposure_gate.get(
            "risk_reduction_permission",
            "OPTIONAL",
        )

        if str(permission).upper() == "PERMITTED":
            preference = (
                "HIGH"
                if risk_state in {"CRITICAL", "HIGH"}
                else "MODERATE"
            )
        else:
            preference = "LOW"

        return {
            "permission": permission,
            "preference": preference,
        }

    @staticmethod
    def _number(value: Any, default: Any) -> float:
        try:
            if value is None:
                return float(default or 0.0)
            return float(value)
        except (TypeError, ValueError):
            try:
                return float(default or 0.0)
            except (TypeError, ValueError):
                return 0.0
