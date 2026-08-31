from __future__ import annotations

from typing import Any


class QMIDecisionService:
    """
    DE-CORE-004.1 — Cross-Engine Decision Fusion + Business Momentum

    Combines the already-finalized Technical Decision Synthesis
    (DE-TA-015.0) with the Fundamental Decision Engine (DE-FA-004.0).

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

    ENGINE_ID = "DE-CORE-004.1"
    ENGINE = "QMI Cross-Engine Decision Fusion"
    VERSION = "0.1.1"

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

    def analyze(
        self,
        *,
        symbol: str,
        technical_response: dict[str, Any],
        fundamental_response: Any,
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

        combined_score = self._combined_score(
            technical_score=technical_score if technical_available else None,
            fundamental_score=fundamental_score if fundamental_available else None,
            business_momentum_score=(
                business_momentum_score
                if business_momentum_available
                else None
            ),
        )

        alignment_score = self._alignment_score(
            technical_score=technical_score if technical_available else None,
            fundamental_score=fundamental_score if fundamental_available else None,
        )

        alignment = self._alignment_state(alignment_score)

        business_divergence = self._business_divergence(
            technical_score=technical_score if technical_available else None,
            business_momentum_score=(
                business_momentum_score
                if business_momentum_available
                else None
            ),
        )

        timing_gate = self._timing_gate(
            technical_posture=technical_posture,
            technical_available=technical_available,
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
                "fusion_weights": self._effective_fusion_weights(
                    technical_available=technical_available,
                    fundamental_available=fundamental_available,
                    business_momentum_available=business_momentum_available,
                ),
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
                        "DE-CORE-004.1 fuses technical timing, fundamental "
                        "quality/direction and adaptive business momentum. "
                        "Portfolio, macro and news context "
                        "are intentionally outside this version."
                    ),
                },
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
