from __future__ import annotations

from statistics import mean, pstdev
from typing import Any


class FundamentalProfitabilityQualityEngine:
    """FA-METRICS-002 — Profitability & Quality Engine.

    Evaluates profitability, cash conversion and operating quality from the
    normalized QMI fundamental dataset. Missing inputs remain unavailable.
    This engine does not issue investment decisions.
    """

    ENGINE_ID = "FA-METRICS-002"
    VERSION = "0.1.0"

    def analyze(
        self,
        *,
        data: Any,
        statement_history: dict[str, Any],
        growth_trend: dict[str, Any],
    ) -> dict[str, Any]:
        profitability = getattr(data, "profitability", None)
        health = getattr(data, "financial_health", None)

        gross_margin = self._num(getattr(profitability, "gross_margin", None))
        operating_margin = self._num(getattr(profitability, "operating_margin", None))
        net_margin = self._num(getattr(profitability, "net_margin", None))
        roe = self._num(getattr(profitability, "return_on_equity", None))
        roa = self._num(getattr(profitability, "return_on_assets", None))
        roic = self._first_num(
            getattr(profitability, "return_on_invested_capital", None),
            getattr(profitability, "roic", None),
        )

        net_income = self._num(getattr(health, "net_income", None))
        operating_cash_flow = self._num(getattr(health, "operating_cash_flow", None))
        free_cash_flow = self._num(getattr(health, "free_cash_flow", None))

        ocf_conversion = self._ratio_pct(operating_cash_flow, net_income)
        fcf_conversion = self._ratio_pct(free_cash_flow, net_income)

        margin_stability = self._margin_stability(statement_history)
        margin_trend = self._margin_trend(growth_trend)

        earnings_quality = self._earnings_quality(
            net_income=net_income,
            operating_cash_flow=operating_cash_flow,
            free_cash_flow=free_cash_flow,
        )

        efficiency_values = [v for v in (roe, roa, roic) if v is not None]
        efficiency_state = self._efficiency_state(efficiency_values)

        available = {
            "gross_margin": gross_margin,
            "operating_margin": operating_margin,
            "net_margin": net_margin,
            "roe": roe,
            "roa": roa,
            "roic": roic,
            "ocf_conversion_pct": ocf_conversion,
            "fcf_conversion_pct": fcf_conversion,
        }
        available_count = sum(value is not None for value in available.values())

        quality_components = [
            self._margin_component(operating_margin),
            self._return_component(roe),
            self._return_component(roa),
            self._return_component(roic),
            self._conversion_component(ocf_conversion),
            self._conversion_component(fcf_conversion),
            margin_stability.get("score"),
        ]
        usable_components = [v for v in quality_components if v is not None]
        quality_score = round(mean(usable_components), 1) if usable_components else None

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "profitability": {
                "gross_margin_pct": gross_margin,
                "operating_margin_pct": operating_margin,
                "net_margin_pct": net_margin,
                "roe_pct": roe,
                "roa_pct": roa,
                "roic_pct": roic,
            },
            "cash_conversion": {
                "operating_cash_flow_to_net_income_pct": ocf_conversion,
                "free_cash_flow_to_net_income_pct": fcf_conversion,
                "earnings_quality": earnings_quality,
            },
            "margin_quality": {
                "stability": margin_stability,
                "trend": margin_trend,
            },
            "capital_efficiency": {
                "state": efficiency_state,
                "metrics_available": len(efficiency_values),
            },
            "quality_score": quality_score,
            "quality_state": self._quality_state(quality_score),
            "coverage": {
                "metrics_available": available_count,
                "metrics_total": len(available),
                "coverage_pct": round(available_count / len(available) * 100.0, 1),
            },
            "contracts": {
                "missing_values_not_zero_filled": True,
                "quality_score_uses_available_components_only": True,
                "historical_margin_stability_used_when_available": True,
                "cash_conversion_explicit": True,
                "no_investment_decision": True,
                "no_execution_change": True,
            },
        }

    def _margin_stability(self, history: dict[str, Any]) -> dict[str, Any]:
        annual = history.get("annual") or {}
        revenue = self._series(annual, ("total_revenue", "revenue", "operating_revenue"))
        operating = self._series(annual, ("operating_income",))
        common = sorted(set(revenue).intersection(operating))

        margins = []
        for period in common:
            rev = self._num(revenue.get(period))
            op = self._num(operating.get(period))
            if rev in (None, 0) or op is None:
                continue
            margins.append(op / rev * 100.0)

        if len(margins) < 2:
            return {"state": "UNAVAILABLE", "score": None, "observations": len(margins), "volatility_pp": None}

        volatility = pstdev(margins)
        score = max(0.0, min(100.0, 100.0 - volatility * 8.0))
        state = "HIGH" if score >= 75 else "MEDIUM" if score >= 50 else "LOW"
        return {
            "state": state,
            "score": round(score, 1),
            "observations": len(margins),
            "volatility_pp": round(volatility, 2),
        }

    @staticmethod
    def _margin_trend(growth_trend: dict[str, Any]) -> dict[str, Any]:
        margins = (growth_trend.get("margins") or {}).get("annual") or {}
        return {
            "gross_margin": (margins.get("gross_margin") or {}).get("state", "UNAVAILABLE"),
            "operating_margin": (margins.get("operating_margin") or {}).get("state", "UNAVAILABLE"),
            "net_margin": (margins.get("net_margin") or {}).get("state", "UNAVAILABLE"),
        }

    @staticmethod
    def _earnings_quality(*, net_income: float | None, operating_cash_flow: float | None, free_cash_flow: float | None) -> str:
        if net_income is None or operating_cash_flow is None:
            return "UNAVAILABLE"
        if net_income <= 0:
            if operating_cash_flow > 0 and (free_cash_flow is None or free_cash_flow >= 0):
                return "RECOVERING"
            return "WEAK"
        ratio = operating_cash_flow / net_income
        if ratio >= 1.0 and (free_cash_flow is None or free_cash_flow > 0):
            return "HIGH"
        if ratio >= 0.7:
            return "GOOD"
        return "WEAK"

    @staticmethod
    def _ratio_pct(numerator: float | None, denominator: float | None) -> float | None:
        if numerator is None or denominator in (None, 0):
            return None
        return round(numerator / denominator * 100.0, 2)

    @staticmethod
    def _margin_component(value: float | None) -> float | None:
        if value is None:
            return None
        return round(max(0.0, min(100.0, 50.0 + value * 2.0)), 1)

    @staticmethod
    def _return_component(value: float | None) -> float | None:
        if value is None:
            return None
        return round(max(0.0, min(100.0, 50.0 + value * 2.0)), 1)

    @staticmethod
    def _conversion_component(value: float | None) -> float | None:
        if value is None:
            return None
        return round(max(0.0, min(100.0, value)), 1)

    @staticmethod
    def _quality_state(score: float | None) -> str:
        if score is None:
            return "UNAVAILABLE"
        if score >= 80:
            return "HIGH"
        if score >= 65:
            return "GOOD"
        if score >= 50:
            return "MODERATE"
        return "WEAK"

    @staticmethod
    def _efficiency_state(values: list[float]) -> str:
        if not values:
            return "UNAVAILABLE"
        avg = mean(values)
        if avg >= 20:
            return "HIGH"
        if avg >= 10:
            return "GOOD"
        if avg >= 0:
            return "MODERATE"
        return "WEAK"

    @staticmethod
    def _series(payload: dict[str, Any], aliases: tuple[str, ...]) -> dict[str, Any]:
        for statement in payload.values():
            metrics = (statement or {}).get("metrics") or {}
            lowered = {str(k).lower(): v for k, v in metrics.items()}
            for alias in aliases:
                if alias.lower() in lowered:
                    return lowered[alias.lower()] or {}
        return {}

    @staticmethod
    def _num(value: Any) -> float | None:
        if value is None or isinstance(value, bool):
            return None
        try:
            number = float(value)
            if number != number:
                return None
            return number
        except (TypeError, ValueError):
            return None

    def _first_num(self, *values: Any) -> float | None:
        for value in values:
            number = self._num(value)
            if number is not None:
                return number
        return None
