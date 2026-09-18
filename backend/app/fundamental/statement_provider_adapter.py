from __future__ import annotations

from typing import Any

from app.fundamental.schemas import FundamentalAnalysisResult, FundamentalStatements


class StatementProviderAdapter:
    """FA-DATA-003 — Statement Provider Adapter.

    Bridges the existing normalized DE-FA statement foundation into the new
    FA-DATA history contract. It does not perform network acquisition itself:
    FundamentalCollector remains the provider boundary.
    """

    ENGINE_ID = "FA-DATA-003"
    VERSION = "0.1.0"

    def adapt(self, *, data: FundamentalAnalysisResult) -> dict[str, Any]:
        statements = data.statements or FundamentalStatements()

        annual = {
            "income_statement": self._period_models(statements.annual_income),
            "balance_sheet": self._period_models(statements.annual_balance_sheet),
            "cash_flow": self._period_models(statements.annual_cash_flow),
        }
        quarterly = {
            "income_statement": self._period_models(statements.quarterly_income),
            "balance_sheet": self._period_models(statements.quarterly_balance_sheet),
            "cash_flow": self._period_models(statements.quarterly_cash_flow),
        }

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "provider": data.data_source or "yfinance",
            "symbol": data.symbol,
            "annual": annual,
            "quarterly": quarterly,
            "ttm": {
                "income_statement": self._model_dump(statements.ttm_income),
                "cash_flow": self._model_dump(statements.ttm_cash_flow),
            },
            "latest_balance_sheet": self._model_dump(statements.latest_balance_sheet),
            "source_quality": self._model_dump(data.data_quality),
            "contracts": {
                "collector_remains_provider_boundary": True,
                "normalized_qmi_statements_reused": True,
                "no_second_provider_request": True,
                "no_synthetic_history": True,
                "missing_values_preserved": True,
            },
        }

    @classmethod
    def _period_models(cls, periods: list[Any]) -> dict[str, dict[str, Any]]:
        """Convert QMI period models to metric -> period -> value."""
        metrics: dict[str, dict[str, Any]] = {}
        for period_model in periods or []:
            row = cls._model_dump(period_model)
            if not row:
                continue
            period = str(row.get("period") or "")
            if not period:
                continue
            for key, value in row.items():
                if key in {"period", "period_type", "currency"}:
                    continue
                metrics.setdefault(key, {})[period] = value
        return metrics

    @staticmethod
    def _model_dump(value: Any) -> dict[str, Any] | None:
        if value is None:
            return None
        if hasattr(value, "model_dump"):
            return value.model_dump(mode="python")
        if isinstance(value, dict):
            return dict(value)
        return None
