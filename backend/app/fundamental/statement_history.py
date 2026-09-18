from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class FinancialStatementHistoryService:
    """FA-DATA-002 — Financial Statement History.

    Normalizes provider statement series into a stable chronological contract.
    This service does not score companies and never invents missing periods.
    """

    ENGINE_ID = "FA-DATA-002"
    VERSION = "0.2.0"

    STATEMENT_ALIASES = {
        "income_statement": ("income_statement", "income_stmt", "financials"),
        "balance_sheet": ("balance_sheet", "balanceSheet"),
        "cash_flow": ("cash_flow", "cashflow", "cash_flow_statement"),
    }

    def normalize(
        self,
        *,
        symbol: str,
        annual: dict[str, Any] | None = None,
        quarterly: dict[str, Any] | None = None,
        provider: str = "Yahoo Finance",
    ) -> dict[str, Any]:
        annual = annual or {}
        quarterly = quarterly or {}

        annual_payload = self._normalize_frequency(annual)
        quarterly_payload = self._normalize_frequency(quarterly)

        annual_periods = self._period_union(annual_payload)
        quarterly_periods = self._period_union(quarterly_payload)

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "symbol": symbol.upper(),
            "provider": provider,
            "normalized_at": datetime.now(timezone.utc).isoformat(),
            "annual": annual_payload,
            "quarterly": quarterly_payload,
            "coverage": {
                "annual_periods": len(annual_periods),
                "quarterly_periods": len(quarterly_periods),
                "annual_period_labels": annual_periods,
                "quarterly_period_labels": quarterly_periods,
                "has_annual_history": len(annual_periods) >= 2,
                "has_quarterly_history": len(quarterly_periods) >= 2,
            },
            "contracts": {
                "chronological_periods": True,
                "missing_periods_not_synthesized": True,
                "missing_values_preserved": True,
                "annual_and_quarterly_separated": True,
                "provider_provenance_exposed": True,
                "scoring_not_performed_here": True,
            },
        }

    def _normalize_frequency(self, payload: dict[str, Any]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for canonical, aliases in self.STATEMENT_ALIASES.items():
            raw = None
            for alias in aliases:
                if alias in payload and payload[alias] is not None:
                    raw = payload[alias]
                    break
            result[canonical] = self._normalize_statement(raw)
        return result

    def _normalize_statement(self, raw: Any) -> dict[str, Any]:
        if raw is None:
            return {"periods": [], "metrics": {}, "available": False}

        # Supports dict-oriented provider adapters without forcing a provider
        # implementation into this domain layer.
        if isinstance(raw, dict):
            metrics: dict[str, dict[str, Any]] = {}
            periods: set[str] = set()

            for metric, series in raw.items():
                metric_name = str(metric)
                if isinstance(series, dict):
                    normalized_series = {}
                    for period, value in series.items():
                        label = self._period_label(period)
                        periods.add(label)
                        normalized_series[label] = self._scalar(value)
                    metrics[metric_name] = normalized_series
                else:
                    metrics[metric_name] = {"current": self._scalar(series)}
                    periods.add("current")

            ordered = sorted(periods, key=self._period_sort_key)
            return {
                "periods": ordered,
                "metrics": metrics,
                "available": bool(metrics),
            }

        return {
            "periods": [],
            "metrics": {},
            "available": False,
            "unsupported_source_type": type(raw).__name__,
        }

    @staticmethod
    def _scalar(value: Any) -> Any:
        if value is None:
            return None
        if hasattr(value, "item"):
            try:
                return value.item()
            except Exception:
                pass
        if isinstance(value, (str, int, float, bool)):
            return value
        try:
            if value != value:
                return None
        except Exception:
            pass
        return str(value)

    @staticmethod
    def _period_label(value: Any) -> str:
        if hasattr(value, "isoformat"):
            try:
                return value.isoformat()
            except Exception:
                pass
        return str(value)

    @staticmethod
    def _period_sort_key(label: str) -> tuple[int, str]:
        if label == "current":
            return (1, label)
        return (0, label)

    @staticmethod
    def _period_union(payload: dict[str, Any]) -> list[str]:
        periods: set[str] = set()
        for statement in payload.values():
            periods.update(statement.get("periods") or [])
        return sorted(periods, key=FinancialStatementHistoryService._period_sort_key)
