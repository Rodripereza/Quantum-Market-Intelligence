from __future__ import annotations

from typing import Any


class TechnicalDecisionService:
    """
    DE-TA-008.2.0 — Technical Decision Layer

    Converts Technical Confluence into an auditable technical posture.

    IMPORTANT:
    - This is NOT the global QMI Decision Engine.
    - This service does NOT issue BUY / HOLD / SELL instructions.
    - It interprets technical evidence only.
    """

    def analyze(
        self,
        confluence_response: dict[str, Any],
    ) -> dict[str, Any]:
        confluence = (
            confluence_response.get("technical_confluence")
            or {}
        )

        direction_score = self._number(
            confluence.get("direction_score"),
            0.0,
        )
        confidence = self._number(
            confluence.get("confidence"),
            0.0,
        )
        agreement = self._number(
            confluence.get("agreement"),
            0.0,
        )
        data_quality = self._number(
            confluence.get("data_quality"),
            0.0,
        )

        conflicts = (
            confluence.get("conflicts")
            if isinstance(confluence.get("conflicts"), list)
            else []
        )
        engines = (
            confluence.get("engines")
            if isinstance(confluence.get("engines"), dict)
            else {}
        )

        posture = self._technical_posture(
            direction_score=direction_score,
            confidence=confidence,
        )

        readiness = self._decision_readiness(
            confidence=confidence,
            agreement=agreement,
            data_quality=data_quality,
            conflicts=conflicts,
        )

        exposure_context = self._exposure_context(
            direction_score=direction_score,
            confidence=confidence,
            readiness_score=readiness["score"],
        )

        blockers = self._identify_blockers(engines)

        reversal_requirements = self._build_reversal_requirements(
            direction_score=direction_score,
            engines=engines,
            blockers=blockers,
        )

        supporting_evidence = self._supporting_evidence(
            direction_score=direction_score,
            engines=engines,
        )

        contradictory_evidence = self._contradictory_evidence(
            direction_score=direction_score,
            engines=engines,
        )

        risk_flags = self._risk_flags(
            confluence=confluence,
            blockers=blockers,
            conflicts=conflicts,
        )

        return {
            "engine": "QMI Technical Decision Layer",
            "engine_id": "DE-TA-008.2.0",
            "version": "0.1.0",
            "status": "operational",
            "technical_decision": {
                "posture": posture,
                "direction_score": round(direction_score, 1),
                "confidence": round(confidence, 1),
                "agreement": round(agreement, 1),
                "data_quality": round(data_quality, 1),
                "readiness": readiness,
                "exposure_context": exposure_context,
                "supporting_evidence": supporting_evidence,
                "contradictory_evidence": contradictory_evidence,
                "blockers": blockers,
                "reversal_requirements": reversal_requirements,
                "risk_flags": risk_flags,
                "decision_scope": {
                    "technical_only": True,
                    "global_decision": False,
                    "buy_hold_sell_signal": False,
                    "note": (
                        "This layer interprets technical conditions only. "
                        "Global QMI decisions require Fundamental, Risk, "
                        "Portfolio and AI/ML evidence."
                    ),
                },
            },
        }

    def _technical_posture(
        self,
        direction_score: float,
        confidence: float,
    ) -> dict[str, Any]:
        abs_score = abs(direction_score)

        if direction_score <= -65:
            state = "DEFENSIVE"
            directional_state = "STRONG_BEARISH"
        elif direction_score <= -30:
            state = "CAUTIOUS"
            directional_state = "BEARISH"
        elif direction_score < 30:
            state = "NEUTRAL"
            directional_state = "NEUTRAL"
        elif direction_score < 65:
            state = "CONSTRUCTIVE"
            directional_state = "BULLISH"
        else:
            state = "AGGRESSIVE_CONSTRUCTIVE"
            directional_state = "STRONG_BULLISH"

        if confidence >= 85:
            conviction = "HIGH"
        elif confidence >= 70:
            conviction = "MODERATE"
        else:
            conviction = "LOW"

        return {
            "state": state,
            "directional_state": directional_state,
            "conviction": conviction,
            "severity": round(abs_score, 1),
        }

    def _decision_readiness(
        self,
        confidence: float,
        agreement: float,
        data_quality: float,
        conflicts: list[dict[str, Any]],
    ) -> dict[str, Any]:
        conflict_penalty = min(
            20.0,
            sum(
                self._number(item.get("severity"), 0.0)
                for item in conflicts
            ) / 25.0,
        )

        score = (
            confidence * 0.45
            + agreement * 0.35
            + data_quality * 0.20
            - conflict_penalty
        )
        score = max(0.0, min(100.0, score))

        if score >= 85:
            state = "DECISION_READY"
        elif score >= 70:
            state = "USABLE_WITH_CAUTION"
        else:
            state = "LOW_READINESS"

        return {
            "score": round(score, 1),
            "state": state,
            "conflict_penalty": round(conflict_penalty, 1),
        }

    def _exposure_context(
        self,
        direction_score: float,
        confidence: float,
        readiness_score: float,
    ) -> dict[str, str]:
        if direction_score <= -65:
            new_long = "UNFAVORABLE"
            existing_long = "HIGH_CAUTION"
            short_term = "BEARISH"
        elif direction_score <= -30:
            new_long = "CAUTION"
            existing_long = "CAUTION"
            short_term = "BEARISH"
        elif direction_score < 30:
            new_long = "NEUTRAL"
            existing_long = "NEUTRAL"
            short_term = "NEUTRAL"
        elif direction_score < 65:
            new_long = "FAVORABLE_WITH_CONFIRMATION"
            existing_long = "CONSTRUCTIVE"
            short_term = "BULLISH"
        else:
            new_long = "TECHNICALLY_FAVORABLE"
            existing_long = "CONSTRUCTIVE"
            short_term = "BULLISH"

        if confidence < 70 or readiness_score < 70:
            new_long = "WAIT_FOR_CONFIRMATION"

        return {
            "new_long_exposure": new_long,
            "existing_long_exposure": existing_long,
            "short_term_bias": short_term,
        }

    def _identify_blockers(
        self,
        engines: dict[str, Any],
    ) -> list[dict[str, Any]]:
        blockers: list[dict[str, Any]] = []

        for engine_name, payload in engines.items():
            if not isinstance(payload, dict):
                continue
            if not payload.get("available", False):
                continue

            score = self._number(payload.get("score"), 0.0)

            if score <= -20:
                blockers.append({
                    "engine": engine_name,
                    "score": round(score, 1),
                    "state": payload.get("state"),
                    "severity": self._severity(abs(score)),
                    "reason": (
                        f"{engine_name} remains materially bearish "
                        "and blocks a constructive technical posture."
                    ),
                })

        blockers.sort(
            key=lambda item: abs(item["score"]),
            reverse=True,
        )

        return blockers

    def _build_reversal_requirements(
        self,
        direction_score: float,
        engines: dict[str, Any],
        blockers: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if direction_score >= -30:
            return [
                {
                    "priority": 1,
                    "requirement": "MAINTAIN_OR_IMPROVE_CONFLUENCE",
                    "description": (
                        "No major bearish reversal requirement is active. "
                        "Maintain current constructive / neutral evidence."
                    ),
                }
            ]

        requirements: list[dict[str, Any]] = []
        priority = 1

        preferred_order = [
            "structure",
            "trend",
            "liquidity",
            "momentum",
            "strength",
            "support_resistance",
            "volume",
        ]

        blockers_by_engine = {
            item["engine"]: item
            for item in blockers
        }

        for engine_name in preferred_order:
            blocker = blockers_by_engine.get(engine_name)
            if blocker is None:
                continue

            current_score = blocker["score"]

            if engine_name == "structure":
                requirement = "STRUCTURE_RECOVERY"
                target = "Structure score > -20"
                description = (
                    "Recover market structure from materially bearish "
                    "conditions before a bullish technical posture can "
                    "be considered."
                )
            elif engine_name == "trend":
                requirement = "TREND_NEUTRALIZATION"
                target = "Trend score > -20"
                description = (
                    "Primary trend must improve toward neutral."
                )
            elif engine_name == "liquidity":
                requirement = "LIQUIDITY_REBALANCE"
                target = "Liquidity score > -20"
                description = (
                    "Bearish liquidity pressure must materially weaken "
                    "or flip toward balanced / bullish context."
                )
            elif engine_name == "momentum":
                requirement = "MOMENTUM_RECOVERY"
                target = "Momentum score >= 0"
                description = (
                    "Momentum must stop reinforcing downside pressure."
                )
            elif engine_name == "strength":
                requirement = "BEARISH_STRENGTH_DECAY"
                target = "Strength directional score > -20"
                description = (
                    "Bearish directional strength must weaken."
                )
            elif engine_name == "support_resistance":
                requirement = "S_R_POSITION_IMPROVEMENT"
                target = "Support/Resistance score > -15"
                description = (
                    "Price context relative to structural zones must improve."
                )
            else:
                requirement = "VOLUME_CONFIRMATION"
                target = "Volume score >= 0"
                description = (
                    "Volume should stop confirming downside conditions."
                )

            requirements.append({
                "priority": priority,
                "engine": engine_name,
                "requirement": requirement,
                "current_score": current_score,
                "target": target,
                "description": description,
            })
            priority += 1

        return requirements

    def _supporting_evidence(
        self,
        direction_score: float,
        engines: dict[str, Any],
    ) -> list[dict[str, Any]]:
        sign = -1 if direction_score < 0 else 1 if direction_score > 0 else 0
        evidence: list[dict[str, Any]] = []

        for name, payload in engines.items():
            if not isinstance(payload, dict):
                continue
            if not payload.get("available", False):
                continue

            score = self._number(payload.get("score"), 0.0)

            if sign < 0 and score <= -15:
                evidence.append(
                    self._evidence_payload(name, payload, score)
                )
            elif sign > 0 and score >= 15:
                evidence.append(
                    self._evidence_payload(name, payload, score)
                )
            elif sign == 0 and abs(score) < 15:
                evidence.append(
                    self._evidence_payload(name, payload, score)
                )

        evidence.sort(
            key=lambda item: abs(item["score"]),
            reverse=True,
        )
        return evidence

    def _contradictory_evidence(
        self,
        direction_score: float,
        engines: dict[str, Any],
    ) -> list[dict[str, Any]]:
        evidence: list[dict[str, Any]] = []

        for name, payload in engines.items():
            if not isinstance(payload, dict):
                continue
            if not payload.get("available", False):
                continue

            score = self._number(payload.get("score"), 0.0)

            if direction_score < 0 and score >= 20:
                evidence.append(
                    self._evidence_payload(name, payload, score)
                )
            elif direction_score > 0 and score <= -20:
                evidence.append(
                    self._evidence_payload(name, payload, score)
                )

        evidence.sort(
            key=lambda item: abs(item["score"]),
            reverse=True,
        )
        return evidence

    def _risk_flags(
        self,
        confluence: dict[str, Any],
        blockers: list[dict[str, Any]],
        conflicts: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        flags: list[dict[str, str]] = []

        volatility = (
            confluence.get("volatility_context")
            if isinstance(
                confluence.get("volatility_context"),
                dict,
            )
            else {}
        )

        if volatility.get("compression"):
            flags.append({
                "flag": "VOLATILITY_COMPRESSION",
                "severity": "MODERATE",
                "description": (
                    "Volatility is compressed; directional resolution "
                    "may accelerate after expansion."
                ),
            })

        if volatility.get("expansion"):
            flags.append({
                "flag": "VOLATILITY_EXPANSION",
                "severity": "HIGH",
                "description": (
                    "Volatility expansion increases execution and "
                    "timing risk."
                ),
            })

        if conflicts:
            flags.append({
                "flag": "ENGINE_CONFLICT",
                "severity": "MODERATE",
                "description": (
                    "Major technical engines contain contradictory "
                    "directional evidence."
                ),
            })

        if len(blockers) >= 5:
            flags.append({
                "flag": "BROAD_BEARISH_ALIGNMENT",
                "severity": "HIGH",
                "description": (
                    "Bearish evidence is distributed across multiple "
                    "independent technical engines."
                ),
            })

        return flags

    def _evidence_payload(
        self,
        name: str,
        payload: dict[str, Any],
        score: float,
    ) -> dict[str, Any]:
        return {
            "engine": name,
            "score": round(score, 1),
            "state": payload.get("state"),
            "confidence": payload.get("confidence"),
        }

    @staticmethod
    def _severity(value: float) -> str:
        if value >= 70:
            return "VERY_HIGH"
        if value >= 50:
            return "HIGH"
        if value >= 30:
            return "MODERATE"
        return "LOW"

    @staticmethod
    def _number(value: Any, default: float) -> float:
        try:
            return float(value)
        except (TypeError, ValueError):
            return float(default)
