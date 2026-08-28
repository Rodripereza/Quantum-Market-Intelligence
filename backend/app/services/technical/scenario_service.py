from __future__ import annotations

from typing import Any


class TechnicalScenarioService:
    """
    DE-TA-009.0 — Technical Scenario Engine

    Builds conditional forward technical scenarios from the
    DE-TA-008.2 Technical Decision Layer.

    IMPORTANT:
    - Scenario plausibility is NOT a calibrated market probability.
    - No price target is invented.
    - No BUY / HOLD / SELL instruction is issued.
    - Every scenario must expose activation and invalidation conditions.
    """

    def analyze(
        self,
        decision_response: dict[str, Any],
    ) -> dict[str, Any]:
        decision = decision_response.get("technical_decision") or {}

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
        readiness = decision.get("readiness") or {}
        readiness_score = self._number(
            readiness.get("score"),
            0.0,
        )

        posture = decision.get("posture") or {}
        blockers = (
            decision.get("blockers")
            if isinstance(decision.get("blockers"), list)
            else []
        )
        reversal_requirements = (
            decision.get("reversal_requirements")
            if isinstance(
                decision.get("reversal_requirements"),
                list,
            )
            else []
        )
        risk_flags = (
            decision.get("risk_flags")
            if isinstance(decision.get("risk_flags"), list)
            else []
        )

        dominant_direction = (
            "BEARISH"
            if direction_score < -20
            else "BULLISH"
            if direction_score > 20
            else "NEUTRAL"
        )

        scenarios = self._build_scenarios(
            dominant_direction=dominant_direction,
            direction_score=direction_score,
            confidence=confidence,
            agreement=agreement,
            readiness_score=readiness_score,
            blockers=blockers,
            reversal_requirements=reversal_requirements,
            risk_flags=risk_flags,
        )

        ranked = sorted(
            scenarios,
            key=lambda item: item["plausibility_score"],
            reverse=True,
        )

        primary = ranked[0] if ranked else None
        secondary = ranked[1] if len(ranked) > 1 else None

        dispersion = self._scenario_dispersion(ranked)

        return {
            "engine": "QMI Technical Scenario Engine",
            "engine_id": "DE-TA-009.0",
            "version": "0.1.0",
            "status": "operational",
            "technical_scenarios": {
                "dominant_direction": dominant_direction,
                "source_posture": posture.get("state"),
                "source_direction_score": round(direction_score, 1),
                "source_confidence": round(confidence, 1),
                "source_agreement": round(agreement, 1),
                "source_readiness": round(readiness_score, 1),
                "primary_scenario": primary,
                "secondary_scenario": secondary,
                "scenario_dispersion": dispersion,
                "scenarios": ranked,
                "scope": {
                    "technical_only": True,
                    "forecast_probability": False,
                    "price_target_model": False,
                    "buy_hold_sell_signal": False,
                    "note": (
                        "Plausibility scores rank conditional technical "
                        "scenarios. They are not calibrated probabilities."
                    ),
                },
            },
        }

    def _build_scenarios(
        self,
        dominant_direction: str,
        direction_score: float,
        confidence: float,
        agreement: float,
        readiness_score: float,
        blockers: list[dict[str, Any]],
        reversal_requirements: list[dict[str, Any]],
        risk_flags: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        directional_strength = min(100.0, abs(direction_score))
        evidence_quality = (
            confidence * 0.45
            + agreement * 0.30
            + readiness_score * 0.25
        )

        broad_alignment = any(
            item.get("flag") == "BROAD_BEARISH_ALIGNMENT"
            for item in risk_flags
            if isinstance(item, dict)
        )

        volatility_compression = any(
            item.get("flag") == "VOLATILITY_COMPRESSION"
            for item in risk_flags
            if isinstance(item, dict)
        )

        blocker_strength = self._blocker_strength(blockers)
        reversal_distance = self._reversal_distance(
            reversal_requirements
        )

        scenarios: list[dict[str, Any]] = []

        if dominant_direction == "BEARISH":
            continuation_score = (
                directional_strength * 0.45
                + evidence_quality * 0.35
                + blocker_strength * 0.20
            )
            if broad_alignment:
                continuation_score += 5.0

            stabilization_score = (
                (100.0 - directional_strength) * 0.35
                + (100.0 - blocker_strength) * 0.25
                + confidence * 0.20
                + (15.0 if volatility_compression else 5.0)
            )

            reversal_score = (
                (100.0 - directional_strength) * 0.30
                + (100.0 - blocker_strength) * 0.25
                + (100.0 - reversal_distance) * 0.30
                + (100.0 - agreement) * 0.15
            )

            scenarios.extend([
                self._scenario(
                    scenario_id="BEARISH_CONTINUATION",
                    name="Bearish Continuation",
                    direction="BEARISH",
                    plausibility=continuation_score,
                    rationale=(
                        "Current technical posture, engine alignment and "
                        "active bearish blockers continue to support downside "
                        "continuation unless key reversal conditions improve."
                    ),
                    activation=self._bearish_activation(blockers),
                    invalidation=self._bearish_invalidation(
                        reversal_requirements
                    ),
                    requirements=[],
                ),
                self._scenario(
                    scenario_id="STABILIZATION",
                    name="Stabilization / Base Formation",
                    direction="NEUTRAL",
                    plausibility=stabilization_score,
                    rationale=(
                        "A neutralization phase becomes more plausible if "
                        "downside momentum decays while structure and trend "
                        "stop deteriorating."
                    ),
                    activation=[
                        "Momentum stops reinforcing downside pressure",
                        "No new bearish structural break is confirmed",
                        "Liquidity pressure begins to rebalance",
                    ],
                    invalidation=[
                        "Fresh bearish BOS with renewed momentum confirmation",
                        "Broad bearish engine alignment strengthens further",
                    ],
                    requirements=self._top_requirements(
                        reversal_requirements,
                        limit=3,
                    ),
                ),
                self._scenario(
                    scenario_id="BULLISH_REVERSAL",
                    name="Bullish Technical Reversal",
                    direction="BULLISH",
                    plausibility=reversal_score,
                    rationale=(
                        "A bullish reversal requires multiple independent "
                        "bearish blockers to be neutralized; this is a higher "
                        "bar than a simple short-term bounce."
                    ),
                    activation=self._bullish_activation(
                        reversal_requirements
                    ),
                    invalidation=[
                        "Structure remains materially bearish",
                        "Trend remains below neutralization threshold",
                        "Liquidity remains strongly bearish",
                    ],
                    requirements=self._top_requirements(
                        reversal_requirements,
                        limit=5,
                    ),
                ),
            ])

        elif dominant_direction == "BULLISH":
            continuation_score = (
                directional_strength * 0.45
                + evidence_quality * 0.35
                + (100.0 - blocker_strength) * 0.20
            )

            stabilization_score = (
                (100.0 - directional_strength) * 0.35
                + confidence * 0.25
                + (15.0 if volatility_compression else 5.0)
                + blocker_strength * 0.15
            )

            bearish_reversal_score = (
                (100.0 - directional_strength) * 0.30
                + blocker_strength * 0.30
                + (100.0 - agreement) * 0.20
                + (100.0 - confidence) * 0.20
            )

            scenarios.extend([
                self._scenario(
                    scenario_id="BULLISH_CONTINUATION",
                    name="Bullish Continuation",
                    direction="BULLISH",
                    plausibility=continuation_score,
                    rationale=(
                        "Constructive technical posture remains intact while "
                        "structure, trend and liquidity continue to align."
                    ),
                    activation=[
                        "Bullish structure remains intact",
                        "Trend remains constructive",
                        "Liquidity does not flip materially bearish",
                    ],
                    invalidation=[
                        "Bearish CHoCH / BOS is confirmed",
                        "Trend deteriorates below neutral",
                        "Liquidity flips to strong bearish pressure",
                    ],
                    requirements=[],
                ),
                self._scenario(
                    scenario_id="STABILIZATION",
                    name="Stabilization / Consolidation",
                    direction="NEUTRAL",
                    plausibility=stabilization_score,
                    rationale=(
                        "Consolidation becomes more plausible if directional "
                        "momentum fades without a structural reversal."
                    ),
                    activation=[
                        "Momentum decelerates",
                        "No bearish structural break is confirmed",
                    ],
                    invalidation=[
                        "Directional expansion resumes with strong agreement",
                    ],
                    requirements=[],
                ),
                self._scenario(
                    scenario_id="BEARISH_REVERSAL",
                    name="Bearish Technical Reversal",
                    direction="BEARISH",
                    plausibility=bearish_reversal_score,
                    rationale=(
                        "Bearish reversal requires constructive technical "
                        "evidence to deteriorate across multiple engines."
                    ),
                    activation=[
                        "Bearish structural break is confirmed",
                        "Trend weakens below neutral",
                        "Liquidity turns materially bearish",
                    ],
                    invalidation=[
                        "Bullish structure remains intact",
                        "Positive engine agreement stays high",
                    ],
                    requirements=[],
                ),
            ])

        else:
            neutral_score = (
                confidence * 0.35
                + readiness_score * 0.25
                + (100.0 - directional_strength) * 0.40
            )
            bullish_break_score = (
                (100.0 - blocker_strength) * 0.35
                + confidence * 0.30
                + (100.0 - reversal_distance) * 0.20
                + (100.0 - agreement) * 0.15
            )
            bearish_break_score = (
                blocker_strength * 0.35
                + confidence * 0.30
                + agreement * 0.20
                + directional_strength * 0.15
            )

            scenarios.extend([
                self._scenario(
                    scenario_id="NEUTRAL_CONTINUATION",
                    name="Neutral / Range Continuation",
                    direction="NEUTRAL",
                    plausibility=neutral_score,
                    rationale=(
                        "Technical evidence remains balanced and does not "
                        "support a decisive directional scenario yet."
                    ),
                    activation=[
                        "No decisive structural break",
                        "Engine scores remain clustered around neutral",
                    ],
                    invalidation=[
                        "Directional score exits neutral regime with high agreement",
                    ],
                    requirements=[],
                ),
                self._scenario(
                    scenario_id="BULLISH_BREAKOUT",
                    name="Bullish Resolution",
                    direction="BULLISH",
                    plausibility=bullish_break_score,
                    rationale=(
                        "Bullish resolution requires constructive structure "
                        "and improving directional confirmation."
                    ),
                    activation=[
                        "Bullish structural confirmation",
                        "Trend and momentum improve",
                        "Liquidity confirms upside acceptance",
                    ],
                    invalidation=[
                        "Bearish structure reasserts",
                    ],
                    requirements=[],
                ),
                self._scenario(
                    scenario_id="BEARISH_BREAKDOWN",
                    name="Bearish Resolution",
                    direction="BEARISH",
                    plausibility=bearish_break_score,
                    rationale=(
                        "Bearish resolution requires downside structural "
                        "confirmation with broad engine agreement."
                    ),
                    activation=[
                        "Bearish structural confirmation",
                        "Trend and momentum deteriorate",
                        "Liquidity confirms downside pressure",
                    ],
                    invalidation=[
                        "Bullish structure recovers",
                    ],
                    requirements=[],
                ),
            ])

        return scenarios

    def _scenario(
        self,
        scenario_id: str,
        name: str,
        direction: str,
        plausibility: float,
        rationale: str,
        activation: list[str],
        invalidation: list[str],
        requirements: list[dict[str, Any]],
    ) -> dict[str, Any]:
        score = max(0.0, min(100.0, plausibility))

        if score >= 75:
            tier = "HIGH"
        elif score >= 55:
            tier = "MODERATE"
        elif score >= 35:
            tier = "LOW"
        else:
            tier = "VERY_LOW"

        return {
            "scenario_id": scenario_id,
            "name": name,
            "direction": direction,
            "plausibility_score": round(score, 1),
            "plausibility_tier": tier,
            "rationale": rationale,
            "activation_conditions": activation,
            "invalidation_conditions": invalidation,
            "key_requirements": requirements,
        }

    def _bearish_activation(
        self,
        blockers: list[dict[str, Any]],
    ) -> list[str]:
        conditions = [
            "Bearish structure remains intact",
            "No major blocker is neutralized",
        ]

        strongest = [
            item for item in blockers
            if isinstance(item, dict)
        ][:3]

        for item in strongest:
            engine = str(item.get("engine") or "").replace("_", " ")
            if engine:
                conditions.append(
                    f"{engine.title()} remains materially bearish"
                )

        return conditions

    def _bearish_invalidation(
        self,
        reversal_requirements: list[dict[str, Any]],
    ) -> list[str]:
        requirements = self._top_requirements(
            reversal_requirements,
            limit=3,
        )

        if not requirements:
            return [
                "Direction score improves above bearish regime",
                "Structure and trend materially recover",
            ]

        return [
            f"{item['requirement']}: {item['target']}"
            for item in requirements
        ]

    def _bullish_activation(
        self,
        reversal_requirements: list[dict[str, Any]],
    ) -> list[str]:
        requirements = self._top_requirements(
            reversal_requirements,
            limit=4,
        )

        if not requirements:
            return [
                "Structure turns constructive",
                "Trend neutralizes",
                "Liquidity confirms recovery",
            ]

        return [
            f"{item['requirement']}: {item['target']}"
            for item in requirements
        ]

    def _top_requirements(
        self,
        reversal_requirements: list[dict[str, Any]],
        limit: int,
    ) -> list[dict[str, Any]]:
        items = [
            item for item in reversal_requirements
            if isinstance(item, dict)
        ]

        items.sort(
            key=lambda item: self._number(
                item.get("priority"),
                999.0,
            )
        )

        return [
            {
                "priority": item.get("priority"),
                "engine": item.get("engine"),
                "requirement": item.get("requirement"),
                "current_score": item.get("current_score"),
                "target": item.get("target"),
            }
            for item in items[:limit]
        ]

    def _blocker_strength(
        self,
        blockers: list[dict[str, Any]],
    ) -> float:
        values = [
            abs(self._number(item.get("score"), 0.0))
            for item in blockers
            if isinstance(item, dict)
        ]

        if not values:
            return 0.0

        top = sorted(values, reverse=True)[:5]
        return min(100.0, sum(top) / len(top))

    def _reversal_distance(
        self,
        requirements: list[dict[str, Any]],
    ) -> float:
        """
        Measures how far the current system is from satisfying the
        listed reversal requirements using current engine score magnitude.
        """
        distances = []

        for item in requirements:
            if not isinstance(item, dict):
                continue
            score = self._number(
                item.get("current_score"),
                0.0,
            )
            distances.append(min(100.0, abs(score)))

        if not distances:
            return 50.0

        return sum(distances) / len(distances)

    def _scenario_dispersion(
        self,
        scenarios: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not scenarios:
            return {
                "spread": 0.0,
                "state": "UNKNOWN",
            }

        scores = [
            self._number(item.get("plausibility_score"), 0.0)
            for item in scenarios
        ]

        spread = max(scores) - min(scores)

        if spread >= 35:
            state = "CLEAR_PRIMARY"
        elif spread >= 18:
            state = "MODERATE_SEPARATION"
        else:
            state = "COMPETING_SCENARIOS"

        return {
            "spread": round(spread, 1),
            "state": state,
        }

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)
