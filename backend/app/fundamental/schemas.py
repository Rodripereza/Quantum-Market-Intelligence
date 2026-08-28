from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class CompanyProfile(BaseModel):
    """Basic identification and classification data for a company."""

    model_config = ConfigDict(extra="ignore")

    symbol: str = Field(..., min_length=1, max_length=20)
    company_name: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    country: Optional[str] = None
    # Backward-compatible trading/quote currency.
    currency: Optional[str] = None
    market_currency: Optional[str] = None
    financial_currency: Optional[str] = None
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
    shares_outstanding: Optional[float] = None
    float_shares: Optional[float] = None


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


class IncomeStatementPeriod(BaseModel):
    """Normalized income-statement snapshot for one reporting period."""

    period: str
    period_type: str
    currency: Optional[str] = None

    revenue: Optional[float] = None
    cost_of_revenue: Optional[float] = None
    gross_profit: Optional[float] = None
    operating_income: Optional[float] = None
    ebit: Optional[float] = None
    ebitda: Optional[float] = None
    pretax_income: Optional[float] = None
    tax_provision: Optional[float] = None
    net_income: Optional[float] = None

    basic_eps: Optional[float] = None
    diluted_eps: Optional[float] = None


class BalanceSheetPeriod(BaseModel):
    """Normalized balance-sheet snapshot for one reporting period."""

    period: str
    period_type: str
    currency: Optional[str] = None

    cash_and_equivalents: Optional[float] = None
    total_cash: Optional[float] = None
    current_assets: Optional[float] = None
    total_assets: Optional[float] = None

    current_liabilities: Optional[float] = None
    total_liabilities: Optional[float] = None

    short_term_debt: Optional[float] = None
    long_term_debt: Optional[float] = None
    total_debt: Optional[float] = None
    stockholders_equity: Optional[float] = None


class CashFlowPeriod(BaseModel):
    """Normalized cash-flow snapshot for one reporting period."""

    period: str
    period_type: str
    currency: Optional[str] = None

    operating_cash_flow: Optional[float] = None
    capital_expenditure: Optional[float] = None
    free_cash_flow: Optional[float] = None

    investing_cash_flow: Optional[float] = None
    financing_cash_flow: Optional[float] = None
    end_cash_position: Optional[float] = None


class FundamentalStatements(BaseModel):
    """
    Historical normalized statements.

    Annual and quarterly periods are preserved independently. TTM is
    calculated from the latest available quarterly flow statements.
    """

    annual_income: List[IncomeStatementPeriod] = Field(default_factory=list)
    quarterly_income: List[IncomeStatementPeriod] = Field(default_factory=list)
    ttm_income: Optional[IncomeStatementPeriod] = None

    annual_balance_sheet: List[BalanceSheetPeriod] = Field(default_factory=list)
    quarterly_balance_sheet: List[BalanceSheetPeriod] = Field(default_factory=list)
    latest_balance_sheet: Optional[BalanceSheetPeriod] = None

    annual_cash_flow: List[CashFlowPeriod] = Field(default_factory=list)
    quarterly_cash_flow: List[CashFlowPeriod] = Field(default_factory=list)
    ttm_cash_flow: Optional[CashFlowPeriod] = None


class FundamentalTrendMetrics(BaseModel):
    """Derived fundamental trends calculated from normalized statements."""

    revenue_yoy: Optional[float] = None
    revenue_cagr_3y: Optional[float] = None
    net_income_yoy: Optional[float] = None
    operating_income_yoy: Optional[float] = None
    free_cash_flow_yoy: Optional[float] = None

    gross_margin_ttm: Optional[float] = None
    operating_margin_ttm: Optional[float] = None
    net_margin_ttm: Optional[float] = None
    free_cash_flow_margin_ttm: Optional[float] = None

    net_cash: Optional[float] = None
    debt_to_cash: Optional[float] = None


class FundamentalIntelligenceBlock(BaseModel):
    """Interpreted state for one fundamental statement domain."""
    state: str = "UNKNOWN"
    score: Optional[float] = Field(default=None, ge=0, le=100)
    confidence: str = "LOW"
    evidence: List[str] = Field(default_factory=list)


