"""
FA-DECISION-001 — Fundamental Decision Engine v2

Fuses the normalized Fundamental Intelligence engines into one decision layer.
Missing inputs are excluded and the remaining weights are renormalized.
"""

from __future__ import annotations

from typing import Any

from app.fundamental.schemas import FundamentalDecision


class FundamentalDecisionEngine:
    ENGINE_ID = "FA-DECISION-001"
    VERSION = "0.1.1"

    BASE_WEIGHTS = {
        "growth": 0.18,
        "profitability": 0.20,
        "financial_health": 0.17,
        "cash_flow": 0.18,
        "valuation": 0.12,
        "expectations": 0.15,
    }

    def analyze(
        self,
        *,
        data: Any,
        growth_trend: dict[str, Any],
        profitability_quality: dict[str, Any],
        financial_health: dict[str, Any],
        cash_flow_intelligence: dict[str, Any],
        valuation_intelligence: dict[str, Any],
        expectations_intelligence: dict[str, Any],
        company_intelligence: dict[str, Any] | None = None,
        business_momentum: dict[str, Any] | None = None,
        legacy_score: float | None = None,
    ) -> FundamentalDecision:
        components = {
            "growth": self._growth_score(growth_trend),
            "profitability": self._num(profitability_quality.get("quality_score")),
            "financial_health": self._num(financial_health.get("financial_health_score")),
            "cash_flow": self._num(cash_flow_intelligence.get("cash_flow_score")),
            "valuation": self._num(valuation_intelligence.get("valuation_score")),
            "expectations": self._num(expectations_intelligence.get("expectations_score")),
        }

        active = {
            name: score
            for name, score in components.items()
            if score is not None
        }

        weighted_total = sum(self.BASE_WEIGHTS[name] for name in active)

        explainability = {}
        for name, raw_score in components.items():
            available = raw_score is not None
            base_weight = self.BASE_WEIGHTS[name]
            effective_weight = (
                base_weight / weighted_total
                if available and weighted_total > 0
                else 0.0
            )
            contribution = (
                raw_score * effective_weight
                if available
                else None
            )
            explainability[name] = {
                "available": available,
                "score": round(raw_score, 1) if available else None,
                "base_weight": round(base_weight, 4),
                "effective_weight": round(effective_weight, 4),
                "contribution": round(contribution, 2) if contribution is not None else None,
            }

        if active and weighted_total > 0:
            decision_score = round(
                sum(
                    item["contribution"]
                    for item in explainability.values()
                    if item["contribution"] is not None
                ),
                1,
            )
        else:
            decision_score = self._num(legacy_score)

        active_components = len(active)
        total_components = len(self.BASE_WEIGHTS)
        coverage_pct = round((active_components / total_components) * 100.0, 1)
        weights_renormalized = 0 < active_components < total_components

        # Company-specific information is intentionally contextual in v0.1.0.
        # It can strengthen evidence, but it does not alter the numerical score
        # until a stable company-specific scoring contract exists.
        company_state = str(
            (company_intelligence or {}).get("company_specific", {}).get("state")
            or (company_intelligence or {}).get("company", {}).get("state")
            or ""
        ).upper()

        momentum_score = self._num((business_momentum or {}).get("score"))
        momentum_regime = str((business_momentum or {}).get("regime") or "").upper()

        stance = self._stance(decision_score)
        conviction = self._conviction(
            active_count=len(active),
            completeness=self._num(
                getattr(getattr(data, "data_quality", None), "completeness_score", None)
            ),
        )

        thesis: list[str] = []
        catalysts: list[str] = []
        risks: list[str] = []

        self._append_component_evidence(
            thesis=thesis,
            catalysts=catalysts,
            risks=risks,
            components=components,
        )

        expectations_state = str(
            expectations_intelligence.get("expectations_state") or ""
        ).upper()
        cash_state = str(cash_flow_intelligence.get("cash_flow_state") or "").upper()
        valuation_state = str(
            valuation_intelligence.get("valuation_state") or ""
        ).upper()

        if expectations_state in {"STRONG", "POSITIVE", "SUPPORTIVE"}:
            catalysts.append("Forward expectations are supportive")
        elif expectations_state in {"WEAK", "NEGATIVE", "DETERIORATING"}:
            risks.append("Forward expectations remain weak")

        if cash_state in {"WEAK", "NEGATIVE", "STRESSED"}:
            risks.append("Cash-flow profile remains weak")

        if valuation_state in {"ELEVATED", "EXPENSIVE", "HIGH"}:
            risks.append("Valuation context is elevated")

        if momentum_score is not None:
            if momentum_score >= 65:
                catalysts.append("Business momentum is supportive")
            elif momentum_score < 40:
                risks.append("Business momentum is weak")

        if momentum_regime in {"EXPANDING", "ACCELERATING", "STRONG"}:
            catalysts.append(f"Business momentum regime is {momentum_regime.lower()}")
        elif momentum_regime in {"CONTRACTING", "DETERIORATING", "WEAK"}:
            risks.append(f"Business momentum regime is {momentum_regime.lower()}")

        if company_state in {"STRONG", "POSITIVE", "SUPPORTIVE"}:
            catalysts.append("Company-specific intelligence is supportive")
        elif company_state in {"WEAK", "NEGATIVE", "DETERIORATING"}:
            risks.append("Company-specific intelligence is weak")

        return FundamentalDecision(
            engine_id=self.ENGINE_ID,
            version=self.VERSION,
            stance=stance,
            decision_score=decision_score,
            conviction=conviction,
            quality_score=components["profitability"],
            regime_score=components["growth"],
            legacy_score=self._num(legacy_score),
            components=explainability,
            active_components=active_components,
            total_components=total_components,
            coverage_pct=coverage_pct,
            weights_renormalized=weights_renormalized,
            thesis=self._unique(thesis),
            catalysts=self._unique(catalysts),
            risks=self._unique(risks),
        )

    @staticmethod
    def _growth_score(payload: dict[str, Any]) -> float | None:
        summary = payload.get("summary") or {}
        for key in ("growth_score", "score"):
            value = FundamentalDecisionEngine._num(summary.get(key))
            if value is not None:
                return FundamentalDecisionEngine._bounded(value)

        avg_growth = FundamentalDecisionEngine._num(
            summary.get("average_latest_growth_pct")
        )
        if avg_growth is None:
            return None

        # Converts realized growth into a bounded 0–100 context score.
        return FundamentalDecisionEngine._bounded(50.0 + avg_growth * 1.5)

    @staticmethod
    def _append_component_evidence(*, thesis, catalysts, risks, components):
        labels = {
            "growth": "Growth",
            "profitability": "Profitability quality",
            "financial_health": "Financial health",
            "cash_flow": "Cash flow",
            "valuation": "Valuation",
            "expectations": "Expectations",
        }

        for name, score in components.items():
            if score is None:
                continue
            label = labels[name]
            if score >= 70:
                catalysts.append(f"{label} is strong ({score:.1f})")
            elif score >= 55:
                thesis.append(f"{label} is supportive ({score:.1f})")
            elif score < 40:
                risks.append(f"{label} is weak ({score:.1f})")

    @staticmethod
    def _stance(score: float | None) -> str:
        if score is None:
            return "UNKNOWN"
        if score >= 80:
            return "VERY_POSITIVE"
        if score >= 68:
            return "POSITIVE"
        if score >= 55:
            return "CONSTRUCTIVE"
        if score >= 42:
            return "CAUTIOUS"
        return "NEGATIVE"

    @staticmethod
    def _conviction(*, active_count: int, completeness: float | None) -> str:
        if active_count >= 5 and completeness is not None and completeness >= 75:
            return "HIGH"
        if active_count >= 4 and completeness is not None and completeness >= 55:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _bounded(value: float) -> float:
        return round(max(0.0, min(100.0, value)), 1)

    @staticmethod
    def _num(value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            number = float(value)
            return None if number != number else number
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _unique(items: list[str]) -> list[str]:
        return list(dict.fromkeys(items))
