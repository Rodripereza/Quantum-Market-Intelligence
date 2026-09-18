from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.fundamental.schemas import FundamentalAnalysisResult


class FinancialDataFoundationService:
    """FA-DATA-001 — Financial Statements & Data Foundation.

    Audits normalized fundamental data before it reaches intelligence/scoring.
    Missing values remain missing; they are never silently converted to zero.
    """

    ENGINE_ID = "FA-DATA-001"
    VERSION = "0.1.0"

    REQUIRED_GROUPS = {
        "income_statement": (
            ("revenue", "financial_health.total_revenue"),
            ("ebitda", "financial_health.ebitda"),
            ("net_income", "financial_health.net_income"),
        ),
        "balance_sheet": (
            ("cash", "financial_health.total_cash"),
            ("debt", "financial_health.total_debt"),
            ("current_ratio", "financial_health.current_ratio"),
        ),
        "cash_flow": (
            ("operating_cash_flow", "financial_health.operating_cash_flow"),
            ("free_cash_flow", "financial_health.free_cash_flow"),
        ),
        "market_valuation": (
            ("market_cap", "valuation.market_cap"),
            ("enterprise_value", "valuation.enterprise_value"),
            ("price_to_sales", "valuation.price_to_sales"),
        ),
    }

    def audit(
        self,
        *,
        symbol: str,
        data: FundamentalAnalysisResult,
        provider: str = "Yahoo Finance",
    ) -> dict[str, Any]:
        groups: dict[str, Any] = {}
        available_total = 0
        metric_total = 0
        missing: list[str] = []

        for group, metrics in self.REQUIRED_GROUPS.items():
            rows = []
            available = 0
            for label, path in metrics:
                value = self._read(data, path)
                present = value is not None
                available += int(present)
                if not present:
                    missing.append(path)
                rows.append({
                    "metric": label,
                    "path": path,
                    "available": present,
                })
            total = len(metrics)
            metric_total += total
            available_total += available
            groups[group] = {
                "available": available > 0,
                "coverage_pct": round(available / total * 100.0, 1) if total else 0.0,
                "metrics_available": available,
                "metrics_total": total,
                "metrics": rows,
            }

        coverage = round(available_total / metric_total * 100.0, 1) if metric_total else 0.0
        if coverage >= 90:
            quality = "HIGH"
        elif coverage >= 70:
            quality = "GOOD"
        elif coverage >= 50:
            quality = "PARTIAL"
        else:
            quality = "LOW"

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "symbol": symbol.upper(),
            "provider": provider,
            "normalized_at": datetime.now(timezone.utc).isoformat(),
            "quality_state": quality,
            "coverage_pct": coverage,
            "metrics_available": available_total,
            "metrics_total": metric_total,
            "groups": groups,
            "missing_metrics": missing,
            "contracts": {
                "missing_values_preserved": True,
                "missing_values_are_not_zero": True,
                "provider_provenance_exposed": True,
                "quality_checked_before_scoring": True,
                "raw_provider_data_not_mutated": True,
            },
        }

    @staticmethod
    def _read(data: Any, path: str) -> Any:
        current = data
        for part in path.split("."):
            if current is None:
                return None
            if isinstance(current, dict):
                current = current.get(part)
            else:
                current = getattr(current, part, None)
        return current
