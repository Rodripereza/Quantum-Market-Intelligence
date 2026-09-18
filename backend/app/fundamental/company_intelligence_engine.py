from __future__ import annotations
from typing import Any

class FundamentalCompanyIntelligenceEngine:
    """FA-COMPANY-001 — optional company-specific intelligence foundation."""
    ENGINE_ID = "FA-COMPANY-001"
    VERSION = "0.1.0"

    def analyze(self, *, data: Any, company_metrics: dict[str, Any] | None = None) -> dict[str, Any]:
        profile = getattr(data, "company", None)
        symbol = self._text(getattr(data, "symbol", None) or getattr(profile, "symbol", None))
        sector = self._text(getattr(profile, "sector", None))
        industry = self._text(getattr(profile, "industry", None))
        currency = self._text(getattr(profile, "financial_currency", None) or getattr(profile, "currency", None))

        supplied = company_metrics or {}
        metrics = {str(k): v for k, v in supplied.items() if v is not None}

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "company": {
                "symbol": symbol,
                "sector": sector,
                "industry": industry,
                "currency": currency,
            },
            "company_specific": {
                "state": "ACTIVE" if metrics else "FOUNDATION_READY",
                "metrics": metrics,
                "metrics_available": len(metrics),
            },
            "coverage": {
                "company_profile_available": any(v is not None for v in (symbol, sector, industry, currency)),
                "company_specific_metrics_available": len(metrics),
            },
            "contracts": {
                "company_intelligence_optional": True,
                "universal_metrics_untouched": True,
                "company_specific_metrics_explicit_only": True,
                "missing_company_metrics_not_zero_filled": True,
                "no_synthetic_company_kpis": True,
                "no_investment_decision": True,
                "no_execution_change": True,
            },
        }

    @staticmethod
    def _text(value: Any) -> str | None:
        if value is None:
            return None
        value = str(value).strip()
        return value or None
