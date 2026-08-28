from __future__ import annotations

from typing import Any


class TechnicalExecutionPlanService:
    """
    DE-TA-013.0 — Technical Execution Plan

    Converts the full technical decision pipeline into a conditional
    execution playbook.

    IMPORTANT:
    - This does NOT place orders.
    - This does NOT use broker connectivity.
    - This does NOT use final portfolio capital.
    - Actions are technical states and conditions only.
    """

    def analyze(
        self,
        *,
        sizing_response: dict[str, Any],
        risk_response: dict[str, Any],
        action_response: dict[str, Any],
        decision_response: dict[str, Any],
        scenario_response: dict[str, Any],
    ) -> dict[str, Any]:
        sizing = sizing_response.get("technical_position_sizing") or {}
        risk = risk_response.get("technical_risk_exposure") or {}
        action = action_response.get("technical_action") or {}
        decision = decision_response.get("technical_decision") or {}
        scenarios = scenario_response.get("technical_scenarios") or {}

        allocation = sizing.get("allocation_regime") or {}
        max_exposure = sizing.get("maximum_technical_exposure") or {}
        new_entry = sizing.get("new_entry_allocation") or {}
        add_on = sizing.get("add_on_capacity") or {}
        reduction = sizing.get("risk_reduction") or {}
        cash_pref = sizing.get("cash_preference") or {}
        sizing_conf = sizing.get("sizing_confidence") or {}

        risk_regime = risk.get("risk_regime") or {}
        exposure_gate = risk.get("exposure_gate") or {}
        action_posture = action.get("action_posture") or {}
        action_readiness = action.get("action_readiness") or {}

        primary = scenarios.get("primary_scenario") or {}
        secondary = scenarios.get("secondary_scenario") or {}

        direction_score = self._number(
            decision.get("direction_score"),
            0.0,
        )
        decision_confidence = self._number(
            decision.get("confidence"),
            0.0,
        )
        action_readiness_score = self._number(
            action_readiness.get("score"),
            0.0,
        )
        sizing_confidence_score = self._number(
            sizing_conf.get("score"),
            0.0,
        )
        risk_score = self._number(
            risk_regime.get("score"),
            0.0,
        )

        execution_state = self._execution_state(
            allocation_state=str(allocation.get("state") or ""),
            new_entry_state=str(new_entry.get("state") or ""),
            add_on_state=str(add_on.get("state") or ""),
            risk_state=str(risk_regime.get("state") or ""),
            direction_score=direction_score,
        )

        action_matrix = self._action_matrix(
            execution_state=execution_state,
            new_entry=new_entry,
            add_on=add_on,
            reduction=reduction,
            exposure_gate=exposure_gate,
        )

        activation_conditions = self._activation_conditions(
            action=action,
            risk=risk,
            scenarios=scenarios,
        )

        invalidation_conditions = self._invalidation_conditions(
            action=action,
            scenarios=scenarios,
        )

        escalation_path = self._escalation_path(
            execution_state=execution_state,
            scenarios=scenarios,
            risk=risk,
        )

        deescalation_path = self._deescalation_path(
            action=action,
            risk=risk,
            scenarios=scenarios,
        )

        execution_confidence = self._execution_confidence(
            decision_confidence=decision_confidence,
            action_readiness=action_readiness_score,
            sizing_confidence=sizing_confidence_score,
            risk_score=risk_score,
        )

        return {
            "engine": "QMI Technical Execution Plan",
            "engine_id": "DE-TA-013.0",
            "version": "0.1.0",
            "status": "operational",
            "technical_execution_plan": {
                "execution_state": execution_state,
                "action_matrix": action_matrix,
                "allocation_context": {
                    "allocation_regime": allocation.get("state"),
                    "maximum_technical_exposure": max_exposure.get("band"),
                    "cash_preference": cash_pref.get("state"),
                    "leverage": sizing.get("leverage"),
                },
                "activation_conditions": activation_conditions,
                "invalidation_conditions": invalidation_conditions,
                "escalation_path": escalation_path,
                "deescalation_path": deescalation_path,
                "execution_confidence": execution_confidence,
                "source_context": {
                    "direction_score": round(direction_score, 1),
                    "decision_confidence": round(decision_confidence, 1),
                    "action_readiness": round(action_readiness_score, 1),
                    "sizing_confidence": round(sizing_confidence_score, 1),
                    "risk_state": risk_regime.get("state"),
                    "risk_score": round(risk_score, 1),
                    "primary_scenario": primary.get("name"),
                    "primary_score": primary.get("plausibility_score"),
                    "secondary_scenario": secondary.get("name"),
                    "secondary_score": secondary.get("plausibility_score"),
                    "action_posture": action_posture.get("state"),
                },
                "scope": {
                    "technical_only": True,
                    "broker_execution": False,
                    "portfolio_capital_used": False,
                    "position_quantity_calculated": False,
                    "automatic_orders": False,
                    "note": (
                        "This engine creates a conditional technical execution "
                        "playbook only. Final order sizing and execution require "
                        "portfolio capital, broker integration and user-defined "
                        "risk controls."
                    ),
                },
            },
        }

    def _execution_state(
        self,
        *,
        allocation_state: str,
        new_entry_state: str,
        add_on_state: str,
        risk_state: str,
        direction_score: float,
    ) -> dict[str, Any]:
        allocation_state = allocation_state.upper()
        new_entry_state = new_entry_state.upper()
        add_on_state = add_on_state.upper()
        risk_state = risk_state.upper()

        if (
            risk_state == "CRITICAL"
            or allocation_state == "CAPITAL_PRESERVATION"
            or new_entry_state == "NO_NEW_ENTRY"
        ):
            state = "WAIT_DEFENSIVE"
            bias = "CAPITAL_PRESERVATION"
        elif direction_score <= -30:
            state = "WAIT_FOR_REVERSAL"
            bias = "DEFENSIVE"
        elif direction_score >= 30 and new_entry_state == "CONDITIONAL_ENTRY":
            state = "READY_ON_CONFIRMATION"
            bias = "SELECTIVE_RISK_ON"
        elif direction_score >= 30:
            state = "TACTICAL_ENTRY_ALLOWED"
            bias = "CONSTRUCTIVE"
        else:
            state = "WAIT_FOR_RESOLUTION"
            bias = "NEUTRAL"

        return {
            "state": state,
            "bias": bias,
            "risk_state": risk_state,
        }

    def _action_matrix(
        self,
        *,
        execution_state: dict[str, Any],
        new_entry: dict[str, Any],
        add_on: dict[str, Any],
        reduction: dict[str, Any],
        exposure_gate: dict[str, Any],
    ) -> dict[str, Any]:
        state = execution_state["state"]

        if state == "WAIT_DEFENSIVE":
            enter = "BLOCKED"
            add = "BLOCKED"
            wait = "PRIMARY"
            reduce = (
                "PERMITTED"
                if str(reduction.get("permission") or "").upper() == "PERMITTED"
                else "OPTIONAL"
            )
            exit_state = "CONDITIONAL"
        elif state == "READY_ON_CONFIRMATION":
            enter = "CONDITIONAL"
            add = "CONDITIONAL"
            wait = "UNTIL_CONFIRMATION"
            reduce = "OPTIONAL"
            exit_state = "CONDITIONAL"
        elif state == "TACTICAL_ENTRY_ALLOWED":
            enter = "PERMITTED"
            add = "CONDITIONAL"
            wait = "OPTIONAL"
            reduce = "OPTIONAL"
            exit_state = "CONDITIONAL"
        else:
            enter = "WAIT"
            add = "WAIT"
            wait = "PRIMARY"
            reduce = "OPTIONAL"
            exit_state = "CONDITIONAL"

        return {
            "WAIT": {
                "state": wait,
                "priority": "HIGH" if wait == "PRIMARY" else "MODERATE",
            },
            "ENTER": {
                "state": enter,
                "technical_band": new_entry.get("technical_band"),
            },
            "ADD": {
                "state": add,
                "technical_band": add_on.get("technical_band"),
            },
            "REDUCE": {
                "state": reduce,
                "preference": reduction.get("preference"),
            },
            "EXIT": {
                "state": exit_state,
                "trigger": "Technical invalidation / risk escalation",
            },
        }

    def _activation_conditions(
        self,
        *,
        action: dict[str, Any],
        risk: dict[str, Any],
        scenarios: dict[str, Any],
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []

        gates = action.get("confirmation_gates") or []
        for gate in gates[:4]:
            if not isinstance(gate, dict):
                continue
            result.append({
                "priority": gate.get("priority"),
                "condition": gate.get("gate"),
                "target": gate.get("target"),
                "status": gate.get("status", "OPEN"),
                "engine": gate.get("engine"),
            })

        for condition in (risk.get("release_conditions") or [])[:3]:
            if not any(
                item.get("target") == condition
                for item in result
            ):
                result.append({
                    "priority": None,
                    "condition": "RISK_RELEASE",
                    "target": condition,
                    "status": "OPEN",
                    "engine": "risk_exposure",
                })

        return result

    def _invalidation_conditions(
        self,
        *,
        action: dict[str, Any],
        scenarios: dict[str, Any],
    ) -> list[dict[str, Any]]:
        result: list[dict[str, Any]] = []

        for item in action.get("invalidation_gates") or []:
            if isinstance(item, dict):
                result.append({
                    "priority": item.get("priority"),
                    "condition": item.get("condition"),
                    "status": item.get("status", "MONITOR"),
                })

        primary = scenarios.get("primary_scenario") or {}
        for condition in primary.get("invalidation_conditions") or []:
            if not any(
                row.get("condition") == condition
                for row in result
            ):
                result.append({
                    "priority": None,
                    "condition": condition,
                    "status": "MONITOR",
                })

        return result

    def _escalation_path(
        self,
        *,
        execution_state: dict[str, Any],
        scenarios: dict[str, Any],
        risk: dict[str, Any],
    ) -> list[str]:
        primary = scenarios.get("primary_scenario") or {}
        direction = str(primary.get("direction") or "").upper()

        path = list(risk.get("escalation_conditions") or [])

        if direction == "BEARISH":
            path.extend([
                "Fresh bearish BOS confirms",
                "Primary bearish scenario strengthens",
                "Risk remains HIGH / CRITICAL",
            ])

        return self._unique(path)

    def _deescalation_path(
        self,
        *,
        action: dict[str, Any],
        risk: dict[str, Any],
        scenarios: dict[str, Any],
    ) -> list[str]:
        path = list(risk.get("release_conditions") or [])

        path.extend([
            "Action posture improves",
            "Primary bearish scenario weakens",
            "Secondary stabilization scenario strengthens",
            "Risk regime falls below HIGH",
        ])

        return self._unique(path)

    def _execution_confidence(
        self,
        *,
        decision_confidence: float,
        action_readiness: float,
        sizing_confidence: float,
        risk_score: float,
    ) -> dict[str, Any]:
        score = (
            decision_confidence * 0.30
            + action_readiness * 0.25
            + sizing_confidence * 0.25
            + min(100.0, risk_score) * 0.20
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

    @staticmethod
    def _unique(items: list[Any]) -> list[str]:
        seen: set[str] = set()
        result: list[str] = []

        for item in items:
            text = str(item)
            if text not in seen:
                seen.add(text)
                result.append(text)

        return result

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
