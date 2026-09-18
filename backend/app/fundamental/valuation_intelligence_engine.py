from __future__ import annotations

from statistics import mean
from typing import Any


class FundamentalValuationIntelligenceEngine:
    """FA-METRICS-005 — Valuation Intelligence.

    Interprets available valuation multiples in the context of growth,
    profitability and cash generation. It is a domain diagnostic, not an
    investment recommendation or execution signal.
    """

    ENGINE_ID = "FA-METRICS-005"
    VERSION = "0.1.0"

    def analyze(
        self,
        *,
        data: Any,
        growth_trend: dict[str, Any],
        profitability_quality: dict[str, Any],
        cash_flow_intelligence: dict[str, Any],
    ) -> dict[str, Any]:
        valuation = getattr(data, "valuation", None)

        metrics = {
            "price_to_sales": self._positive(getattr(valuation, "price_to_sales", None)),
            "enterprise_to_revenue": self._positive(getattr(valuation, "enterprise_to_revenue", None)),
            "trailing_pe": self._positive(getattr(valuation, "trailing_pe", None)),
            "forward_pe": self._positive(getattr(valuation, "forward_pe", None)),
            "price_to_book": self._positive(getattr(valuation, "price_to_book", None)),
            "enterprise_to_ebitda": self._positive(getattr(valuation, "enterprise_to_ebitda", None)),
        }

        raw = {
            "market_cap": self._num(getattr(valuation, "market_cap", None)),
            "enterprise_value": self._num(getattr(valuation, "enterprise_value", None)),
            **metrics,
        }

        revenue_growth = self._num((growth_trend.get("summary") or {}).get("average_latest_growth_pct"))
        quality_score = self._num(profitability_quality.get("quality_score"))
        cash_flow_score = self._num(cash_flow_intelligence.get("cash_flow_score"))

        multiple_scores = {
            name: self._multiple_score(name, value)
            for name, value in metrics.items()
            if value is not None
        }

        base_score = round(mean(multiple_scores.values()), 1) if multiple_scores else None
        context_score = self._context_score(
            growth=revenue_growth,
            quality=quality_score,
            cash_flow=cash_flow_score,
        )

        # Multiples remain the dominant component; business context prevents
        # a low multiple from being interpreted automatically as attractive.
        if base_score is not None and context_score is not None:
            score = round(base_score * 0.70 + context_score * 0.30, 1)
        else:
            score = base_score if base_score is not None else context_score

        available = len(multiple_scores)
        total = len(metrics)

        unavailable = [name for name, value in metrics.items() if value is None]

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "metrics": raw,
            "multiple_diagnostics": {
                name: {
                    "value": metrics[name],
                    "score": multiple_scores.get(name),
                    "state": self._multiple_state(name, metrics[name]),
                }
                for name in metrics
            },
            "context": {
                "growth_pct": revenue_growth,
                "profitability_quality_score": quality_score,
                "cash_flow_score": cash_flow_score,
                "context_score": context_score,
            },
            "valuation_score": score,
            "valuation_state": self._state(score),
            "coverage": {
                "multiples_available": available,
                "multiples_total": total,
                "coverage_pct": round(available / total * 100.0, 1),
                "unavailable_multiples": unavailable,
            },
            "contracts": {
                "positive_meaningful_multiples_only": True,
                "loss_multiples_not_treated_as_cheap": True,
                "low_multiple_not_automatically_attractive": True,
                "business_context_applied": True,
                "missing_values_not_zero_filled": True,
                "no_investment_decision": True,
                "no_execution_change": True,
            },
        }

    @staticmethod
    def _multiple_score(name: str, value: float | None) -> float | None:
        if value is None:
            return None
        # Broad deterministic bands. These are internal valuation diagnostics,
        # not sector-relative fair-value estimates.
        bands = {
            "price_to_sales": ((1, 90), (3, 75), (6, 55), (10, 40)),
            "enterprise_to_revenue": ((1, 90), (3, 75), (6, 55), (10, 40)),
            "trailing_pe": ((15, 90), (25, 75), (40, 55), (60, 40)),
            "forward_pe": ((15, 90), (25, 75), (40, 55), (60, 40)),
            "price_to_book": ((1.5, 90), (3, 75), (6, 55), (10, 40)),
            "enterprise_to_ebitda": ((8, 90), (14, 75), (22, 55), (35, 40)),
        }
        for ceiling, score in bands[name]:
            if value <= ceiling:
                return float(score)
        return 25.0

    @staticmethod
    def _multiple_state(name: str, value: float | None) -> str:
        if value is None:
            return "UNAVAILABLE"
        score = FundamentalValuationIntelligenceEngine._multiple_score(name, value)
        if score >= 80:
            return "LOW_MULTIPLE"
        if score >= 65:
            return "MODERATE_MULTIPLE"
        if score >= 45:
            return "ELEVATED_MULTIPLE"
        return "HIGH_MULTIPLE"

    @staticmethod
    def _context_score(*, growth: float | None, quality: float | None, cash_flow: float | None) -> float | None:
        parts: list[float] = []
        if growth is not None:
            parts.append(max(0.0, min(100.0, 50.0 + growth * 1.5)))
        if quality is not None:
            parts.append(max(0.0, min(100.0, quality)))
        if cash_flow is not None:
            parts.append(max(0.0, min(100.0, cash_flow)))
        return round(mean(parts), 1) if parts else None

    @staticmethod
    def _state(score: float | None) -> str:
        if score is None:
            return "UNAVAILABLE"
        if score >= 80:
            return "LOW_RELATIVE_MULTIPLES"
        if score >= 65:
            return "MODERATE_RELATIVE_MULTIPLES"
        if score >= 50:
            return "ELEVATED_RELATIVE_MULTIPLES"
        return "HIGH_RELATIVE_MULTIPLES"

    @staticmethod
    def _positive(value: Any) -> float | None:
        number = FundamentalValuationIntelligenceEngine._num(value)
        return number if number is not None and number > 0 else None

    @staticmethod
    def _num(value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            number = float(value)
            return None if number != number else number
        except (TypeError, ValueError):
            return None
