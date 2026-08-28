from __future__ import annotations

from typing import Any


class TechnicalActionService:
    """
    DE-TA-010.0 — Technical Action Framework

    Converts the current Technical Decision Layer and Scenario Engine
    into an auditable action framework.

    IMPORTANT:
    - This is NOT the global QMI Decision Engine.
    - This layer does NOT issue BUY / HOLD / SELL instructions.
    - It defines technical operating constraints and activation gates.
    """

    def analyze(
        self,
        *,
        decision_response: dict[str, Any],
        scenario_response: dict[str, Any],
    ) -> dict[str, Any]:
        decision = decision_response.get("technical_decision") or {}
        scenario_root = scenario_response.get("technical_scenarios") or {}

        posture = decision.get("posture") or {}
        exposure = decision.get("exposure_context") or {}
        readiness = decision.get("readiness") or {}

        direction_score = self._number(
            decision.get("direction_score"),
            0.0,
        )
        confidence = self._number(
            decision.get("confidence"),
            0.0,
        )
        agreement = self._number(
            decision.get("agreement"),
            0.0,
        )
        readiness_score = self._number(
            readiness.get("score"),
            0.0,
        )

        primary = scenario_root.get("primary_scenario") or {}
        secondary = scenario_root.get("secondary_scenario") or {}
        dispersion = scenario_root.get("scenario_dispersion") or {}

        primary_direction = str(
            primary.get("direction") or "NEUTRAL"
        ).upper()
        primary_score = self._number(
            primary.get("plausibility_score"),
            0.0,
        )
        dispersion_state = str(
            dispersion.get("state") or "UNKNOWN"
        ).upper()

        action_posture = self._action_posture(
            direction_score=direction_score,
            readiness_score=readiness_score,
            primary_direction=primary_direction,
            primary_score=primary_score,
        )

        technical_permission = self._technical_permission(
            action_posture=action_posture,
            exposure=exposure,
            confidence=confidence,
            agreement=agreement,
            readiness_score=readiness_score,
            dispersion_state=dispersion_state,
        )

        entry_constraints = self._entry_constraints(
            decision=decision,
            primary=primary,
            secondary=secondary,
            action_posture=action_posture,
        )

        confirmation_gates = self._confirmation_gates(
            decision=decision,
            primary=primary,
            action_posture=action_posture,
        )

        invalidation_gates = self._invalidation_gates(
            primary=primary,
            decision=decision,
        )

        escalation_conditions = self._escalation_conditions(
            decision=decision,
            scenario_root=scenario_root,
        )

        downgrade_conditions = self._downgrade_conditions(
            decision=decision,
            scenario_root=scenario_root,
        )

        action_readiness = self._action_readiness(
            confidence=confidence,
            agreement=agreement,
            readiness_score=readiness_score,
            primary_score=primary_score,
            dispersion_state=dispersion_state,
            confirmation_gates=confirmation_gates,
        )

        return {
            "engine": "QMI Technical Action Framework",
            "engine_id": "DE-TA-010.0",
            "version": "0.1.0",
            "status": "operational",
            "technical_action": {
                "action_posture": action_posture,
                "technical_permission": technical_permission,
                "action_readiness": action_readiness,
                "primary_scenario": {
                    "scenario_id": primary.get("scenario_id"),
                    "name": primary.get("name"),
                    "direction": primary_direction,
                    "plausibility_score": round(primary_score, 1),
                    "plausibility_tier": primary.get(
                        "plausibility_tier"
                    ),
                },
                "secondary_scenario": {
                    "scenario_id": secondary.get("scenario_id"),
                    "name": secondary.get("name"),
                    "direction": secondary.get("direction"),
                    "plausibility_score": secondary.get(
                        "plausibility_score"
                    ),
                    "plausibility_tier": secondary.get(
                        "plausibility_tier"
                    ),
                },
                "entry_constraints": entry_constraints,
                "confirmation_gates": confirmation_gates,
                "invalidation_gates": invalidation_gates,
                "escalation_conditions": escalation_conditions,
                "downgrade_conditions": downgrade_conditions,
                "scope": {
                    "technical_only": True,
                    "global_decision": False,
                    "buy_hold_sell_signal": False,
                    "execution_instruction": False,
                    "note": (
                        "This framework defines technical permissions, "
                        "constraints and activation gates only. Global QMI "
                        "execution decisions require Risk, Portfolio, "
                        "Fundamental and AI/ML layers."
                    ),
                },
            },
        }

    def _action_posture(
        self,
        *,
        direction_score: float,
        readiness_score: float,
        primary_direction: str,
        primary_score: float,
    ) -> dict[str, Any]:
        if primary_direction == "BEARISH":
            if direction_score <= -65 and primary_score >= 75:
                state = "DEFENSIVE_RESTRICTED"
            elif direction_score <= -30:
                state = "DEFENSIVE"
            else:
                state = "CAUTIOUS"
        elif primary_direction == "BULLISH":
            if direction_score >= 65 and primary_score >= 75:
                state = "CONSTRUCTIVE_READY"
            elif direction_score >= 30:
                state = "CONSTRUCTIVE"
            else:
                state = "CAUTIOUS"
        else:
            state = "WAIT_FOR_RESOLUTION"

        if readiness_score < 70:
            state = "WAIT_FOR_CONFIRMATION"

        return {
            "state": state,
            "direction": primary_direction,
            "severity": round(abs(direction_score), 1),
        }

    def _technical_permission(
        self,
        *,
        action_posture: dict[str, Any],
        exposure: dict[str, Any],
        confidence: float,
        agreement: float,
        readiness_score: float,
        dispersion_state: str,
    ) -> dict[str, Any]:
        state = action_posture["state"]

        if state == "DEFENSIVE_RESTRICTED":
            new_long = "BLOCKED_TECHNICALLY"
            add_long = "BLOCKED_TECHNICALLY"
            reduce_risk = "PERMITTED"
            wait = "PREFERRED"
        elif state == "DEFENSIVE":
            new_long = "RESTRICTED"
            add_long = "RESTRICTED"
            reduce_risk = "PERMITTED"
            wait = "PREFERRED"
        elif state == "CONSTRUCTIVE_READY":
            new_long = "PERMITTED_WITH_CONFIRMATION"
            add_long = "PERMITTED_WITH_CONFIRMATION"
            reduce_risk = "OPTIONAL"
            wait = "OPTIONAL"
        elif state == "CONSTRUCTIVE":
            new_long = "CONDITIONAL"
            add_long = "CONDITIONAL"
            reduce_risk = "OPTIONAL"
            wait = "ACCEPTABLE"
        else:
            new_long = "WAIT"
            add_long = "WAIT"
            reduce_risk = "OPTIONAL"
            wait = "PREFERRED"

        return {
            "new_long_exposure": new_long,
            "add_to_existing_long": add_long,
            "risk_reduction": reduce_risk,
            "wait_for_confirmation": wait,
            "existing_long_context": exposure.get(
                "existing_long_exposure"
            ),
            "quality_gate": (
                "HIGH"
                if (
                    confidence >= 85
                    and agreement >= 80
                    and readiness_score >= 85
                    and dispersion_state == "CLEAR_PRIMARY"
                )
                else "MODERATE"
                if readiness_score >= 70
                else "LOW"
            ),
        }

    def _entry_constraints(
        self,
        *,
        decision: dict[str, Any],
        primary: dict[str, Any],
        secondary: dict[str, Any],
        action_posture: dict[str, Any],
    ) -> list[dict[str, Any]]:
        constraints: list[dict[str, Any]] = []

        blockers = (
            decision.get("blockers")
            if isinstance(decision.get("blockers"), list)
            else []
        )

        for blocker in blockers[:4]:
            if not isinstance(blocker, dict):
                continue
            constraints.append({
                "type": "ENGINE_BLOCKER",
                "engine": blocker.get("engine"),
                "severity": blocker.get("severity"),
                "current_score": blocker.get("score"),
                "constraint": blocker.get("reason"),
            })

        if action_posture["direction"] == "BEARISH":
            constraints.append({
                "type": "SCENARIO_CONSTRAINT",
                "engine": "scenario_engine",
                "severity": "HIGH",
                "current_score": primary.get(
                    "plausibility_score"
                ),
                "constraint": (
                    "Primary technical scenario remains bearish; "
                    "new long exposure requires scenario deterioration "
                    "or explicit reversal confirmation."
                ),
            })

        if secondary:
            constraints.append({
                "type": "SECONDARY_SCENARIO",
                "engine": "scenario_engine",
                "severity": "INFORMATIONAL",
                "current_score": secondary.get(
                    "plausibility_score"
                ),
                "constraint": (
                    f"Secondary scenario is "
                    f"{secondary.get('name')}; monitor for transition."
                ),
            })

        return constraints

    def _confirmation_gates(
        self,
        *,
        decision: dict[str, Any],
        primary: dict[str, Any],
        action_posture: dict[str, Any],
    ) -> list[dict[str, Any]]:
        gates: list[dict[str, Any]] = []

        requirements = (
            decision.get("reversal_requirements")
            if isinstance(
                decision.get("reversal_requirements"),
                list,
            )
            else []
        )

        if action_posture["direction"] == "BEARISH":
            for item in requirements[:4]:
                if not isinstance(item, dict):
                    continue
                gates.append({
                    "priority": item.get("priority"),
                    "gate": item.get("requirement"),
                    "engine": item.get("engine"),
                    "current_score": item.get("current_score"),
                    "target": item.get("target"),
                    "status": "OPEN",
                })
        else:
            for index, condition in enumerate(
                primary.get("activation_conditions") or [],
                start=1,
            ):
                gates.append({
                    "priority": index,
                    "gate": "PRIMARY_SCENARIO_CONFIRMATION",
                    "engine": "scenario_engine",
                    "current_score": None,
                    "target": condition,
                    "status": "OPEN",
                })

        return gates

    def _invalidation_gates(
        self,
        *,
        primary: dict[str, Any],
        decision: dict[str, Any],
    ) -> list[dict[str, Any]]:
        conditions = primary.get("invalidation_conditions") or []

        result = []
        for index, condition in enumerate(conditions, start=1):
            result.append({
                "priority": index,
                "condition": condition,
                "status": "MONITOR",
            })

        if not result:
            result.append({
                "priority": 1,
                "condition": (
                    "Primary scenario loses technical dominance."
                ),
                "status": "MONITOR",
            })

        return result

    def _escalation_conditions(
        self,
        *,
        decision: dict[str, Any],
        scenario_root: dict[str, Any],
    ) -> list[str]:
        conditions: list[str] = []

        primary = scenario_root.get("primary_scenario") or {}
        direction = str(
            primary.get("direction") or "NEUTRAL"
        ).upper()

        if direction == "BEARISH":
            conditions.extend([
                "Primary bearish scenario plausibility increases",
                "Fresh bearish BOS / structural deterioration",
                "Momentum re-accelerates bearish",
                "Liquidity pressure strengthens bearish",
            ])
        elif direction == "BULLISH":
            conditions.extend([
                "Primary bullish scenario plausibility increases",
                "Bullish structure remains confirmed",
                "Momentum accelerates bullish",
                "Liquidity confirms upside acceptance",
            ])
        else:
            conditions.extend([
                "Scenario dispersion widens",
                "Directional score exits neutral regime",
            ])

        return conditions

    def _downgrade_conditions(
        self,
        *,
        decision: dict[str, Any],
        scenario_root: dict[str, Any],
    ) -> list[str]:
        conditions: list[str] = []

        primary = scenario_root.get("primary_scenario") or {}
        secondary = scenario_root.get("secondary_scenario") or {}

        if primary:
            conditions.append(
                "Primary scenario plausibility materially weakens"
            )

        if secondary:
            conditions.append(
                "Secondary scenario begins converging on primary"
            )

        conditions.extend([
            "Decision confidence falls below 70%",
            "Decision readiness falls below 70%",
            "Material cross-engine conflicts emerge",
        ])

        return conditions

    def _action_readiness(
        self,
        *,
        confidence: float,
        agreement: float,
        readiness_score: float,
        primary_score: float,
        dispersion_state: str,
        confirmation_gates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        dispersion_bonus = (
            8.0
            if dispersion_state == "CLEAR_PRIMARY"
            else 3.0
            if dispersion_state == "MODERATE_SEPARATION"
            else 0.0
        )

        open_gate_penalty = min(
            15.0,
            len(confirmation_gates) * 2.0,
        )

        score = (
            confidence * 0.30
            + agreement * 0.25
            + readiness_score * 0.25
            + primary_score * 0.20
            + dispersion_bonus
            - open_gate_penalty
        )

        score = max(0.0, min(100.0, score))

        if score >= 85:
            state = "HIGH"
        elif score >= 70:
            state = "MODERATE"
        else:
            state = "LOW"

        return {
            "score": round(score, 1),
            "state": state,
            "open_confirmation_gates": len(
                confirmation_gates
            ),
            "dispersion_state": dispersion_state,
        }

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)
