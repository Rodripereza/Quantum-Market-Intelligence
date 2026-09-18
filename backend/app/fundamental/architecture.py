from __future__ import annotations

from typing import Any

from app.fundamental.schemas import FundamentalAnalysisResult


class FundamentalArchitectureService:
    """FA-CORE-001 — Fundamental Intelligence Architecture.

    Defines the stable domain contract for QMI Fundamental Intelligence while
    preserving the existing DE-FA engines. This layer describes availability
    and ownership; it does not duplicate scoring logic.
    """

    ENGINE_ID = "FA-CORE-001"
    VERSION = "0.1.0"

    DOMAIN_ORDER = (
        "financial_performance",
        "growth",
        "financial_health",
        "cash_flow",
        "valuation",
        "expectations",
        "company_intelligence",
    )

    def build(self, *, data: FundamentalAnalysisResult, company_specific: dict[str, Any] | None = None) -> dict[str, Any]:
        company_specific = company_specific or {}

        domains = {
            "financial_performance": self._domain(
                "Financial Performance",
                [
                    data.financial_health.total_revenue,
                    data.financial_health.ebitda,
                    data.financial_health.net_income,
                    data.profitability.gross_margin,
                    data.profitability.operating_margin,
                    data.profitability.net_margin,
                ],
                "Normalized statements + profitability",
            ),
            "growth": self._domain(
                "Growth",
                [
                    data.growth.revenue_growth,
                    data.growth.earnings_growth,
                    data.trends.revenue_cagr_3y,
                    data.trends.net_income_yoy,
                ],
                "Growth metrics + statement trends",
            ),
            "financial_health": self._domain(
                "Financial Health",
                [
                    data.financial_health.total_cash,
                    data.financial_health.total_debt,
                    data.financial_health.current_ratio,
                    data.financial_health.quick_ratio,
                    data.trends.net_cash,
                ],
                "Balance sheet + liquidity",
            ),
            "cash_flow": self._domain(
                "Cash Flow",
                [
                    data.financial_health.operating_cash_flow,
                    data.financial_health.free_cash_flow,
                    data.trends.free_cash_flow_yoy,
                    data.trends.free_cash_flow_margin_ttm,
                ],
                "Cash-flow statements + derived trends",
            ),
            "valuation": self._domain(
                "Valuation",
                [
                    data.valuation.forward_pe,
                    data.valuation.price_to_sales,
                    data.valuation.price_to_book,
                    data.valuation.enterprise_to_revenue,
                    data.valuation.enterprise_to_ebitda,
                ],
                "Market valuation snapshot",
            ),
            "expectations": {
                "name": "Expectations",
                "available": False,
                "coverage_pct": 0.0,
                "source": "Reserved for analyst estimates / revisions / surprises",
                "status": "PLANNED",
            },
            "company_intelligence": {
                "name": "Company Intelligence",
                "available": bool(company_specific),
                "coverage_pct": 100.0 if company_specific else 0.0,
                "source": "Optional ticker-specific adapters",
                "status": "ACTIVE" if company_specific else "OPTIONAL",
            },
        }

        active = sum(bool(domains[key]["available"]) for key in self.DOMAIN_ORDER)
        universal_keys = self.DOMAIN_ORDER[:-1]
        universal_active = sum(bool(domains[key]["available"]) for key in universal_keys)

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "architecture": "QMI Fundamental Intelligence",
            "pipeline": [
                "RAW_PROVIDER_DATA",
                "NORMALIZED_FINANCIAL_DATA",
                "DATA_QUALITY_AND_PROVENANCE",
                "STATEMENT_PROVIDER_ADAPTER",
                "FINANCIAL_STATEMENT_HISTORY",
                "DERIVED_METRICS",
                "GROWTH_AND_TREND_INTELLIGENCE",
                "PROFITABILITY_AND_QUALITY_INTELLIGENCE",
                "FINANCIAL_HEALTH_INTELLIGENCE",
                "CASH_FLOW_INTELLIGENCE",
                "VALUATION_INTELLIGENCE",
                "EXPECTATIONS_INTELLIGENCE",
                "COMPANY_INTELLIGENCE",
                "DOMAIN_INTELLIGENCE",
                "FUNDAMENTAL_DECISION",
            ],
            "domains": domains,
            "active_domains": active,
            "total_domains": len(self.DOMAIN_ORDER),
            "universal_domain_coverage_pct": round(universal_active / len(universal_keys) * 100.0, 1),
            "contracts": {
                "raw_data_and_scoring_separated": True,
                "missing_metrics_are_not_zero": True,
                "company_intelligence_optional": True,
                "company_specific_weighting_capped": True,
                "decision_layer_consumes_normalized_intelligence": True,
            },
            "legacy_engines_preserved": [
                "DE-FA-001",
                "DE-FA-001.1",
                "DE-FA-002.1",
                "DE-FA-003.0",
                "DE-FA-003.1",
                "DE-FA-004.0",
                "DE-FA-BM-001.1",
            ],
        }

    @staticmethod
    def _domain(name: str, values: list[Any], source: str) -> dict[str, Any]:
        total = len(values)
        available = sum(value is not None for value in values)
        coverage = (available / total * 100.0) if total else 0.0
        return {
            "name": name,
            "available": available > 0,
            "coverage_pct": round(coverage, 1),
            "metrics_available": available,
            "metrics_total": total,
            "source": source,
            "status": "ACTIVE" if available > 0 else "UNAVAILABLE",
        }