class FundamentalStatementIntelligence(BaseModel):
    """DE-FA-002.1 calibrated statement-level fundamental intelligence."""
    income_statement: FundamentalIntelligenceBlock = Field(default_factory=FundamentalIntelligenceBlock)
    cash_flow: FundamentalIntelligenceBlock = Field(default_factory=FundamentalIntelligenceBlock)
    balance_sheet: FundamentalIntelligenceBlock = Field(default_factory=FundamentalIntelligenceBlock)
    revenue_trend: str = "UNKNOWN"
    margin_trend: str = "UNKNOWN"
    profitability_state: str = "UNKNOWN"
    cash_flow_state: str = "UNKNOWN"
    balance_sheet_state: str = "UNKNOWN"
    liquidity_state: str = "UNKNOWN"
    fundamental_regime: str = "UNKNOWN"
    regime_score: Optional[float] = Field(default=None, ge=0, le=100)
    confidence: str = "LOW"


class FundamentalQualityDimension(BaseModel):
    """One calibrated dimension of fundamental quality."""

    state: str = "UNKNOWN"
    score: Optional[float] = Field(default=None, ge=0, le=100)
    confidence: str = "LOW"
    evidence: List[str] = Field(default_factory=list)


class FundamentalQualityIntelligence(BaseModel):
    """DE-FA-003.1 — Fundamental Quality with calibrated valuation confidence."""

    business_quality: FundamentalQualityDimension = Field(
        default_factory=FundamentalQualityDimension
    )
    financial_quality: FundamentalQualityDimension = Field(
        default_factory=FundamentalQualityDimension
    )
    growth_quality: FundamentalQualityDimension = Field(
        default_factory=FundamentalQualityDimension
    )
    valuation_context: FundamentalQualityDimension = Field(
        default_factory=FundamentalQualityDimension
    )

    quality_score: Optional[float] = Field(default=None, ge=0, le=100)
    quality_regime: str = "UNKNOWN"
    valuation_state: str = "UNKNOWN"
    confidence: str = "LOW"


class FundamentalDataQuality(BaseModel):
    """Coverage diagnostics for the fundamental dataset."""

    provider: str = "yfinance"
    completeness_score: float = Field(default=0.0, ge=0, le=100)
    completeness_grade: str = "Unknown"

    snapshot_fields_available: int = 0
    snapshot_fields_total: int = 0

    annual_income_periods: int = 0
    quarterly_income_periods: int = 0
    annual_balance_periods: int = 0
    quarterly_balance_periods: int = 0
    annual_cash_flow_periods: int = 0
    quarterly_cash_flow_periods: int = 0

    has_ttm_income: bool = False
    has_ttm_cash_flow: bool = False
    has_latest_balance_sheet: bool = False

    market_currency: Optional[str] = None
    financial_currency: Optional[str] = None
    currency_mismatch: bool = False

    warnings: List[str] = Field(default_factory=list)


class FundamentalAnalysisResult(BaseModel):
    """Normalized fundamental analysis response used across QMI."""

    model_config = ConfigDict(extra="ignore")

    symbol: str
    profile: CompanyProfile
    valuation: ValuationMetrics
    profitability: ProfitabilityMetrics
    growth: GrowthMetrics
    financial_health: FinancialHealthMetrics

    # DE-FA-001 — historical statement foundation.
    statements: FundamentalStatements = Field(
        default_factory=FundamentalStatements
    )

    # DE-FA-001.1 — derived trends and dataset quality diagnostics.
    trends: FundamentalTrendMetrics = Field(
        default_factory=FundamentalTrendMetrics
    )
    data_quality: FundamentalDataQuality = Field(
        default_factory=FundamentalDataQuality
    )
    statement_intelligence: FundamentalStatementIntelligence = Field(
        default_factory=FundamentalStatementIntelligence
    )

    # DE-FA-003.0 — business/financial/growth quality plus valuation context.
    quality_intelligence: FundamentalQualityIntelligence = Field(
        default_factory=FundamentalQualityIntelligence
    )

    fundamental_score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )

    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    data_source: str = "yfinance"
    engine_version: str = "DE-FA-004.0"


class FundamentalDecision(BaseModel):
    """DE-FA-004.0 — consolidated fundamental decision layer."""

    stance: str = "UNKNOWN"
    decision_score: Optional[float] = Field(default=None, ge=0, le=100)
    conviction: str = "LOW"

    quality_score: Optional[float] = None
    regime_score: Optional[float] = None
    legacy_score: Optional[float] = None

    thesis: List[str] = Field(default_factory=list)
    catalysts: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)


class FundamentalInsight(BaseModel):
    """Interpreted fundamental analysis generated by QMI."""

    data: FundamentalAnalysisResult

    score: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
    )

    rating: str
    strengths: List[str] = Field(default_factory=list)
    weaknesses: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    decision: FundamentalDecision = Field(default_factory=FundamentalDecision)
