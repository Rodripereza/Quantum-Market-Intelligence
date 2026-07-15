from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CompanyProfile(BaseModel):
    """Basic identification and classification data for a company."""

    model_config = ConfigDict(extra="ignore")

    symbol: str = Field(..., min_length=1, max_length=20)
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None
    exchange: Optional[str] = None


class ValuationMetrics(BaseModel):
    """Market valuation metrics."""

    market_cap: Optional[float] = None
    enterprise_value: Optional[float] = None
    trailing_pe: Optional[float] = None
    forward_pe: Optional[float] = None
    price_to_book: Optional[float] = None
    price_to_sales: Optional[float] = None
    enterprise_to_revenue: Optional[float] = None
    enterprise_to_ebitda: Optional[float] = None


class ProfitabilityMetrics(BaseModel):
    """Profitability and return metrics."""

    gross_margin: Optional[float] = None
    operating_margin: Optional[float] = None
    net_margin: Optional[float] = None
    return_on_assets: Optional[float] = None
    return_on_equity: Optional[float] = None


class GrowthMetrics(BaseModel):
    """Revenue and earnings growth metrics."""

    revenue_growth: Optional[float] = None
    earnings_growth: Optional[float] = None
    earnings_quarterly_growth: Optional[float] = None


class FinancialHealthMetrics(BaseModel):
    """Liquidity, leverage and cash-flow metrics."""

    total_revenue: Optional[float] = None
    ebitda: Optional[float] = None
    net_income: Optional[float] = None
    operating_cash_flow: Optional[float] = None
    free_cash_flow: Optional[float] = None
    total_cash: Optional[float] = None
    total_debt: Optional[float] = None
    debt_to_equity: Optional[float] = None
    current_ratio: Optional[float] = None
    quick_ratio: Optional[float] = None


class FundamentalAnalysisResult(BaseModel):
    """Normalized fundamental analysis response used across QMI."""

    model_config = ConfigDict(extra="ignore")

    symbol: str
    profile: CompanyProfile
    valuation: ValuationMetrics
    profitability: ProfitabilityMetrics
    growth: GrowthMetrics
    financial_health: FinancialHealthMetrics

    fundamental_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )

    generated_at: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc)
    )

    data_source: str = "yfinance"