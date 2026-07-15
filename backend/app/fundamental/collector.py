"""
Fundamental Data Collector

Retrieves company fundamental data from yfinance
and converts it into QMI normalized schemas.
"""

from typing import Any, Optional

import yfinance as yf

from app.fundamental.schemas import (
    CompanyProfile,
    FinancialHealthMetrics,
    FundamentalAnalysisResult,
    GrowthMetrics,
    ProfitabilityMetrics,
    ValuationMetrics,
)


class FundamentalCollector:
    """Retrieve and normalize fundamental company data."""

    def __init__(self) -> None:
        self.provider = "yfinance"

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        """
        Convert provider values to float safely.

        Returns None when the value is missing or invalid.
        """

        if value is None:
            return None

        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    def get_fundamentals(self, symbol: str) -> FundamentalAnalysisResult:
        """
        Retrieve normalized fundamentals for a market symbol.
        """

        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError("Symbol cannot be empty.")

        ticker = yf.Ticker(normalized_symbol)
        info = ticker.info

        profile = CompanyProfile(
            symbol=normalized_symbol,
            company_name=info.get("longName") or info.get("shortName"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            country=info.get("country"),
            currency=info.get("currency"),
            exchange=info.get("exchange"),
        )

        valuation = ValuationMetrics(
            market_cap=self._to_float(info.get("marketCap")),
            enterprise_value=self._to_float(info.get("enterpriseValue")),
            trailing_pe=self._to_float(info.get("trailingPE")),
            forward_pe=self._to_float(info.get("forwardPE")),
            price_to_book=self._to_float(info.get("priceToBook")),
            price_to_sales=self._to_float(
                info.get("priceToSalesTrailing12Months")
            ),
            enterprise_to_revenue=self._to_float(
                info.get("enterpriseToRevenue")
            ),
            enterprise_to_ebitda=self._to_float(
                info.get("enterpriseToEbitda")
            ),
        )

        profitability = ProfitabilityMetrics(
            gross_margin=self._to_float(info.get("grossMargins")),
            operating_margin=self._to_float(info.get("operatingMargins")),
            net_margin=self._to_float(info.get("profitMargins")),
            return_on_assets=self._to_float(info.get("returnOnAssets")),
            return_on_equity=self._to_float(info.get("returnOnEquity")),
        )

        growth = GrowthMetrics(
            revenue_growth=self._to_float(info.get("revenueGrowth")),
            earnings_growth=self._to_float(info.get("earningsGrowth")),
            earnings_quarterly_growth=self._to_float(
                info.get("earningsQuarterlyGrowth")
            ),
        )

        financial_health = FinancialHealthMetrics(
            total_revenue=self._to_float(info.get("totalRevenue")),
            ebitda=self._to_float(info.get("ebitda")),
            net_income=self._to_float(info.get("netIncomeToCommon")),
            operating_cash_flow=self._to_float(
                info.get("operatingCashflow")
            ),
            free_cash_flow=self._to_float(info.get("freeCashflow")),
            total_cash=self._to_float(info.get("totalCash")),
            total_debt=self._to_float(info.get("totalDebt")),
            debt_to_equity=self._to_float(info.get("debtToEquity")),
            current_ratio=self._to_float(info.get("currentRatio")),
            quick_ratio=self._to_float(info.get("quickRatio")),
        )

        return FundamentalAnalysisResult(
            symbol=normalized_symbol,
            profile=profile,
            valuation=valuation,
            profitability=profitability,
            growth=growth,
            financial_health=financial_health,
            data_source=self.provider,
        )