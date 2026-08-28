from __future__ import annotations

from typing import Any


class TechnicalRiskExposureService:
    """
    DE-TA-011.0 — Technical Risk & Exposure Gate

    Converts the Technical Action Framework into a technical-only
    exposure and risk envelope.

    IMPORTANT:
    - This is NOT final portfolio position sizing.
    - This does NOT issue BUY / HOLD / SELL.
    - Exposure bands are technical permissions only.
    - Final sizing requires portfolio, risk-budget and capital inputs.
    """

    def analyze(
        self,
        *,
        action_response: dict[str, Any],
        decision_response: dict[str, Any],
        scenario_response: dict[str, Any],
    ) -> dict[str, Any]:
        action = action_response.get("technical_action") or {}
        decision = decision_response.get("technical_decision") or {}
        scenarios = scenario_response.get("technical_scenarios") or {}

        action_posture = action.get("action_posture") or {}
        permissions = action.get("technical_permission") or {}
        action_readiness = action.get("action_readiness") or {}
        decision_posture = decision.get("posture") or {}
        risk_flags = decision.get("risk_flags") or []

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
            action_readiness.get("score"),
            0.0,
        )

        primary = scenarios.get("primary_scenario") or {}
        secondary = scenarios.get("secondary_scenario") or {}
        dispersion = scenarios.get("scenario_dispersion") or {}

        primary_score = self._number(
            primary.get("plausibility_score"),
            0.0,
        )
        secondary_score = self._number(
            secondary.get("plausibility_score"),
            0.0,
        )
        dispersion_spread = self._number(
            dispersion.get("spread"),
            max(0.0, primary_score - secondary_score),
        )

        risk_score = self._risk_score(
            direction_score=direction_score,
            confidence=confidence,
            agreement=agreement,
            readiness_score=readiness_score,
            primary_score=primary_score,
            dispersion_spread=dispersion_spread,
            risk_flags=risk_flags,
            action_posture=action_posture,
        )

        risk_regime = self._risk_regime(risk_score)

        exposure_gate = self._exposure_gate(
            permissions=permissions,
            action_posture=action_posture,
            risk_regime=risk_regime,
            direction_score=direction_score,
        )

        technical_budget = self._technical_budget(
            exposure_gate=exposure_gate,
            risk_score=risk_score,
            primary=primary,
            dispersion=dispersion,
        )

        protective_controls = self._protective_controls(
            action=action,
            decision=decision,
            risk_regime=risk_regime,
        )

        release_conditions = self._release_conditions(
            action=action,
            decision=decision,
            scenarios=scenarios,
        )

        escalation_conditions = self._escalation_conditions(
            action=action,
            decision=decision,
            scenarios=scenarios,
        )

        return {
            "engine": "QMI Technical Risk & Exposure Gate",
            "engine_id": "DE-TA-011.0",
            "version": "0.1.0",
            "status": "operational",
            "technical_risk_exposure": {
                "risk_regime": {
                    "state": risk_regime,
                    "score": round(risk_score, 1),
                    "directional_state": decision_posture.get(
                        "directional_state"
                    ),
                    "action_state": action_posture.get("state"),
                },
                "exposure_gate": exposure_gate,
                "technical_budget": technical_budget,
                "protective_controls": protective_controls,
                "release_conditions": release_conditions,
                "escalation_conditions": escalation_conditions,
                "source_context": {
                    "direction_score": round(direction_score, 1),
                    "decision_confidence": round(confidence, 1),
                    "agreement": round(agreement, 1),
                    "action_readiness": round(readiness_score, 1),
                    "primary_scenario": primary.get("name"),
                    "primary_scenario_score": round(
                        primary_score, 1
                    ),
                    "scenario_dispersion": round(
                        dispersion_spread, 1
                    ),
                },
                "scope": {
                    "technical_only": True,
                    "portfolio_sizing": False,
                    "capital_allocation": False,
                    "execution_instruction": False,
                    "buy_hold_sell_signal": False,
                    "note": (
                        "Exposure bands express technical permission only. "
                        "Final position sizing requires portfolio-level "
                        "risk budget, concentration and capital constraints."
                    ),
                },
            },
        }

    def _risk_score(
        self,
        *,
        direction_score: float,
        confidence: float,
        agreement: float,
        readiness_score: float,
        primary_score: float,
        dispersion_spread: float,
        risk_flags: list[Any],
        action_posture: dict[str, Any],
    ) -> float:
        downside = max(0.0, -direction_score)
        directional_risk = downside * 0.34

        conviction_risk = (
            confidence * 0.16
            + agreement * 0.12
            + readiness_score * 0.10
        )

        scenario_risk = primary_score * 0.18
        clarity_risk = min(100.0, dispersion_spread) * 0.10

        flag_penalty = 0.0
        for flag in risk_flags:
            if not isinstance(flag, dict):
                continue
            severity = str(flag.get("severity") or "").upper()
            if severity in {"VERY_HIGH", "CRITICAL"}:
                flag_penalty += 7.0
            elif severity == "HIGH":
                flag_penalty += 5.0
            elif severity == "MODERATE":
                flag_penalty += 2.5
            elif severity == "LOW":
                flag_penalty += 1.0

        state = str(
            action_posture.get("state") or ""
        ).upper()

        posture_penalty = (
            8.0
            if state == "DEFENSIVE_RESTRICTED"
            else 5.0
            if state == "DEFENSIVE"
            else 0.0
        )

        score = (
            directional_risk
            + conviction_risk
            + scenario_risk
            + clarity_risk
            + flag_penalty
            + posture_penalty
        )

        return max(0.0, min(100.0, score))

    def _risk_regime(self, score: float) -> str:
        if score >= 85:
            return "CRITICAL"
        if score >= 70:
            return "HIGH"
        if score >= 50:
            return "ELEVATED"
        if score >= 30:
            return "MODERATE"
        return "LOW"

    def _exposure_gate(
        self,
        *,
        permissions: dict[str, Any],
        action_posture: dict[str, Any],
        risk_regime: str,
        direction_score: float,
    ) -> dict[str, Any]:
        new_long_permission = str(
            permissions.get("new_long_exposure") or "WAIT"
        ).upper()

        add_long_permission = str(
            permissions.get("add_to_existing_long") or "WAIT"
        ).upper()

        if new_long_permission == "BLOCKED_TECHNICALLY":
            new_long_band = "0%"
        elif new_long_permission == "RESTRICTED":
            new_long_band = "0-10%"
        elif new_long_permission in {
            "CONDITIONAL",
            "PERMITTED_WITH_CONFIRMATION",
        }:
            new_long_band = "0-25%"
        else:
            new_long_band = "0-15%"

        if add_long_permission == "BLOCKED_TECHNICALLY":
            add_long_band = "0%"
        elif add_long_permission == "RESTRICTED":
            add_long_band = "0-10%"
        elif add_long_permission in {
            "CONDITIONAL",
            "PERMITTED_WITH_CONFIRMATION",
        }:
            add_long_band = "0-20%"
        else:
            add_long_band = "0-10%"

        if risk_regime in {"HIGH", "CRITICAL"}:
            tactical_bias = "CAPITAL_PRESERVATION"
        elif direction_score < -20:
            tactical_bias = "DEFENSIVE"
        elif direction_score > 20:
            tactical_bias = "SELECTIVE_RISK_ON"
        else:
            tactical_bias = "NEUTRAL"

        return {
            "new_long_permission": new_long_permission,
            "new_long_technical_band": new_long_band,
            "add_long_permission": add_long_permission,
            "add_long_technical_band": add_long_band,
            "risk_reduction_permission": permissions.get(
                "risk_reduction"
            ),
            "wait_preference": permissions.get(
                "wait_for_confirmation"
            ),
            "tactical_bias": tactical_bias,
            "technical_leverage": "PROHIBITED"
            if risk_regime in {"HIGH", "CRITICAL"}
            else "NOT_EVALUATED",
        }

    def _technical_budget(
        self,
        *,
        exposure_gate: dict[str, Any],
        risk_score: float,
        primary: dict[str, Any],
        dispersion: dict[str, Any],
    ) -> dict[str, Any]:
        if risk_score >= 85:
            gross_band = "0-15%"
        elif risk_score >= 70:
            gross_band = "0-25%"
        elif risk_score >= 50:
            gross_band = "0-40%"
        elif risk_score >= 30:
            gross_band = "0-60%"
        else:
            gross_band = "0-80%"

        return {
            "technical_gross_exposure_band": gross_band,
            "capital_preservation_priority": (
                "VERY_HIGH"
                if risk_score >= 85
                else "HIGH"
                if risk_score >= 70
                else "MODERATE"
                if risk_score >= 50
                else "NORMAL"
            ),
            "primary_scenario_direction": primary.get(
                "direction"
            ),
            "scenario_clarity": dispersion.get("state"),
            "note": (
                "This band is an upper technical envelope, not a "
                "portfolio allocation recommendation."
            ),
        }

    def _protective_controls(
        self,
        *,
        action: dict[str, Any],
        decision: dict[str, Any],
        risk_regime: str,
    ) -> list[dict[str, Any]]:
        controls: list[dict[str, Any]] = []

        controls.append({
            "control": "NEW_LONG_GATE",
            "state": (
                "HARD_BLOCK"
                if risk_regime in {"HIGH", "CRITICAL"}
                else "CONDITIONAL"
            ),
            "reason": (
                "Technical risk regime requires confirmation before "
                "new long exposure."
            ),
        })

        controls.append({
            "control": "AVERAGING_DOWN",
            "state": "PROHIBITED"
            if risk_regime in {"HIGH", "CRITICAL"}
            else "RESTRICTED",
            "reason": (
                "Do not increase directional exposure while the "
                "technical risk envelope remains adverse."
            ),
        })

        controls.append({
            "control": "LEVERAGE",
            "state": "PROHIBITED",
            "reason": (
                "Technical leverage is not permitted by this layer."
            ),
        })

        invalidation = action.get("invalidation_gates") or []
        if invalidation:
            controls.append({
                "control": "INVALIDATION_MONITOR",
                "state": "ACTIVE",
                "reason": (
                    f"{len(invalidation)} invalidation conditions "
                    "are under active monitoring."
                ),
            })

        return controls

    def _release_conditions(
        self,
        *,
        action: dict[str, Any],
        decision: dict[str, Any],
        scenarios: dict[str, Any],
    ) -> list[str]:
        conditions: list[str] = []

        gates = action.get("confirmation_gates") or []
        for gate in gates[:4]:
            if not isinstance(gate, dict):
                continue
            requirement = gate.get("gate")
            target = gate.get("target")
            if requirement and target:
                conditions.append(
                    f"{requirement}: {target}"
                )

        conditions.extend([
            "Action posture improves from defensive regime",
            "Primary bearish scenario materially weakens",
            "Risk flags de-escalate",
        ])

        return conditions

    def _escalation_conditions(
        self,
        *,
        action: dict[str, Any],
        decision: dict[str, Any],
        scenarios: dict[str, Any],
    ) -> list[str]:
        conditions = list(
            action.get("escalation_conditions") or []
        )

        conditions.extend([
            "Risk regime reaches CRITICAL",
            "Fresh structural deterioration confirms",
            "Scenario dispersion increases in bearish direction",
        ])

        return conditions

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)
