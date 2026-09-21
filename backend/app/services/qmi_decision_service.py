from __future__ import annotations

from typing import Any


class QMIDecisionService:
    """
    DE-CORE-004.4 — Decision Trust Layer

    Combines Technical Decision Synthesis (DE-TA-015.0), the explainable
    Fundamental Decision Engine (FA-DECISION-001.1), and Adaptive Business Momentum.

    Scope:
    - strategic cross-engine posture
    - technical/fundamental alignment
    - timing gate preservation
    - transparent evidence and conflict reporting

    This layer does NOT:
    - execute orders
    - override technical risk gates
    - use portfolio capital constraints
    - issue an autonomous BUY/HOLD/SELL instruction
    """

    ENGINE_ID = "DE-CORE-004.4"
    ENGINE = "QMI Cross-Engine Decision Fusion"
    VERSION = "0.5.0"

    TECHNICAL_POSTURE_SCORES = {
        "ENTER": 90.0,
        "ADD": 82.0,
        "PREPARE": 70.0,
        "WATCH": 58.0,
        "WAIT": 45.0,
        "REDUCE": 25.0,
        "EXIT": 10.0,
    }

    TECHNICAL_HARD_GATES = {"WAIT", "REDUCE", "EXIT"}

    BASE_FUSION_WEIGHTS = {
        "technical": 0.45,
        "fundamental": 0.35,
        "business_momentum": 0.20,
    }

    REGIME_FUSION_WEIGHTS = {
        "CAPITAL_PROTECTION": {"technical": 0.65, "fundamental": 0.25, "business_momentum": 0.10},
        "DEFENSIVE": {"technical": 0.60, "fundamental": 0.25, "business_momentum": 0.15},
        "TIMING_BLOCKED": {"technical": 0.55, "fundamental": 0.30, "business_momentum": 0.15},
        "RECOVERY_WATCH": {"technical": 0.40, "fundamental": 0.30, "business_momentum": 0.30},
        "PRICE_AHEAD_OF_BUSINESS": {"technical": 0.50, "fundamental": 0.35, "business_momentum": 0.15},
        "CROSS_ENGINE_CONFLICT": {"technical": 0.50, "fundamental": 0.35, "business_momentum": 0.15},
        "CONFIRMED_CONSTRUCTIVE": {"technical": 0.45, "fundamental": 0.35, "business_momentum": 0.20},
        "CONFIRMED_DEFENSIVE": {"technical": 0.60, "fundamental": 0.30, "business_momentum": 0.10},
        "TRANSITION": {"technical": 0.45, "fundamental": 0.35, "business_momentum": 0.20},
    }

    def analyze(
        self,
        *,
        symbol: str,
        technical_response: dict[str, Any],
        fundamental_response: Any,
        decision_intelligence: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        technical = (
            technical_response.get("technical_decision_synthesis")
            if isinstance(technical_response, dict)
            else {}
        ) or {}

        fundamental = self._to_dict(fundamental_response)
        fundamental_decision = fundamental.get("decision") or {}
        business_momentum = fundamental.get("business_momentum") or {}

        technical_available = bool(technical.get("available", False))
        fundamental_available = bool(fundamental_decision)
        business_momentum_available = (
            self._number_or_none(business_momentum.get("score")) is not None
        )

        if (
            not technical_available
            and not fundamental_available
            and not business_momentum_available
        ):
            return self._insufficient(symbol)

        technical_posture = str(
            technical.get("final_posture") or "WAIT"
        ).upper()
        technical_conviction = self._number(
            technical.get("conviction"),
            0.0,
        )
        technical_score = self._technical_score(
            posture=technical_posture,
            conviction=technical_conviction,
        )

        fundamental_stance = str(
            fundamental_decision.get("stance") or "UNKNOWN"
        ).upper()
        fundamental_score = self._number(
            fundamental_decision.get("decision_score"),
            50.0,
        )
        fundamental_conviction = str(
            fundamental_decision.get("conviction") or "LOW"
        ).upper()

        business_momentum_score = self._number_or_none(
            business_momentum.get("score")
        )
        business_momentum_regime = str(
            business_momentum.get("regime") or "UNKNOWN"
        ).upper()
        business_momentum_trend = str(
            business_momentum.get("trend") or "UNKNOWN"
        ).upper()
        business_momentum_confidence = str(
            business_momentum.get("confidence") or "LOW"
        ).upper()

        # Stage 1: calculate the neutral/base fusion. The regime is derived from
        # this score so adaptive weighting cannot recursively redefine its own regime.
        base_fusion_components = self._fusion_components(
            technical_score=technical_score if technical_available else None,
            fundamental_score=fundamental_score if fundamental_available else None,
            business_momentum_score=(
                business_momentum_score if business_momentum_available else None
            ),
            target_weights=self.BASE_FUSION_WEIGHTS,
        )
        base_combined_score = self._score_from_components(base_fusion_components)

        alignment_score = self._alignment_score(
            technical_score=technical_score if technical_available else None,
            fundamental_score=fundamental_score if fundamental_available else None,
        )
        alignment = self._alignment_state(alignment_score)

        business_divergence = self._business_divergence(
            technical_score=technical_score if technical_available else None,
            business_momentum_score=(
                business_momentum_score if business_momentum_available else None
            ),
        )

        timing_gate = self._timing_gate(
            technical_posture=technical_posture,
            technical_available=technical_available,
        )

        decision_regime = self._decision_regime(
            technical_posture=technical_posture,
            technical_available=technical_available,
            technical_risk_state=str(technical.get("risk_state") or "UNKNOWN").upper(),
            technical_execution_state=str(technical.get("execution_state") or "UNKNOWN").upper(),
            alignment=alignment,
            business_divergence=business_divergence,
            combined_score=base_combined_score,
        )

        # Stage 2: the resolved regime selects a transparent weight policy. Missing
        # engines are still renormalized to 100% after the regime policy is applied.
        regime_state = str(decision_regime.get("state") or "TRANSITION").upper()
        regime_weights = self.REGIME_FUSION_WEIGHTS.get(
            regime_state, self.BASE_FUSION_WEIGHTS
        )
        fusion_components = self._fusion_components(
            technical_score=technical_score if technical_available else None,
            fundamental_score=fundamental_score if fundamental_available else None,
            business_momentum_score=(
                business_momentum_score if business_momentum_available else None
            ),
            target_weights=regime_weights,
        )
        combined_score = self._score_from_components(fusion_components)

        conflict_resolution = self._conflict_resolution(
            decision_regime=decision_regime,
            technical_posture=technical_posture,
            technical_available=technical_available,
            fundamental_stance=fundamental_stance,
            business_momentum_regime=business_momentum_regime,
            business_divergence=business_divergence,
            timing_gate=timing_gate,
        )

        integrated_posture = self._integrated_posture(
            combined_score=combined_score,
            technical_posture=technical_posture,
            technical_available=technical_available,
            fundamental_stance=fundamental_stance,
        )

        confidence = self._confidence(
            technical_conviction=technical_conviction,
            fundamental_conviction=fundamental_conviction,
            technical_available=technical_available,
            fundamental_available=fundamental_available,
            business_momentum_confidence=business_momentum_confidence,
            business_momentum_available=business_momentum_available,
            alignment_score=alignment_score,
        )

        supporting_evidence = self._supporting_evidence(
            technical=technical,
            fundamental_decision=fundamental_decision,
            business_momentum=business_momentum,
        )
        conflicts = self._conflicts(
            technical_posture=technical_posture,
            fundamental_stance=fundamental_stance,
            technical=technical,
            fundamental_decision=fundamental_decision,
            business_divergence=business_divergence,
        )

        decision_trust = self._decision_trust(decision_intelligence or {})

        thesis = self._thesis(
            integrated_posture=integrated_posture,
            technical_posture=technical_posture,
            fundamental_stance=fundamental_stance,
            timing_gate=timing_gate,
            alignment=alignment,
            business_momentum_regime=business_momentum_regime,
            business_momentum_available=business_momentum_available,
            business_divergence=business_divergence,
        )

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "symbol": symbol.strip().upper(),
            "qmi_decision": {
                "available": True,
                "integrated_posture": integrated_posture,
                "combined_score": round(combined_score, 1),
                "base_combined_score": round(base_combined_score, 1),
                "confidence": confidence,
                "alignment": {
                    "state": alignment,
                    "score": round(alignment_score, 1),
                },
                "timing_gate": timing_gate,
                "technical": {
                    "available": technical_available,
                    "posture": technical_posture,
                    "score": round(technical_score, 1),
                    "conviction": round(technical_conviction, 1),
                    "timing": technical.get("timing") or "--",
                    "risk_state": technical.get("risk_state") or "UNKNOWN",
                    "execution_state": (
                        technical.get("execution_state") or "UNKNOWN"
                    ),
                },
                "fundamental": {
                    "available": fundamental_available,
                    "stance": fundamental_stance,
                    "score": round(fundamental_score, 1),
                    "conviction": fundamental_conviction,
                    "quality_score": fundamental_decision.get("quality_score"),
                    "regime_score": fundamental_decision.get("regime_score"),
                    "legacy_score": fundamental_decision.get("legacy_score"),
                    "engine_id": fundamental_decision.get("engine_id") or "FA-DECISION-001",
                    "version": fundamental_decision.get("version"),
                    "coverage_pct": fundamental_decision.get("coverage_pct"),
                },
                "business_momentum": {
                    "available": business_momentum_available,
                    "score": (
                        round(business_momentum_score, 1)
                        if business_momentum_score is not None
                        else None
                    ),
                    "regime": business_momentum_regime,
                    "trend": business_momentum_trend,
                    "confidence": business_momentum_confidence,
                    "coverage_pct": business_momentum.get("coverage_pct"),
                    "operating_driver_cap_pct": business_momentum.get(
                        "operating_driver_cap_pct"
                    ),
                },
                "business_divergence": business_divergence,
                "decision_regime": decision_regime,
                "conflict_resolution": conflict_resolution,
                "decision_trust": decision_trust,
                "adaptive_weighting": {
                    "enabled": True,
                    "regime": regime_state,
                    "base_weights": self.BASE_FUSION_WEIGHTS,
                    "regime_weights": regime_weights,
                    "weights_changed": any(
                        abs(regime_weights.get(key, self.BASE_FUSION_WEIGHTS[key]) - self.BASE_FUSION_WEIGHTS[key]) > 0.0001
                        for key in self.BASE_FUSION_WEIGHTS
                    ),
                },
                "fusion_weights": {
                    key: item["effective_weight"]
                    for key, item in fusion_components.items()
                },
                "fusion_components": fusion_components,
                "fusion_coverage": {
                    "active_components": sum(
                        1 for item in fusion_components.values() if item["available"]
                    ),
                    "total_components": len(fusion_components),
                    "coverage_pct": round(
                        (
                            sum(
                                1
                                for item in fusion_components.values()
                                if item["available"]
                            )
                            / len(fusion_components)
                        )
                        * 100.0,
                        1,
                    ),
                    "weights_renormalized": any(
                        item["available"]
                        and abs(item["effective_weight"] - item["regime_weight"]) > 0.0001
                        for item in fusion_components.values()
                    ),
                },
                "thesis": thesis,
                "supporting_evidence": supporting_evidence,
                "conflicts": conflicts,
                "scope": {
                    "technical": True,
                    "fundamental": True,
                    "business_momentum": True,
                    "portfolio": False,
                    "macro": False,
                    "news_sentiment": False,
                    "automatic_execution": False,
                    "buy_hold_sell_signal": False,
                    "note": (
                        "DE-CORE-004.4 v0.5.0 adds an auditable Decision Trust Layer over regime-aware adaptive fusion. "
                        "Trust evaluates evidence quality without changing the combined decision score or technical gates. "
                        "Portfolio, macro and news context "
                        "are intentionally outside this version."
                    ),
                },
            },
        }

    def _decision_trust(self, payload: dict[str, Any]) -> dict[str, Any]:
        """DE-CORE-004.4: quantify trust without changing direction or execution."""
        reliability = (payload.get("decision_reliability") or {}).get("decision_reliability") or {}
        evidence = (payload.get("decision_evidence_score") or {}).get("decision_evidence_score") or {}
        gate = (payload.get("decision_evidence_gate") or {}).get("decision_evidence_gate") or {}
        validation = (payload.get("decision_validation_state") or {}).get("decision_validation_state") or {}
        momentum = (payload.get("decision_validation_momentum") or {}).get("decision_validation_momentum") or {}
        contradiction = (payload.get("decision_contradiction_guard") or {}).get("decision_contradiction_guard") or {}
        calibration = (payload.get("decision_calibration") or {}).get("decision_calibration") or {}
        edge = (payload.get("historical_edge") or {}).get("historical_edge") or {}

        validation_state = str(validation.get("validation_state") or "UNAVAILABLE").upper()
        validation_score = {
            "VALIDATED": 90.0, "CONFIRMED": 90.0, "CONDITIONAL": 60.0,
            "UNVALIDATED": 25.0, "UNAVAILABLE": None,
        }.get(validation_state, 50.0 if validation.get("available") else None)

        raw = {
            "evidence": (self._number_or_none(evidence.get("score")), 0.40),
            "reliability": (self._number_or_none(reliability.get("reliability_pct")), 0.25),
            "coherence": (self._number_or_none(contradiction.get("coherence_score")), 0.20),
            "validation": (validation_score, 0.15),
        }
        active_weight = sum(weight for score, weight in raw.values() if score is not None)
        components = {}
        raw_score = None
        if active_weight > 0:
            total = 0.0
            for key, (score, base_weight) in raw.items():
                effective = base_weight / active_weight if score is not None else 0.0
                contribution = score * effective if score is not None else None
                components[key] = {
                    "available": score is not None,
                    "score": round(score, 1) if score is not None else None,
                    "base_weight": base_weight,
                    "effective_weight": round(effective, 4),
                    "contribution": round(contribution, 2) if contribution is not None else None,
                }
                if contribution is not None:
                    total += contribution
            raw_score = self._clamp(total)
        else:
            for key, (_, base_weight) in raw.items():
                components[key] = {"available": False, "score": None, "base_weight": base_weight, "effective_weight": 0.0, "contribution": None}

        gate_state = str(gate.get("gate") or "UNAVAILABLE").upper()
        guard_state = str(contradiction.get("guard_state") or "UNAVAILABLE").upper()
        cap = 100.0
        cap_reason = "NONE"
        if guard_state == "HARD_CONFLICT":
            cap, cap_reason = 39.0, "HARD_CONFLICT"
        elif gate_state == "BLOCKED":
            cap, cap_reason = 49.0, "EVIDENCE_GATE_BLOCKED"
        elif validation_state == "UNVALIDATED":
            cap, cap_reason = 59.0, "DECISION_UNVALIDATED"

        trust_score = min(raw_score, cap) if raw_score is not None else None
        if trust_score is None:
            level = "INSUFFICIENT_EVIDENCE"
        elif trust_score >= 80:
            level = "HIGH"
        elif trust_score >= 65:
            level = "MEDIUM_HIGH"
        elif trust_score >= 50:
            level = "MEDIUM"
        elif trust_score >= 35:
            level = "LOW"
        else:
            level = "VERY_LOW"

        return {
            "available": trust_score is not None,
            "trust_score": round(trust_score, 1) if trust_score is not None else None,
            "raw_trust_score": round(raw_score, 1) if raw_score is not None else None,
            "trust_level": level,
            "coverage_pct": round(sum(1 for x in components.values() if x["available"]) / len(components) * 100.0, 1),
            "components": components,
            "governance_cap": {"applied": cap < 100.0, "cap": cap if cap < 100.0 else None, "reason": cap_reason},
            "evidence_gate": gate_state,
            "validation_state": validation_state,
            "validation_momentum": str(momentum.get("state") or "UNAVAILABLE").upper(),
            "contradiction_guard": guard_state,
            "calibration_readiness": str(calibration.get("readiness") or "INSUFFICIENT_HISTORY").upper(),
            "historical_edge": {
                "available": bool(edge.get("available")),
                "score": self._number_or_none(edge.get("edge_score")),
                "quality": str(edge.get("evidence") or "INSUFFICIENT_HISTORY").upper(),
                "sample_size": int(edge.get("total_completed_samples") or 0),
            },
            "scope": {
                "advisory_only": True,
                "changes_combined_score": False,
                "changes_fusion_weights": False,
                "changes_execution_permission": False,
                "technical_gates_preserved": True,
            },
        }

    def _technical_score(
        self,
        *,
        posture: str,
        conviction: float,
    ) -> float:
        base = self.TECHNICAL_POSTURE_SCORES.get(posture, 50.0)

        # Conviction refines the technical posture without changing its meaning.
        adjustment = (conviction - 50.0) * 0.10

        return self._clamp(base + adjustment)

    @classmethod
    def _fusion_components(
        cls,
        *,
        technical_score: float | None,
        fundamental_score: float | None,
        business_momentum_score: float | None,
        target_weights: dict[str, float] | None = None,
    ) -> dict[str, dict[str, Any]]:
        """Return an auditable base -> regime -> effective fusion calculation."""
        target = target_weights or cls.BASE_FUSION_WEIGHTS
        scores = {
            "technical": technical_score,
            "fundamental": fundamental_score,
            "business_momentum": business_momentum_score,
        }
        active_weight = sum(
            float(target.get(key, cls.BASE_FUSION_WEIGHTS[key]))
            for key, score in scores.items()
            if score is not None
        )
        result: dict[str, dict[str, Any]] = {}
        for key, score in scores.items():
            available = score is not None
            base_weight = cls.BASE_FUSION_WEIGHTS[key]
            regime_weight = float(target.get(key, base_weight))
            effective_weight = (
                regime_weight / active_weight if available and active_weight > 0 else 0.0
            )
            contribution = score * effective_weight if available else None
            result[key] = {
                "available": available,
                "score": round(score, 1) if available else None,
                "base_weight": round(base_weight, 4),
                "regime_weight": round(regime_weight, 4),
                "effective_weight": round(effective_weight, 4),
                "weight_delta": round(regime_weight - base_weight, 4),
                "contribution": round(contribution, 2) if contribution is not None else None,
            }
        return result

    @staticmethod
    def _score_from_components(components: dict[str, dict[str, Any]]) -> float:
        return sum(
            float(item["contribution"])
            for item in components.values()
            if item.get("contribution") is not None
        )

    @staticmethod
    def _combined_score(
        *,
        technical_score: float | None,
        fundamental_score: float | None,
        business_momentum_score: float | None,
    ) -> float:
        weighted: list[tuple[float, float]] = []

        # DE-CORE-004.1 target architecture:
        # Technical timing 45%, Fundamental quality/direction 35%,
        # Adaptive Business Momentum 20%.
        if technical_score is not None:
            weighted.append((technical_score, 0.45))

        if fundamental_score is not None:
            weighted.append((fundamental_score, 0.35))

        if business_momentum_score is not None:
            weighted.append((business_momentum_score, 0.20))

        if not weighted:
            return 50.0

        total_weight = sum(weight for _, weight in weighted)
        return sum(score * weight for score, weight in weighted) / total_weight

    @staticmethod
    def _effective_fusion_weights(
        *,
        technical_available: bool,
        fundamental_available: bool,
        business_momentum_available: bool,
    ) -> dict[str, float]:
        base = {
            "technical": 0.45 if technical_available else 0.0,
            "fundamental": 0.35 if fundamental_available else 0.0,
            "business_momentum": 0.20 if business_momentum_available else 0.0,
        }
        total = sum(base.values())

        if total <= 0:
            return {
                "technical": 0.0,
                "fundamental": 0.0,
                "business_momentum": 0.0,
            }

        return {
            key: round(value / total, 4)
            for key, value in base.items()
        }

    @staticmethod
    def _business_divergence(
        *,
        technical_score: float | None,
        business_momentum_score: float | None,
    ) -> dict[str, Any]:
        if technical_score is None or business_momentum_score is None:
            return {
                "available": False,
                "state": "UNAVAILABLE",
                "spread": None,
                "severity": "NONE",
            }

        spread = business_momentum_score - technical_score
        magnitude = abs(spread)

        if magnitude < 15:
            state = "ALIGNED"
            severity = "LOW"
        elif spread >= 30:
            state = "POSITIVE_BUSINESS_DIVERGENCE"
            severity = "HIGH"
        elif spread >= 15:
            state = "POSITIVE_BUSINESS_DIVERGENCE"
            severity = "MEDIUM"
        elif spread <= -30:
            state = "NEGATIVE_BUSINESS_DIVERGENCE"
            severity = "HIGH"
        else:
            state = "NEGATIVE_BUSINESS_DIVERGENCE"
            severity = "MEDIUM"

        return {
            "available": True,
            "state": state,
            "spread": round(spread, 1),
            "severity": severity,
        }

    @staticmethod
    def _alignment_score(
        *,
        technical_score: float | None,
        fundamental_score: float | None,
    ) -> float:
        if technical_score is None or fundamental_score is None:
            return 50.0

        spread = abs(technical_score - fundamental_score)
        return max(0.0, min(100.0, 100.0 - spread))

    @staticmethod
    def _alignment_state(score: float) -> str:
        if score >= 85:
            return "STRONG_ALIGNMENT"
        if score >= 70:
            return "ALIGNED"
        if score >= 55:
            return "PARTIAL_ALIGNMENT"
        return "CONFLICT"

    def _timing_gate(
        self,
        *,
        technical_posture: str,
        technical_available: bool,
    ) -> str:
        if not technical_available:
            return "TECHNICAL_UNAVAILABLE"

        if technical_posture == "EXIT":
            return "CAPITAL_PROTECTION"
        if technical_posture == "REDUCE":
            return "REDUCE_EXPOSURE"
        if technical_posture == "WAIT":
            return "WAIT"
        if technical_posture == "WATCH":
            return "MONITOR"
        if technical_posture == "PREPARE":
            return "PREPARE"
        if technical_posture in {"ENTER", "ADD"}:
            return "TECHNICALLY_ACTIONABLE"

        return "MONITOR"

    def _integrated_posture(
        self,
        *,
        combined_score: float,
        technical_posture: str,
        technical_available: bool,
        fundamental_stance: str,
    ) -> str:
        # Technical capital-protection gates cannot be relaxed by fundamentals.
        if technical_available:
            if technical_posture == "EXIT":
                return "DEFENSIVE"
            if technical_posture == "REDUCE":
                return "CAUTIOUS"
            if technical_posture == "WAIT":
                if fundamental_stance in {
                    "VERY_POSITIVE",
                    "POSITIVE",
                    "CONSTRUCTIVE",
                }:
                    return "CONSTRUCTIVE_BUT_WAIT"
                return "NEUTRAL"

        if combined_score >= 78:
            return "FAVORABLE"
        if combined_score >= 65:
            return "CONSTRUCTIVE"
        if combined_score >= 52:
            return "SELECTIVE"
        if combined_score >= 40:
            return "CAUTIOUS"
        return "DEFENSIVE"

    @staticmethod
    def _confidence(
        *,
        technical_conviction: float,
        fundamental_conviction: str,
        technical_available: bool,
        fundamental_available: bool,
        business_momentum_confidence: str,
        business_momentum_available: bool,
        alignment_score: float,
    ) -> str:
        fundamental_map = {
            "HIGH": 85.0,
            "MEDIUM": 65.0,
            "LOW": 40.0,
        }

        scores: list[float] = []

        if technical_available:
            scores.append(technical_conviction)

        if fundamental_available:
            scores.append(fundamental_map.get(fundamental_conviction, 40.0))

        if business_momentum_available:
            scores.append(
                fundamental_map.get(business_momentum_confidence, 40.0)
            )

        if not scores:
            return "LOW"

        average = sum(scores) / len(scores)

        if alignment_score < 55:
            average -= 15.0
        elif alignment_score < 70:
            average -= 7.0

        if average >= 75:
            return "HIGH"
        if average >= 55:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _decision_regime(
        *,
        technical_posture: str,
        technical_available: bool,
        technical_risk_state: str,
        technical_execution_state: str,
        alignment: str,
        business_divergence: dict[str, Any],
        combined_score: float,
    ) -> dict[str, Any]:
        divergence = str(business_divergence.get("state") or "UNAVAILABLE").upper()

        if technical_available and (technical_posture == "EXIT" or technical_risk_state == "CRITICAL"):
            state, priority, severity = "CAPITAL_PROTECTION", "TECHNICAL_RISK", "HIGH"
        elif technical_available and technical_posture == "REDUCE":
            state, priority, severity = "DEFENSIVE", "TECHNICAL_RISK", "HIGH"
        elif technical_available and technical_posture == "WAIT":
            state, priority, severity = "TIMING_BLOCKED", "TECHNICAL_TIMING", "MEDIUM"
        elif divergence == "POSITIVE_BUSINESS_DIVERGENCE":
            state, priority = "RECOVERY_WATCH", "CONFIRMATION"
            severity = str(business_divergence.get("severity") or "MEDIUM").upper()
        elif divergence == "NEGATIVE_BUSINESS_DIVERGENCE":
            state, priority = "PRICE_AHEAD_OF_BUSINESS", "FUNDAMENTAL_CONFIRMATION"
            severity = str(business_divergence.get("severity") or "MEDIUM").upper()
        elif alignment == "CONFLICT":
            state, priority, severity = "CROSS_ENGINE_CONFLICT", "CONFIRMATION", "MEDIUM"
        elif alignment in {"STRONG_ALIGNMENT", "ALIGNED"} and combined_score >= 65:
            state, priority, severity = "CONFIRMED_CONSTRUCTIVE", "BALANCED", "LOW"
        elif alignment in {"STRONG_ALIGNMENT", "ALIGNED"} and combined_score < 40:
            state, priority, severity = "CONFIRMED_DEFENSIVE", "CAPITAL_PROTECTION", "HIGH"
        else:
            state, priority, severity = "TRANSITION", "BALANCED", "MEDIUM"

        return {
            "state": state,
            "priority": priority,
            "severity": severity,
            "technical_risk_state": technical_risk_state,
            "technical_execution_state": technical_execution_state,
        }

    @staticmethod
    def _conflict_resolution(
        *,
        decision_regime: dict[str, Any],
        technical_posture: str,
        technical_available: bool,
        fundamental_stance: str,
        business_momentum_regime: str,
        business_divergence: dict[str, Any],
        timing_gate: str,
    ) -> dict[str, Any]:
        regime = str(decision_regime.get("state") or "TRANSITION").upper()
        divergence = str(business_divergence.get("state") or "UNAVAILABLE").upper()
        permission, strategic_state, resolution = "MONITOR", "MIXED", "WAIT_FOR_CONFIRMATION"

        if regime == "CAPITAL_PROTECTION":
            permission, strategic_state, resolution = "BLOCKED", "DEFENSIVE", "TECHNICAL_RISK_DOMINATES"
        elif regime == "DEFENSIVE":
            permission, strategic_state = "REDUCE_ONLY", "DEFENSIVE"
            resolution = "PRESERVE_CAPITAL_WHILE_MONITORING_FUNDAMENTALS"
        elif regime == "TIMING_BLOCKED":
            permission, strategic_state = "BLOCKED", "WATCH"
            resolution = "FUNDAMENTALS_CANNOT_OVERRIDE_TIMING_GATE"
        elif regime == "RECOVERY_WATCH":
            permission = "ACTIONABLE" if technical_posture in {"ENTER", "ADD"} else "MONITOR"
            strategic_state, resolution = "IMPROVING", "BUSINESS_IMPROVEMENT_AWAITS_PRICE_CONFIRMATION"
        elif regime == "PRICE_AHEAD_OF_BUSINESS":
            permission = "ACTIONABLE_WITH_CAUTION" if technical_posture in {"ENTER", "ADD", "PREPARE"} else "MONITOR"
            strategic_state, resolution = "CAUTION", "PRICE_STRENGTH_AWAITS_BUSINESS_CONFIRMATION"
        elif regime == "CONFIRMED_CONSTRUCTIVE":
            permission = "ACTIONABLE" if technical_posture in {"ENTER", "ADD"} else "MONITOR"
            strategic_state, resolution = "CONSTRUCTIVE", "ENGINES_CONFIRM_DIRECTION"
        elif regime == "CONFIRMED_DEFENSIVE":
            permission, strategic_state, resolution = "BLOCKED", "DEFENSIVE", "ENGINES_CONFIRM_DEFENSIVE_POSTURE"

        # Hard invariant: Fundamental/Business cannot relax technical protection gates.
        if technical_available and technical_posture == "EXIT":
            permission, resolution = "EXIT_ONLY", "TECHNICAL_EXIT_GATE_DOMINATES"
        elif technical_available and technical_posture == "REDUCE":
            permission, resolution = "REDUCE_ONLY", "TECHNICAL_REDUCTION_GATE_DOMINATES"
        elif technical_available and technical_posture == "WAIT":
            permission, resolution = "BLOCKED", "TECHNICAL_WAIT_GATE_DOMINATES"

        return {
            "strategic_state": strategic_state,
            "execution_permission": permission,
            "resolution": resolution,
            "timing_gate": timing_gate,
            "fundamental_stance": fundamental_stance,
            "business_momentum_regime": business_momentum_regime,
            "business_divergence": divergence,
            "technical_gate_preserved": bool(
                technical_available and technical_posture in {"WAIT", "REDUCE", "EXIT"}
            ),
        }

    @staticmethod
    def _supporting_evidence(
        *,
        technical: dict[str, Any],
        fundamental_decision: dict[str, Any],
        business_momentum: dict[str, Any],
    ) -> list[str]:
        evidence: list[str] = []

        rationale = technical.get("rationale")
        if rationale:
            evidence.append(str(rationale))

        for item in fundamental_decision.get("thesis") or []:
            if item not in evidence:
                evidence.append(str(item))

        for item in fundamental_decision.get("catalysts") or []:
            if item not in evidence:
                evidence.append(str(item))

        for item in business_momentum.get("evidence") or []:
            if item not in evidence:
                evidence.append(str(item))

        return evidence[:12]

    @staticmethod
    def _conflicts(
        *,
        technical_posture: str,
        fundamental_stance: str,
        technical: dict[str, Any],
        fundamental_decision: dict[str, Any],
        business_divergence: dict[str, Any],
    ) -> list[str]:
        conflicts: list[str] = []

        positive_fundamental = fundamental_stance in {
            "VERY_POSITIVE",
            "POSITIVE",
            "CONSTRUCTIVE",
        }

        if technical_posture in {"WAIT", "REDUCE", "EXIT"} and positive_fundamental:
            conflicts.append(
                "Fundamental backdrop is constructive while technical timing "
                f"remains {technical_posture.lower()}."
            )

        if technical_posture in {"ENTER", "ADD"} and fundamental_stance in {
            "CAUTIOUS",
            "NEGATIVE",
        }:
            conflicts.append(
                "Technical setup is actionable while fundamental stance is "
                f"{fundamental_stance.lower()}."
            )

        blockers = technical.get("blockers")
        if isinstance(blockers, list) and blockers:
            conflicts.append(
                f"{len(blockers)} technical blocker(s) remain active."
            )

        for item in fundamental_decision.get("risks") or []:
            conflicts.append(str(item))

        divergence_state = str(
            business_divergence.get("state") or ""
        ).upper()

        if divergence_state == "POSITIVE_BUSINESS_DIVERGENCE":
            conflicts.append(
                "Business momentum materially exceeds current technical strength; "
                "fundamentals/operations may be improving ahead of price confirmation."
            )
        elif divergence_state == "NEGATIVE_BUSINESS_DIVERGENCE":
            conflicts.append(
                "Technical strength materially exceeds business momentum; "
                "price action may be running ahead of operating fundamentals."
            )

        # Ordered deduplication.
        return list(dict.fromkeys(conflicts))[:12]

    @staticmethod
    def _thesis(
        *,
        integrated_posture: str,
        technical_posture: str,
        fundamental_stance: str,
        timing_gate: str,
        alignment: str,
        business_momentum_regime: str,
        business_momentum_available: bool,
        business_divergence: dict[str, Any],
    ) -> str:
        business_clause = (
            f" Business momentum regime is "
            f"{business_momentum_regime.replace('_', ' ')}."
            if business_momentum_available
            else ""
        )

        divergence_state = str(
            business_divergence.get("state") or "UNAVAILABLE"
        ).replace("_", " ")

        divergence_clause = (
            f" Business/technical relationship: {divergence_state}."
            if business_divergence.get("available")
            else ""
        )

        return (
            f"QMI cross-engine posture is {integrated_posture.replace('_', ' ')}. "
            f"Technical posture is {technical_posture}, fundamental stance is "
            f"{fundamental_stance.replace('_', ' ')}, and cross-engine alignment "
            f"is {alignment.replace('_', ' ')}. Timing gate: "
            f"{timing_gate.replace('_', ' ')}."
            f"{business_clause}{divergence_clause}"
        )

    @staticmethod
    def _to_dict(value: Any) -> dict[str, Any]:
        if isinstance(value, dict):
            return value

        model_dump = getattr(value, "model_dump", None)
        if callable(model_dump):
            result = model_dump()
            return result if isinstance(result, dict) else {}

        return {}

    @staticmethod
    def _number(value: Any, default: float = 0.0) -> float:
        try:
            if value is None:
                return float(default)
            return float(value)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def _number_or_none(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _clamp(value: float) -> float:
        return max(0.0, min(100.0, float(value)))

    def _insufficient(self, symbol: str) -> dict[str, Any]:
        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "insufficient_data",
            "symbol": symbol.strip().upper(),
            "qmi_decision": {
                "available": False,
                "integrated_posture": "UNKNOWN",
                "combined_score": None,
                "confidence": "LOW",
                "reason": (
                    "Neither technical decision synthesis nor fundamental "
                    "decision data is available."
                ),
            },
        }
