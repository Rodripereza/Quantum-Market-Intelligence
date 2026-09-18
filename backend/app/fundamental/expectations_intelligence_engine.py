from __future__ import annotations

from statistics import mean
from typing import Any


class FundamentalExpectationsIntelligenceEngine:
    """FA-METRICS-006 — Expectations Intelligence.

    Uses only forward/expectation fields already normalized by the existing
    FundamentalCollector. No extra provider request is made here.
    """

    ENGINE_ID = "FA-METRICS-006"
    VERSION = "0.1.0"

    def analyze(
        self,
        *,
        data: Any,
        growth_trend: dict[str, Any],
        profitability_quality: dict[str, Any],
        cash_flow_intelligence: dict[str, Any],
        valuation_intelligence: dict[str, Any],
    ) -> dict[str, Any]:
        valuation = getattr(data, "valuation", None)
        growth = getattr(data, "growth", None)

        trailing_pe = self._positive(getattr(valuation, "trailing_pe", None))
        forward_pe = self._positive(getattr(valuation, "forward_pe", None))
        revenue_growth = self._pct(getattr(growth, "revenue_growth", None))
        earnings_growth = self._pct(getattr(growth, "earnings_growth", None))
        earnings_quarterly_growth = self._pct(
            getattr(growth, "earnings_quarterly_growth", None)
        )

        pe_change_pct = None
        if trailing_pe is not None and forward_pe is not None:
            pe_change_pct = round((forward_pe / trailing_pe - 1.0) * 100.0, 1)

        signals: list[float] = []
        evidence: list[str] = []

        for label, value in (
            ("revenue_growth", revenue_growth),
            ("earnings_growth", earnings_growth),
            ("earnings_quarterly_growth", earnings_quarterly_growth),
        ):
            score = self._growth_score(value)
            if score is not None:
                signals.append(score)
                evidence.append(f"{label}:{self._growth_state(value)}")

        pe_score = self._pe_expectation_score(trailing_pe, forward_pe)
        if pe_score is not None:
            signals.append(pe_score)

            if forward_pe is not None and trailing_pe is not None:
                evidence.append(
                    "forward_pe_below_trailing"
                    if forward_pe < trailing_pe
                    else "forward_pe_at_or_above_trailing"
                )
            elif forward_pe is not None:
                evidence.append("forward_pe_available_trailing_unavailable")

        market_expectation_score = round(mean(signals), 1) if signals else None

        quality_score = self._num(profitability_quality.get("quality_score"))
        cash_score = self._num(cash_flow_intelligence.get("cash_flow_score"))
        valuation_score = self._num(valuation_intelligence.get("valuation_score"))
        realized_growth = self._num(
            (growth_trend.get("summary") or {}).get("average_latest_growth_pct")
        )

        support_parts: list[float] = []
        if quality_score is not None:
            support_parts.append(self._bounded(quality_score))
        if cash_score is not None:
            support_parts.append(self._bounded(cash_score))
        if valuation_score is not None:
            support_parts.append(self._bounded(valuation_score))
        if realized_growth is not None:
            support_parts.append(self._bounded(50.0 + realized_growth * 1.5))

        fundamental_support_score = (
            round(mean(support_parts), 1) if support_parts else None
        )

        if market_expectation_score is not None and fundamental_support_score is not None:
            score = round(
                market_expectation_score * 0.65
                + fundamental_support_score * 0.35,
                1,
            )
        else:
            score = (
                market_expectation_score
                if market_expectation_score is not None
                else fundamental_support_score
            )

        available = sum(
            value is not None
            for value in (
                revenue_growth,
                earnings_growth,
                earnings_quarterly_growth,
                forward_pe,
            )
        )
        total = 4

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "expectations": {
                "revenue_growth_pct": revenue_growth,
                "earnings_growth_pct": earnings_growth,
                "earnings_quarterly_growth_pct": earnings_quarterly_growth,
                "trailing_pe": trailing_pe,
                "forward_pe": forward_pe,
                "forward_vs_trailing_pe_change_pct": pe_change_pct,
            },
            "trajectory": {
                "revenue": self._growth_state(revenue_growth),
                "earnings": self._growth_state(earnings_growth),
                "quarterly_earnings": self._growth_state(
                    earnings_quarterly_growth
                ),
                "pe_expectation": self._pe_state(trailing_pe, forward_pe),
            },
            "context": {
                "market_expectation_score": market_expectation_score,
                "fundamental_support_score": fundamental_support_score,
                "realized_growth_pct": realized_growth,
                "profitability_quality_score": quality_score,
                "cash_flow_score": cash_score,
                "valuation_score": valuation_score,
            },
            "expectations_score": score,
            "expectations_state": self._state(score),
            "evidence": evidence,
            "coverage": {
                "metrics_available": available,
                "metrics_total": total,
                "coverage_pct": round(available / total * 100.0, 1),
                "revisions_available": False,
            },
            "contracts": {
                "existing_normalized_provider_fields_only": True,
                "no_extra_provider_request": True,
                "missing_values_not_zero_filled": True,
                "no_synthetic_estimates": True,
                "revisions_not_inferred_when_unavailable": True,
                "fundamental_context_applied": True,
                "no_investment_decision": True,
                "no_execution_change": True,
            },
        }

    @staticmethod
    def _growth_score(value: float | None) -> float | None:
        if value is None:
            return None
        if value >= 25:
            return 90.0
        if value >= 10:
            return 75.0
        if value >= 0:
            return 60.0
        if value >= -10:
            return 40.0
        return 20.0

    @staticmethod
    def _growth_state(value: float | None) -> str:
        if value is None:
            return "UNAVAILABLE"
        if value >= 20:
            return "STRONG_GROWTH"
        if value >= 5:
            return "GROWTH"
        if value >= -5:
            return "STABLE"
        if value >= -20:
            return "CONTRACTION"
        return "STRONG_CONTRACTION"

    @staticmethod
    def _pe_expectation_score(
        trailing_pe: float | None,
        forward_pe: float | None,
    ) -> float | None:
        if forward_pe is None:
            return None
        if trailing_pe is None:
            return 50.0
        ratio = forward_pe / trailing_pe
        if ratio <= 0.70:
            return 85.0
        if ratio <= 0.90:
            return 70.0
        if ratio <= 1.10:
            return 55.0
        if ratio <= 1.30:
            return 40.0
        return 25.0

    @staticmethod
    def _pe_state(
        trailing_pe: float | None,
        forward_pe: float | None,
    ) -> str:
        if forward_pe is None:
            return "UNAVAILABLE"
        if trailing_pe is None:
            return "FORWARD_ONLY"
        if forward_pe < trailing_pe * 0.90:
            return "EARNINGS_EXPANSION_IMPLIED"
        if forward_pe > trailing_pe * 1.10:
            return "EARNINGS_CONTRACTION_IMPLIED"
        return "STABLE_EXPECTATION"

    @staticmethod
    def _state(score: float | None) -> str:
        if score is None:
            return "UNAVAILABLE"
        if score >= 80:
            return "STRONG"
        if score >= 65:
            return "GOOD"
        if score >= 50:
            return "MODERATE"
        return "WEAK"

    @staticmethod
    def _pct(value: Any) -> float | None:
        number = FundamentalExpectationsIntelligenceEngine._num(value)
        return None if number is None else round(number * 100.0, 2)

    @staticmethod
    def _positive(value: Any) -> float | None:
        number = FundamentalExpectationsIntelligenceEngine._num(value)
        return number if number is not None and number > 0 else None

    @staticmethod
    def _bounded(value: float) -> float:
        return max(0.0, min(100.0, value))

    @staticmethod
    def _num(value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            number = float(value)
            return None if number != number else number
        except (TypeError, ValueError):
            return None
