from __future__ import annotations

from typing import Any, Dict, Optional

from app.fundamental.schemas import FundamentalAnalysisResult


class AdaptiveBusinessMomentumEngine:
    """
    DE-FA-BM-001.1 — Adaptive Business Momentum / Factor Family Architecture

    Comparable 0–100 business-momentum score across tickers.

    Architecture:
      Growth Family              30%
      Profitability Family       25%
      Cash & Quality Family      25%
      Operating Drivers Family   20% max

    Core rules:
    - unavailable metrics are excluded, never scored as zero;
    - weights are normalized inside each family;
    - missing universal families are redistributed across available universal families;
    - company-specific operating drivers are capped at 20% of the final score;
    - if no operating drivers exist, universal families automatically receive 100%;
    - company-specific depth therefore cannot structurally advantage one ticker.
    """

    ENGINE_ID = "DE-FA-BM-001.1"
    VERSION = "0.1.1"

    UNIVERSAL_FAMILY_WEIGHTS = {
        "growth": 0.30,
        "profitability": 0.25,
        "cash_quality": 0.25,
    }
    OPERATING_DRIVER_CAP = 0.20

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
        return max(low, min(high, float(value)))

    @classmethod
    def _linear_score(
        cls,
        value: Optional[float],
        bearish: float,
        bullish: float,
    ) -> Optional[float]:
        if value is None:
            return None
        if bullish == bearish:
            return 50.0
        normalized = (float(value) - bearish) / (bullish - bearish)
        return cls._clamp(normalized * 100.0)

    @staticmethod
    def _state_score(state: Optional[str]) -> Optional[float]:
        if not state:
            return None

        mapping = {
            "STRONG": 85.0,
            "GOOD": 72.0,
            "HEALTHY": 72.0,
            "IMPROVING": 75.0,
            "RECOVERING": 70.0,
            "EXPANSION": 78.0,
            "STRONG_EXPANSION": 90.0,
            "STABLE": 50.0,
            "ADEQUATE": 55.0,
            "NEUTRAL": 50.0,
            "MIXED": 45.0,
            "WEAK": 30.0,
            "POOR": 20.0,
            "DETERIORATING": 25.0,
            "SLOWDOWN": 35.0,
            "CONTRACTION": 22.0,
            "LOSS_MAKING": 25.0,
            "ACCELERATING": 80.0,
            "DECELERATING": 25.0,
            "RISING": 70.0,
            "FALLING": 30.0,
        }
        return mapping.get(str(state).upper())

    def _component(
        self,
        *,
        label: str,
        score: Optional[float],
        source: str,
        family: str,
        intra_weight: float,
        value: Any = None,
        state: Optional[str] = None,
        confidence: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "label": label,
            "family": family,
            "available": score is not None,
            "score": round(float(score), 1) if score is not None else None,
            "base_weight": round(float(intra_weight), 4),
            "effective_weight": 0.0,
            "source": source,
            "value": value,
            "state": state,
            "confidence": confidence,
        }

    def _universal_components(
        self,
        data: FundamentalAnalysisResult,
    ) -> Dict[str, Dict[str, Any]]:
        earnings_value = (
            data.growth.earnings_growth
            if data.growth.earnings_growth is not None
            else data.trends.net_income_yoy
        )

        cash_flow_block = data.statement_intelligence.cash_flow
        cash_flow_score = (
            cash_flow_block.score
            if cash_flow_block.score is not None
            else self._state_score(data.statement_intelligence.cash_flow_state)
        )

        balance_block = data.statement_intelligence.balance_sheet
        balance_score = (
            balance_block.score
            if balance_block.score is not None
            else self._state_score(data.statement_intelligence.balance_sheet_state)
        )

        quality = data.quality_intelligence

        return {
            "revenue_growth": self._component(
                label="Revenue Growth",
                score=self._linear_score(data.growth.revenue_growth, -0.20, 0.40),
                source="fundamental.growth.revenue_growth",
                family="growth",
                intra_weight=0.67,
                value=data.growth.revenue_growth,
            ),
            "growth_persistence": self._component(
                label="Growth Persistence",
                score=self._linear_score(data.trends.revenue_cagr_3y, -0.10, 0.30),
                source="fundamental.trends.revenue_cagr_3y",
                family="growth",
                intra_weight=0.33,
                value=data.trends.revenue_cagr_3y,
            ),
            "earnings_momentum": self._component(
                label="Earnings Momentum",
                score=self._linear_score(earnings_value, -0.50, 0.50),
                source=(
                    "fundamental.growth.earnings_growth"
                    if data.growth.earnings_growth is not None
                    else "fundamental.trends.net_income_yoy"
                ),
                family="profitability",
                intra_weight=0.50,
                value=earnings_value,
            ),
            "margin_momentum": self._component(
                label="Margin Momentum",
                score=self._state_score(data.statement_intelligence.margin_trend),
                source="fundamental.statement_intelligence.margin_trend",
                family="profitability",
                intra_weight=0.50,
                state=data.statement_intelligence.margin_trend,
                confidence=data.statement_intelligence.confidence,
            ),
            "cash_flow_momentum": self._component(
                label="Cash Flow Momentum",
                score=cash_flow_score,
                source="fundamental.statement_intelligence.cash_flow",
                family="cash_quality",
                intra_weight=0.375,
                state=data.statement_intelligence.cash_flow_state,
                confidence=cash_flow_block.confidence,
            ),
            "balance_sheet_momentum": self._component(
                label="Balance Sheet Support",
                score=balance_score,
                source="fundamental.statement_intelligence.balance_sheet",
                family="cash_quality",
                intra_weight=0.25,
                state=data.statement_intelligence.balance_sheet_state,
                confidence=balance_block.confidence,
            ),
            "fundamental_quality": self._component(
                label="Fundamental Quality",
                score=quality.quality_score,
                source="fundamental.quality_intelligence.quality_score",
                family="cash_quality",
                intra_weight=0.375,
                state=quality.quality_regime,
                confidence=quality.confidence,
            ),
        }

    def _operating_components(
        self,
        company_specific: Optional[Dict[str, Any]],
    ) -> Dict[str, Dict[str, Any]]:
        if not company_specific:
            return {}

        nio = company_specific.get("nio_delivery_momentum")
        if not isinstance(nio, dict):
            return {}

        nio_components = nio.get("components") or {}
        asp = nio_components.get("asp_momentum") or {}
        revenue = nio_components.get("revenue_momentum") or {}

        # Revenue is deliberately not dominant here: it is correlated with the
        # universal Revenue Growth factor. Delivery volume carries the largest
        # operating-driver weight, ASP captures monetization/mix, and LFL revenue
        # is a confirmation signal.
        return {
            "nio_delivery_momentum": self._component(
                label="NIO Delivery Momentum",
                score=nio.get("score"),
                source="company_intelligence.nio.delivery_momentum.score",
                family="operating_drivers",
                intra_weight=0.50,
                state=nio.get("trend"),
                confidence=nio.get("confidence"),
            ),
            "nio_asp_momentum": self._component(
                label="NIO ASP Momentum",
                score=asp.get("score"),
                source="company_intelligence.nio.delivery_momentum.components.asp_momentum",
                family="operating_drivers",
                intra_weight=0.25,
                value=asp.get("qoq_pct"),
                state=asp.get("trend"),
            ),
            "nio_revenue_momentum": self._component(
                label="NIO Revenue Momentum",
                score=revenue.get("score"),
                source="company_intelligence.nio.delivery_momentum.components.revenue_momentum",
                family="operating_drivers",
                intra_weight=0.25,
                value=revenue.get("qoq_pct"),
                state=revenue.get("comparison"),
            ),
        }

    @staticmethod
    def _family_score(
        components: Dict[str, Dict[str, Any]],
        family: str,
    ) -> Dict[str, Any]:
        members = {
            key: item
            for key, item in components.items()
            if item["family"] == family
        }
        available = {
            key: item
            for key, item in members.items()
            if item["available"] and item["score"] is not None
        }

        active_base = sum(item["base_weight"] for item in available.values())
        if active_base <= 0:
            return {
                "available": False,
                "score": None,
                "coverage_pct": 0.0,
                "active_components": 0,
                "total_components": len(members),
                "components": list(members.keys()),
            }

        score = sum(
            item["score"] * (item["base_weight"] / active_base)
            for item in available.values()
        )
        total_base = sum(item["base_weight"] for item in members.values())
        coverage = (
            active_base / total_base * 100.0
            if total_base > 0
            else 0.0
        )

        return {
            "available": True,
            "score": round(score, 1),
            "coverage_pct": round(min(100.0, coverage), 1),
            "active_components": len(available),
            "total_components": len(members),
            "components": list(members.keys()),
        }

    def analyze(
        self,
        data: FundamentalAnalysisResult,
        company_specific: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        components = self._universal_components(data)
        components.update(self._operating_components(company_specific))

        families = {
            "growth": self._family_score(components, "growth"),
            "profitability": self._family_score(components, "profitability"),
            "cash_quality": self._family_score(components, "cash_quality"),
            "operating_drivers": self._family_score(components, "operating_drivers"),
        }

        available_universal = [
            name
            for name in self.UNIVERSAL_FAMILY_WEIGHTS
            if families[name]["available"]
        ]
        universal_base = sum(
            self.UNIVERSAL_FAMILY_WEIGHTS[name]
            for name in available_universal
        )

        operating_available = families["operating_drivers"]["available"]
        operating_weight = self.OPERATING_DRIVER_CAP if operating_available else 0.0
        universal_pool = 1.0 - operating_weight

        family_effective_weights: Dict[str, float] = {}

        if universal_base > 0:
            for name in available_universal:
                family_effective_weights[name] = (
                    universal_pool
                    * self.UNIVERSAL_FAMILY_WEIGHTS[name]
                    / universal_base
                )

        if operating_available:
            family_effective_weights["operating_drivers"] = operating_weight

        if not family_effective_weights:
            return {
                "engine": "Adaptive Business Momentum Engine",
                "engine_id": self.ENGINE_ID,
                "version": self.VERSION,
                "score": None,
                "regime": "UNAVAILABLE",
                "trend": "UNKNOWN",
                "confidence": "LOW",
                "coverage_pct": 0.0,
                "active_components": 0,
                "total_components": len(components),
                "adaptive_weighting": True,
                "factor_family_architecture": True,
                "operating_driver_cap_pct": self.OPERATING_DRIVER_CAP * 100.0,
                "families": families,
                "components": components,
                "excluded_components": [
                    item["label"] for item in components.values()
                ],
                "evidence": [],
                "risks": ["No valid business-momentum components are available."],
            }

        # Assign final component effective weights for auditability.
        for family_name, family_weight in family_effective_weights.items():
            available_members = {
                key: item
                for key, item in components.items()
                if item["family"] == family_name
                and item["available"]
                and item["score"] is not None
            }
            active_base = sum(
                item["base_weight"] for item in available_members.values()
            )
            if active_base <= 0:
                continue

            for item in available_members.values():
                item["effective_weight"] = round(
                    family_weight * item["base_weight"] / active_base,
                    4,
                )

        for name, family in families.items():
            family["effective_weight"] = round(
                family_effective_weights.get(name, 0.0),
                4,
            )

        score = sum(
            families[name]["score"] * weight
            for name, weight in family_effective_weights.items()
            if families[name]["score"] is not None
        )
        score = self._clamp(score)

        universal_family_coverage = []
        for name in self.UNIVERSAL_FAMILY_WEIGHTS:
            family = families[name]
            if family["total_components"] > 0:
                universal_family_coverage.append(family["coverage_pct"])

        coverage_pct = (
            sum(universal_family_coverage) / len(universal_family_coverage)
            if universal_family_coverage
            else 0.0
        )

        if score >= 80:
            regime = "STRONG_EXPANSION"
        elif score >= 65:
            regime = "EXPANSION"
        elif score >= 50:
            regime = "STABLE"
        elif score >= 35:
            regime = "SLOWDOWN"
        else:
            regime = "CONTRACTION"

        directional_families = [
            families[name]["score"]
            for name in ("growth", "profitability", "operating_drivers")
            if families[name]["available"] and families[name]["score"] is not None
        ]
        strong_votes = sum(value >= 65 for value in directional_families)
        weak_votes = sum(value < 40 for value in directional_families)

        if strong_votes >= 2 and strong_votes > weak_votes:
            trend = "ACCELERATING"
        elif weak_votes >= 2 and weak_votes > strong_votes:
            trend = "DECELERATING"
        else:
            trend = "STABLE"

        data_quality = data.data_quality.completeness_score
        if coverage_pct >= 75 and data_quality >= 75:
            confidence = "HIGH"
        elif coverage_pct >= 50 and data_quality >= 55:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        available_components = {
            key: item
            for key, item in components.items()
            if item["available"] and item["score"] is not None
        }
        excluded = [
            item["label"]
            for item in components.values()
            if not item["available"]
        ]

        evidence = []
        risks = []

        ranked_families = sorted(
            (
                (name, family)
                for name, family in families.items()
                if family["available"] and family["score"] is not None
            ),
            key=lambda pair: pair[1]["score"],
            reverse=True,
        )

        labels = {
            "growth": "Growth",
            "profitability": "Profitability",
            "cash_quality": "Cash & Quality",
            "operating_drivers": "Operating Drivers",
        }

        for name, family in ranked_families[:3]:
            if family["score"] >= 65:
                evidence.append(
                    f"{labels[name]} family is supportive ({family['score']:.1f}/100)."
                )

        for name, family in reversed(ranked_families):
            if family["score"] < 40:
                risks.append(
                    f"{labels[name]} family is weak ({family['score']:.1f}/100)."
                )
            if len(risks) >= 3:
                break

        return {
            "engine": "Adaptive Business Momentum Engine",
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "score": round(score, 1),
            "regime": regime,
            "trend": trend,
            "confidence": confidence,
            "coverage_pct": round(coverage_pct, 1),
            "active_components": len(available_components),
            "total_components": len(components),
            "adaptive_weighting": True,
            "factor_family_architecture": True,
            "operating_driver_cap_pct": self.OPERATING_DRIVER_CAP * 100.0,
            "family_effective_weights": {
                key: round(value, 4)
                for key, value in family_effective_weights.items()
            },
            "families": families,
            "excluded_components": excluded,
            "components": components,
            "evidence": evidence,
            "risks": risks,
        }
