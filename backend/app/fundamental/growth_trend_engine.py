from __future__ import annotations

from statistics import mean
from typing import Any


class FundamentalGrowthTrendEngine:
    """FA-METRICS-001 — Fundamental Growth & Trend Engine.

    Converts normalized annual/quarterly statement history into comparable
    growth and trend metrics. It is deterministic, provider-independent and
    does not score or issue investment decisions.
    """

    ENGINE_ID = "FA-METRICS-001"
    VERSION = "0.1.0"

    METRIC_ALIASES = {
        "revenue": ("total_revenue", "revenue", "operating_revenue"),
        "gross_profit": ("gross_profit",),
        "operating_income": ("operating_income",),
        "net_income": ("net_income", "net_income_common_stockholders"),
        "operating_cash_flow": ("operating_cash_flow", "total_cash_from_operating_activities"),
        "free_cash_flow": ("free_cash_flow",),
    }

    def analyze(self, *, statement_history: dict[str, Any]) -> dict[str, Any]:
        annual = statement_history.get("annual") or {}
        quarterly = statement_history.get("quarterly") or {}

        metrics: dict[str, Any] = {}
        for canonical, aliases in self.METRIC_ALIASES.items():
            annual_series = self._find_series(annual, aliases)
            quarterly_series = self._find_series(quarterly, aliases)

            annual_values = self._ordered_numeric(annual_series)
            quarterly_values = self._ordered_numeric(quarterly_series)

            metrics[canonical] = {
                "annual": self._growth_block(annual_values, periods_per_year=1),
                "quarterly": self._growth_block(quarterly_values, periods_per_year=4),
            }

        margins = self._margin_analysis(annual=annual, quarterly=quarterly)
        fcf = metrics.get("free_cash_flow") or {}

        available_growth = [
            block.get("latest_growth_pct")
            for metric in metrics.values()
            for block in (metric.get("annual") or {}, metric.get("quarterly") or {})
            if block.get("latest_growth_pct") is not None
        ]

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "metrics": metrics,
            "margins": margins,
            "free_cash_flow_trend": {
                "annual": self._trend_label((fcf.get("annual") or {}).get("latest_growth_pct")),
                "quarterly": self._trend_label((fcf.get("quarterly") or {}).get("latest_growth_pct")),
            },
            "summary": {
                "growth_metrics_available": len(available_growth),
                "average_latest_growth_pct": round(mean(available_growth), 2) if available_growth else None,
                "revenue_trend": self._metric_trend(metrics.get("revenue")),
                "earnings_trend": self._metric_trend(metrics.get("net_income")),
                "cash_flow_trend": self._metric_trend(metrics.get("free_cash_flow")),
            },
            "contracts": {
                "uses_normalized_statement_history": True,
                "missing_values_not_zero_filled": True,
                "no_synthetic_periods": True,
                "annual_and_quarterly_kept_separate": True,
                "no_investment_decision": True,
                "no_scoring": True,
            },
        }

    def _growth_block(self, values: list[tuple[str, float]], *, periods_per_year: int) -> dict[str, Any]:
        if not values:
            return self._empty_block()

        latest_growth = self._pct_change(values[-2][1], values[-1][1]) if len(values) >= 2 else None
        previous_growth = self._pct_change(values[-3][1], values[-2][1]) if len(values) >= 3 else None

        acceleration = None
        if latest_growth is not None and previous_growth is not None:
            acceleration = round(latest_growth - previous_growth, 2)

        cagr = None
        if len(values) >= 2 and values[0][1] > 0 and values[-1][1] > 0:
            years = (len(values) - 1) / periods_per_year
            if years > 0:
                cagr = round(((values[-1][1] / values[0][1]) ** (1 / years) - 1) * 100, 2)

        return {
            "periods": len(values),
            "latest_period": values[-1][0],
            "latest_value": values[-1][1],
            "latest_growth_pct": latest_growth,
            "previous_growth_pct": previous_growth,
            "acceleration_pp": acceleration,
            "cagr_pct": cagr,
            "trend": self._trend_label(latest_growth),
            "acceleration_state": self._acceleration_label(acceleration),
        }

    def _margin_analysis(self, *, annual: dict[str, Any], quarterly: dict[str, Any]) -> dict[str, Any]:
        return {
            "annual": self._margins_for_frequency(annual),
            "quarterly": self._margins_for_frequency(quarterly),
        }

    def _margins_for_frequency(self, payload: dict[str, Any]) -> dict[str, Any]:
        revenue = dict(self._find_series(payload, self.METRIC_ALIASES["revenue"]))
        result = {}
        for name in ("gross_profit", "operating_income", "net_income"):
            numerator = dict(self._find_series(payload, self.METRIC_ALIASES[name]))
            common = sorted(set(revenue).intersection(numerator))
            series = []
            for period in common:
                rev = self._num(revenue.get(period))
                num = self._num(numerator.get(period))
                if rev in (None, 0) or num is None:
                    continue
                series.append((period, num / rev * 100))
            series.sort(key=lambda item: item[0])
            latest = series[-1][1] if series else None
            previous = series[-2][1] if len(series) >= 2 else None
            delta = round(latest - previous, 2) if latest is not None and previous is not None else None
            result[name.replace("_profit", "").replace("_income", "") + "_margin"] = {
                "latest_pct": round(latest, 2) if latest is not None else None,
                "previous_pct": round(previous, 2) if previous is not None else None,
                "change_pp": delta,
                "state": self._margin_label(delta),
            }
        return result

    @staticmethod
    def _find_series(payload: dict[str, Any], aliases: tuple[str, ...]) -> dict[str, Any]:
        for statement in payload.values():
            metrics = (statement or {}).get("metrics") or {}
            lowered = {str(k).lower(): v for k, v in metrics.items()}
            for alias in aliases:
                if alias.lower() in lowered:
                    return lowered[alias.lower()] or {}
        return {}

    def _ordered_numeric(self, series: dict[str, Any]) -> list[tuple[str, float]]:
        result = []
        for period, value in (series or {}).items():
            number = self._num(value)
            if number is not None:
                result.append((str(period), number))
        return sorted(result, key=lambda item: item[0])

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

    @staticmethod
    def _pct_change(previous: float, current: float) -> float | None:
        if previous == 0:
            return None
        return round((current / previous - 1) * 100, 2)

    @staticmethod
    def _trend_label(value: float | None) -> str:
        if value is None:
            return "UNAVAILABLE"
        if value > 5:
            return "EXPANDING"
        if value < -5:
            return "CONTRACTING"
        return "STABLE"

    @staticmethod
    def _acceleration_label(value: float | None) -> str:
        if value is None:
            return "UNAVAILABLE"
        if value > 2:
            return "ACCELERATING"
        if value < -2:
            return "DECELERATING"
        return "STABLE"

    @staticmethod
    def _margin_label(value: float | None) -> str:
        if value is None:
            return "UNAVAILABLE"
        if value > 0.5:
            return "EXPANDING"
        if value < -0.5:
            return "CONTRACTING"
        return "STABLE"

    def _metric_trend(self, metric: dict[str, Any] | None) -> str:
        metric = metric or {}
        quarterly = metric.get("quarterly") or {}
        annual = metric.get("annual") or {}
        return quarterly.get("trend") if quarterly.get("trend") != "UNAVAILABLE" else annual.get("trend", "UNAVAILABLE")

    @staticmethod
    def _empty_block() -> dict[str, Any]:
        return {
            "periods": 0,
            "latest_period": None,
            "latest_value": None,
            "latest_growth_pct": None,
            "previous_growth_pct": None,
            "acceleration_pp": None,
            "cagr_pct": None,
            "trend": "UNAVAILABLE",
            "acceleration_state": "UNAVAILABLE",
        }
