from __future__ import annotations

from typing import Any


class TechnicalStateTransitionService:
    """
    DE-TA-014.0 — Technical Monitoring & State Transition Engine

    Converts the current technical execution context into a state-machine
    representation and transition watchlist.

    This version establishes the deterministic state machine and transition
    logic. Persistent historical state tracking can be added in DE-TA-014.1.
    """

    STATE_ORDER = [
        "WAIT_DEFENSIVE",
        "STABILIZING",
        "WATCH_REVERSAL",
        "ENTRY_ELIGIBLE",
        "CONSTRUCTIVE",
    ]

    def analyze(
        self,
        *,
        execution_response: dict[str, Any],
        sizing_response: dict[str, Any],
        risk_response: dict[str, Any],
        action_response: dict[str, Any],
        decision_response: dict[str, Any],
        scenario_response: dict[str, Any],
    ) -> dict[str, Any]:
        execution = (
            execution_response.get("technical_execution_plan") or {}
        )
        sizing = sizing_response.get("technical_position_sizing") or {}
        risk = risk_response.get("technical_risk_exposure") or {}
        action = action_response.get("technical_action") or {}
        decision = decision_response.get("technical_decision") or {}
        scenarios = scenario_response.get("technical_scenarios") or {}

        execution_state = execution.get("execution_state") or {}
        action_matrix = execution.get("action_matrix") or {}
        execution_confidence = execution.get("execution_confidence") or {}

        risk_regime = risk.get("risk_regime") or {}
        sizing_conf = sizing.get("sizing_confidence") or {}
        action_readiness = action.get("action_readiness") or {}

        primary = scenarios.get("primary_scenario") or {}
        secondary = scenarios.get("secondary_scenario") or {}

        direction_score = self._number(
            decision.get("direction_score"), 0.0
        )
        risk_score = self._number(
            risk_regime.get("score"), 0.0
        )
        exec_conf = self._number(
            execution_confidence.get("score"), 0.0
        )
        sizing_conf_score = self._number(
            sizing_conf.get("score"), 0.0
        )
        readiness_score = self._number(
            action_readiness.get("score"), 0.0
        )
        primary_score = self._number(
            primary.get("plausibility_score"), 0.0
        )
        secondary_score = self._number(
            secondary.get("plausibility_score"), 0.0
        )

        current_state = self._derive_state(
            execution_state=execution_state,
            action_matrix=action_matrix,
            risk_state=str(risk_regime.get("state") or ""),
            direction_score=direction_score,
            primary=primary,
            secondary=secondary,
        )

        state_score = self._state_score(
            current_state=current_state,
            direction_score=direction_score,
            risk_score=risk_score,
            primary_score=primary_score,
            secondary_score=secondary_score,
            readiness_score=readiness_score,
        )

        transition_candidates = self._transition_candidates(
            current_state=current_state,
            direction_score=direction_score,
            risk_score=risk_score,
            primary=primary,
            secondary=secondary,
            action=action,
            execution=execution,
        )

        next_state = (
            transition_candidates[0]
            if transition_candidates
            else {
                "state": current_state,
                "probability": 100.0,
                "status": "HOLD_STATE",
                "requirements": [],
            }
        )

        watchlist = self._watchlist(
            current_state=current_state,
            transition_candidates=transition_candidates,
            execution=execution,
            risk=risk,
            action=action,
        )

        transition_readiness = self._transition_readiness(
            current_state=current_state,
            next_state=next_state,
            direction_score=direction_score,
            risk_score=risk_score,
            readiness_score=readiness_score,
            exec_conf=exec_conf,
            sizing_conf=sizing_conf_score,
        )

        return {
            "engine": "QMI Technical Monitoring & State Transition Engine",
            "engine_id": "DE-TA-014.0",
            "version": "0.1.0",
            "status": "operational",
            "technical_state_transition": {
                "current_state": {
                    "state": current_state,
                    "state_score": round(state_score, 1),
                    "execution_state": execution_state.get("state"),
                    "risk_state": risk_regime.get("state"),
                },
                "next_state_candidate": next_state,
                "transition_readiness": transition_readiness,
                "transition_candidates": transition_candidates,
                "watchlist": watchlist,
                "state_machine": {
                    "states": self.STATE_ORDER,
                    "current_index": self.STATE_ORDER.index(current_state),
                    "persistent_history": False,
                    "persistence_target": "DE-TA-014.1",
                },
                "source_context": {
                    "direction_score": round(direction_score, 1),
                    "risk_score": round(risk_score, 1),
                    "execution_confidence": round(exec_conf, 1),
                    "sizing_confidence": round(sizing_conf_score, 1),
                    "action_readiness": round(readiness_score, 1),
                    "primary_scenario": primary.get("name"),
                    "primary_score": round(primary_score, 1),
                    "secondary_scenario": secondary.get("name"),
                    "secondary_score": round(secondary_score, 1),
                },
                "scope": {
                    "technical_only": True,
                    "persistent_history": False,
                    "automatic_execution": False,
                    "portfolio_state_used": False,
                    "note": (
                        "DE-TA-014.0 detects the current technical state and "
                        "transition conditions. Persistent state history and "
                        "transition auditing are reserved for DE-TA-014.1."
                    ),
                },
            },
        }

    def _derive_state(
        self,
        *,
        execution_state: dict[str, Any],
        action_matrix: dict[str, Any],
        risk_state: str,
        direction_score: float,
        primary: dict[str, Any],
        secondary: dict[str, Any],
    ) -> str:
        risk_state = risk_state.upper()
        exec_state = str(
            execution_state.get("state") or ""
        ).upper()

        enter_state = str(
            (action_matrix.get("ENTER") or {}).get("state") or ""
        ).upper()

        primary_direction = str(
            primary.get("direction") or "NEUTRAL"
        ).upper()

        secondary_name = str(
            secondary.get("name") or ""
        ).upper()

        if (
            risk_state in {"CRITICAL", "HIGH"}
            or exec_state == "WAIT_DEFENSIVE"
            or direction_score <= -55
        ):
            return "WAIT_DEFENSIVE"

        if (
            direction_score < -20
            and (
                "STABIL" in secondary_name
                or primary_direction == "NEUTRAL"
            )
        ):
            return "STABILIZING"

        if (
            -20 <= direction_score < 20
            and enter_state in {"WAIT", "BLOCKED", "CONDITIONAL"}
        ):
            return "WATCH_REVERSAL"

        if enter_state in {"CONDITIONAL", "PERMITTED"}:
            return "ENTRY_ELIGIBLE"

        if direction_score >= 35 and primary_direction == "BULLISH":
            return "CONSTRUCTIVE"

        return "STABILIZING"

    def _state_score(
        self,
        *,
        current_state: str,
        direction_score: float,
        risk_score: float,
        primary_score: float,
        secondary_score: float,
        readiness_score: float,
    ) -> float:
        if current_state == "WAIT_DEFENSIVE":
            score = (
                max(0.0, -direction_score) * 0.30
                + risk_score * 0.30
                + primary_score * 0.20
                + readiness_score * 0.20
            )
        elif current_state == "STABILIZING":
            score = (
                (100.0 - min(100.0, abs(direction_score))) * 0.30
                + secondary_score * 0.30
                + (100.0 - risk_score) * 0.20
                + readiness_score * 0.20
            )
        elif current_state == "WATCH_REVERSAL":
            score = (
                (100.0 - min(100.0, abs(direction_score))) * 0.35
                + secondary_score * 0.25
                + readiness_score * 0.25
                + (100.0 - risk_score) * 0.15
            )
        elif current_state == "ENTRY_ELIGIBLE":
            score = (
                max(0.0, direction_score) * 0.30
                + readiness_score * 0.30
                + primary_score * 0.25
                + (100.0 - risk_score) * 0.15
            )
        else:
            score = (
                max(0.0, direction_score) * 0.35
                + primary_score * 0.30
                + readiness_score * 0.20
                + (100.0 - risk_score) * 0.15
            )

        return max(0.0, min(100.0, score))

    def _transition_candidates(
        self,
        *,
        current_state: str,
        direction_score: float,
        risk_score: float,
        primary: dict[str, Any],
        secondary: dict[str, Any],
        action: dict[str, Any],
        execution: dict[str, Any],
    ) -> list[dict[str, Any]]:
        candidates: list[dict[str, Any]] = []

        primary_direction = str(
            primary.get("direction") or "NEUTRAL"
        ).upper()
        primary_score = self._number(
            primary.get("plausibility_score"), 0.0
        )
        secondary_score = self._number(
            secondary.get("plausibility_score"), 0.0
        )

        if current_state == "WAIT_DEFENSIVE":
            probability = self._clamp(
                25.0
                + max(0.0, 70.0 - risk_score) * 0.45
                + max(0.0, direction_score + 70.0) * 0.20
                + secondary_score * 0.15,
                0.0,
                100.0,
            )
            candidates.append({
                "state": "STABILIZING",
                "probability": round(probability, 1),
                "status": "WATCH",
                "requirements": [
                    "Risk regime falls below HIGH",
                    "Direction score improves above -55",
                    "Primary bearish scenario weakens",
                    "Momentum deterioration stops",
                ],
            })

        elif current_state == "STABILIZING":
            probability = self._clamp(
                30.0
                + max(0.0, 60.0 - risk_score) * 0.35
                + max(0.0, direction_score + 30.0) * 0.25
                + secondary_score * 0.20,
                0.0,
                100.0,
            )
            candidates.append({
                "state": "WATCH_REVERSAL",
                "probability": round(probability, 1),
                "status": "WATCH",
                "requirements": [
                    "Direction score approaches neutral",
                    "Structure recovery validates",
                    "Liquidity rebalances",
                    "Momentum score reaches neutral",
                ],
            })

        elif current_state == "WATCH_REVERSAL":
            probability = self._clamp(
                35.0
                + max(0.0, direction_score + 20.0) * 0.35
                + max(0.0, 50.0 - risk_score) * 0.25
                + max(0.0, 60.0 - primary_score) * 0.20,
                0.0,
                100.0,
            )
            candidates.append({
                "state": "ENTRY_ELIGIBLE",
                "probability": round(probability, 1),
                "status": "WATCH",
                "requirements": [
                    "All critical confirmation gates close",
                    "Execution ENTER state becomes conditional/permitted",
                    "Risk regime falls to MODERATE/ELEVATED",
                    "Bullish or neutral structure confirms",
                ],
            })

        elif current_state == "ENTRY_ELIGIBLE":
            probability = self._clamp(
                40.0
                + max(0.0, direction_score) * 0.35
                + max(0.0, 50.0 - risk_score) * 0.25
                + primary_score * 0.20,
                0.0,
                100.0,
            )
            candidates.append({
                "state": "CONSTRUCTIVE",
                "probability": round(probability, 1),
                "status": "WATCH",
                "requirements": [
                    "Primary scenario becomes bullish",
                    "Direction score exceeds +35",
                    "Risk remains below ELEVATED",
                    "Entry permissions remain active",
                ],
            })

        if current_state != "WAIT_DEFENSIVE":
            candidates.append({
                "state": "WAIT_DEFENSIVE",
                "probability": round(
                    self._clamp(
                        risk_score * 0.55
                        + max(0.0, -direction_score) * 0.45,
                        0.0,
                        100.0,
                    ),
                    1,
                ),
                "status": "RISK_REVERSAL",
                "requirements": [
                    "Risk returns to HIGH/CRITICAL",
                    "Fresh bearish structural break",
                    "Execution plan returns to WAIT_DEFENSIVE",
                ],
            })

        candidates.sort(
            key=lambda item: float(item.get("probability") or 0.0),
            reverse=True,
        )

        return candidates

    def _watchlist(
        self,
        *,
        current_state: str,
        transition_candidates: list[dict[str, Any]],
        execution: dict[str, Any],
        risk: dict[str, Any],
        action: dict[str, Any],
    ) -> list[dict[str, Any]]:
        watch: list[dict[str, Any]] = []

        if transition_candidates:
            target = transition_candidates[0]
            for requirement in target.get("requirements") or []:
                watch.append({
                    "category": "TRANSITION",
                    "target_state": target.get("state"),
                    "condition": requirement,
                    "status": "OPEN",
                })

        for condition in (risk.get("release_conditions") or [])[:4]:
            watch.append({
                "category": "RISK_RELEASE",
                "target_state": None,
                "condition": condition,
                "status": "OPEN",
            })

        for item in (action.get("confirmation_gates") or [])[:4]:
            if isinstance(item, dict):
                watch.append({
                    "category": "CONFIRMATION_GATE",
                    "target_state": None,
                    "condition": item.get("target") or item.get("gate"),
                    "status": item.get("status", "OPEN"),
                })

        return watch

    def _transition_readiness(
        self,
        *,
        current_state: str,
        next_state: dict[str, Any],
        direction_score: float,
        risk_score: float,
        readiness_score: float,
        exec_conf: float,
        sizing_conf: float,
    ) -> dict[str, Any]:
        probability = self._number(
            next_state.get("probability"), 0.0
        )

        score = (
            probability * 0.35
            + readiness_score * 0.20
            + exec_conf * 0.20
            + sizing_conf * 0.15
            + (100.0 - min(100.0, risk_score)) * 0.10
        )

        if score >= 80:
            state = "HIGH"
        elif score >= 60:
            state = "MODERATE"
        else:
            state = "LOW"

        return {
            "score": round(
                max(0.0, min(100.0, score)), 1
            ),
            "state": state,
            "from_state": current_state,
            "to_state": next_state.get("state"),
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

    @staticmethod
    def _clamp(
        value: float,
        minimum: float,
        maximum: float,
    ) -> float:
        return max(minimum, min(maximum, value))
