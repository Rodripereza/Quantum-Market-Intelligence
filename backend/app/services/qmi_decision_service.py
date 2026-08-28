from __future__ import annotations

from typing import Any


class QMIDecisionService:
    """
    DE-CORE-004.0 — Cross-Engine Decision Fusion

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

    ENGINE_ID = "DE-CORE-004.0"
    ENGINE = "QMI Cross-Engine Decision Fusion"
    VERSION = "0.1.0"

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

        technical_available = bool(technical.get("available", False))
        fundamental_available = bool(fundamental_decision)

        if not technical_available and not fundamental_available:
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

        combined_score = self._combined_score(
            technical_score=technical_score if technical_available else None,
            fundamental_score=fundamental_score if fundamental_available else None,
        )

        alignment_score = self._alignment_score(
            technical_score=technical_score if technical_available else None,
            fundamental_score=fundamental_score if fundamental_available else None,
        )

        alignment = self._alignment_state(alignment_score)

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
            alignment_score=alignment_score,
        )

        supporting_evidence = self._supporting_evidence(
            technical=technical,
            fundamental_decision=fundamental_decision,
        )
        conflicts = self._conflicts(
            technical_posture=technical_posture,
            fundamental_stance=fundamental_stance,
            technical=technical,
            fundamental_decision=fundamental_decision,
        )

        thesis = self._thesis(
            integrated_posture=integrated_posture,
            technical_posture=technical_posture,
            fundamental_stance=fundamental_stance,
            timing_gate=timing_gate,
            alignment=alignment,
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
                "thesis": thesis,
                "supporting_evidence": supporting_evidence,
                "conflicts": conflicts,
                "scope": {
                    "technical": True,
                    "fundamental": True,
                    "portfolio": False,
                    "macro": False,
                    "news_sentiment": False,
                    "automatic_execution": False,
                    "buy_hold_sell_signal": False,
                    "note": (
                        "DE-CORE-004.0 fuses technical timing with fundamental "
                        "quality/direction. Portfolio, macro and news context "
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
    ) -> float:
        weighted: list[tuple[float, float]] = []

        if technical_score is not None:
            weighted.append((technical_score, 0.45))

        if fundamental_score is not None:
            weighted.append((fundamental_score, 0.55))

        if not weighted:
            return 50.0

        total_weight = sum(weight for _, weight in weighted)
        return sum(score * weight for score, weight in weighted) / total_weight

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

        return evidence[:10]

    @staticmethod
    def _conflicts(
        *,
        technical_posture: str,
        fundamental_stance: str,
        technical: dict[str, Any],
        fundamental_decision: dict[str, Any],
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
    ) -> str:
        return (
            f"QMI cross-engine posture is {integrated_posture.replace('_', ' ')}. "
            f"Technical posture is {technical_posture}, fundamental stance is "
            f"{fundamental_stance.replace('_', ' ')}, and cross-engine alignment "
            f"is {alignment.replace('_', ' ')}. Timing gate: "
            f"{timing_gate.replace('_', ' ')}."
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
