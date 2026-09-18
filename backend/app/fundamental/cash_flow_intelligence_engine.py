from __future__ import annotations

from statistics import mean
from typing import Any


class FundamentalCashFlowIntelligenceEngine:
    """FA-METRICS-004 — Cash Flow Intelligence Engine.

    Evaluates cash generation, FCF conversion, CapEx intensity, burn/generation
    state and historical cash-flow direction. It consumes normalized QMI data
    and never fabricates missing periods or values.
    """

    ENGINE_ID = "FA-METRICS-004"
    VERSION = "0.1.0"

    def analyze(
        self,
        *,
        data: Any,
        statement_history: dict[str, Any],
        profitability_quality: dict[str, Any],
    ) -> dict[str, Any]:
        health = getattr(data, "financial_health", None)

        revenue = self._num(getattr(health, "total_revenue", None))
        net_income = self._num(getattr(health, "net_income", None))
        ocf = self._num(getattr(health, "operating_cash_flow", None))
        fcf = self._num(getattr(health, "free_cash_flow", None))

        annual = statement_history.get("annual") or {}
        quarterly = statement_history.get("quarterly") or {}

        annual_ocf = self._ordered(self._series(
            annual,
            ("operating_cash_flow", "total_cash_from_operating_activities"),
        ))
        annual_fcf = self._ordered(self._series(annual, ("free_cash_flow",)))
        annual_capex = self._ordered(self._series(
            annual,
            ("capital_expenditure", "capital_expenditures", "capital_expenditure_reported"),
        ))

        quarterly_ocf = self._ordered(self._series(
            quarterly,
            ("operating_cash_flow", "total_cash_from_operating_activities"),
        ))
        quarterly_fcf = self._ordered(self._series(quarterly, ("free_cash_flow",)))
        quarterly_capex = self._ordered(self._series(
            quarterly,
            ("capital_expenditure", "capital_expenditures", "capital_expenditure_reported"),
        ))

        ocf_margin = self._pct(ocf, revenue)
        fcf_margin = self._pct(fcf, revenue)
        ocf_to_income = self._pct(ocf, net_income)
        fcf_to_income = self._pct(fcf, net_income)

        latest_capex = self._latest_value(quarterly_capex)
        if latest_capex is None:
            latest_capex = self._latest_value(annual_capex)
        capex_intensity = self._pct(abs(latest_capex) if latest_capex is not None else None, revenue)

        annual_ocf_trend = self._trend(annual_ocf)
        annual_fcf_trend = self._trend(annual_fcf)
        quarterly_ocf_trend = self._trend(quarterly_ocf)
        quarterly_fcf_trend = self._trend(quarterly_fcf)

        generation_state = self._generation_state(ocf=ocf, fcf=fcf)
        burn_state = self._burn_state(ocf=ocf, fcf=fcf)

        conversion_quality = (
            (profitability_quality.get("cash_conversion") or {}).get("earnings_quality")
            or "UNAVAILABLE"
        )

        components = [
            self._positive_flow_score(ocf),
            self._positive_flow_score(fcf),
            self._conversion_score(ocf_to_income),
            self._conversion_score(fcf_to_income),
            self._margin_score(fcf_margin),
            self._trend_score(quarterly_fcf_trend if quarterly_fcf_trend != "UNAVAILABLE" else annual_fcf_trend),
        ]
        score = self._avg(components)

        available = {
            "operating_cash_flow": ocf,
            "free_cash_flow": fcf,
            "ocf_margin_pct": ocf_margin,
            "fcf_margin_pct": fcf_margin,
            "ocf_to_net_income_pct": ocf_to_income,
            "fcf_to_net_income_pct": fcf_to_income,
            "capex_intensity_pct": capex_intensity,
        }
        available_count = sum(v is not None for v in available.values())

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "cash_generation": {
                "operating_cash_flow": ocf,
                "free_cash_flow": fcf,
                "state": generation_state,
                "burn_state": burn_state,
            },
            "cash_margins": {
                "operating_cash_flow_margin_pct": ocf_margin,
                "free_cash_flow_margin_pct": fcf_margin,
            },
            "cash_conversion": {
                "operating_cash_flow_to_net_income_pct": ocf_to_income,
                "free_cash_flow_to_net_income_pct": fcf_to_income,
                "quality": conversion_quality,
            },
            "capex": {
                "latest_capex": latest_capex,
                "capex_intensity_pct": capex_intensity,
                "state": self._capex_state(capex_intensity),
            },
            "historical_trend": {
                "annual_operating_cash_flow": annual_ocf_trend,
                "annual_free_cash_flow": annual_fcf_trend,
                "quarterly_operating_cash_flow": quarterly_ocf_trend,
                "quarterly_free_cash_flow": quarterly_fcf_trend,
                "annual_ocf_periods": len(annual_ocf),
                "annual_fcf_periods": len(annual_fcf),
                "quarterly_ocf_periods": len(quarterly_ocf),
                "quarterly_fcf_periods": len(quarterly_fcf),
            },
            "cash_flow_score": score,
            "cash_flow_state": self._state(score),
            "coverage": {
                "metrics_available": available_count,
                "metrics_total": len(available),
                "coverage_pct": round(available_count / len(available) * 100.0, 1),
            },
            "contracts": {
                "normalized_history_only": True,
                "missing_values_not_zero_filled": True,
                "no_synthetic_periods": True,
                "cash_burn_explicit": True,
                "capex_intensity_explicit": True,
                "no_investment_decision": True,
                "no_execution_change": True,
            },
        }

    def _trend(self, values: list[tuple[str, float]]) -> str:
        if len(values) < 2:
            return "UNAVAILABLE"
        previous, current = values[-2][1], values[-1][1]
        if current > previous:
            return "IMPROVING"
        if current < previous:
            return "DETERIORATING"
        return "STABLE"

    @staticmethod
    def _generation_state(*, ocf: float | None, fcf: float | None) -> str:
        if ocf is None and fcf is None:
            return "UNAVAILABLE"
        if ocf is not None and ocf > 0 and fcf is not None and fcf > 0:
            return "STRONG_GENERATION"
        if ocf is not None and ocf > 0:
            return "OPERATING_GENERATION"
        if (ocf is not None and ocf < 0) or (fcf is not None and fcf < 0):
            return "CASH_BURN"
        return "NEUTRAL"

    @staticmethod
    def _burn_state(*, ocf: float | None, fcf: float | None) -> str:
        if ocf is None and fcf is None:
            return "UNAVAILABLE"
        if ocf is not None and ocf < 0 and fcf is not None and fcf < 0:
            return "HIGH"
        if (ocf is not None and ocf < 0) or (fcf is not None and fcf < 0):
            return "PRESENT"
        return "NONE"

    @staticmethod
    def _capex_state(value: float | None) -> str:
        if value is None:
            return "UNAVAILABLE"
        if value >= 20:
            return "HIGH_INTENSITY"
        if value >= 10:
            return "MODERATE_INTENSITY"
        return "LOW_INTENSITY"

    @staticmethod
    def _positive_flow_score(value: float | None) -> float | None:
        if value is None:
            return None
        return 85.0 if value > 0 else 50.0 if value == 0 else 20.0

    @staticmethod
    def _conversion_score(value: float | None) -> float | None:
        if value is None:
            return None
        if value >= 100:
            return 90.0
        if value >= 70:
            return 70.0
        if value >= 40:
            return 50.0
        return 25.0

    @staticmethod
    def _margin_score(value: float | None) -> float | None:
        if value is None:
            return None
        if value >= 15:
            return 90.0
        if value >= 5:
            return 70.0
        if value >= 0:
            return 55.0
        return 20.0

    @staticmethod
    def _trend_score(value: str) -> float | None:
        return {
            "IMPROVING": 80.0,
            "STABLE": 60.0,
            "DETERIORATING": 30.0,
        }.get(value)

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
    def _pct(numerator: float | None, denominator: float | None) -> float | None:
        if numerator is None or denominator in (None, 0):
            return None
        return round(numerator / denominator * 100.0, 2)

    @staticmethod
    def _avg(values: list[float | None]) -> float | None:
        usable = [v for v in values if v is not None]
        return round(mean(usable), 1) if usable else None

    @staticmethod
    def _latest_value(values: list[tuple[str, float]]) -> float | None:
        return values[-1][1] if values else None

    def _ordered(self, series: dict[str, Any]) -> list[tuple[str, float]]:
        result = []
        for period, value in (series or {}).items():
            number = self._num(value)
            if number is not None:
                result.append((str(period), number))
        return sorted(result, key=lambda item: item[0])

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
            return None if number != number else number
        except (TypeError, ValueError):
            return None
