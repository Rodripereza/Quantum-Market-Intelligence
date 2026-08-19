from typing import Optional

from pydantic import BaseModel


class PortfolioPositionSnapshot(BaseModel):
    id: int

    ticker: str
    company: str
    sector: str
    currency: str

    shares: float
    average_price: float

    current_price: Optional[float] = None
    previous_close: Optional[float] = None

    cost_basis: float
    market_value: float

    unrealized_pl: float
    unrealized_pl_pct: float

    weight: float = 0.0

    notes: str = ""


class PortfolioSectorAllocation(BaseModel):
    sector: str
    value: float
    weight: float


class PortfolioSnapshot(BaseModel):
    positions: list[PortfolioPositionSnapshot]

    total_value: float
    total_cost: float

    total_pl: float
    total_pl_pct: float

    largest_position_weight: float

    sector_allocation: list[PortfolioSectorAllocation]


# ============================================================
# HISTORICAL PERFORMANCE
# ============================================================

class PortfolioHistoryPoint(BaseModel):
    date: str

    market_value: float
    cost_basis: float

    profit_loss: float
    return_pct: float

    normalized_value: Optional[float] = None

class PortfolioHistorySummary(BaseModel):
    start_value: float
    end_value: float

    absolute_return: float
    return_pct: float

    max_value: float
    min_value: float

    observations: int


class PortfolioBenchmarkPoint(BaseModel):
    date: str

    benchmark_value: float
    normalized_value: float
    return_pct: float


class PortfolioBenchmarkSummary(BaseModel):
    symbol: str
    name: str

    start_value: float
    end_value: float
    return_pct: float

    observations: int


class PortfolioComparisonSummary(BaseModel):
    portfolio_return_pct: float
    benchmark_return_pct: float
    alpha_pct: float


class PortfolioRiskMetrics(BaseModel):
    annualization_factor: int
    risk_free_rate_pct: float

    volatility_pct: Optional[float] = None
    sharpe_ratio: Optional[float] = None
    max_drawdown_pct: Optional[float] = None

    beta: Optional[float] = None
    tracking_error_pct: Optional[float] = None
    information_ratio: Optional[float] = None

    observations: int = 0


class PortfolioHistoryResponse(BaseModel):
    period: str
    interval: str

    currency: str

    positions: int

    history: list[PortfolioHistoryPoint]

    summary: PortfolioHistorySummary

    benchmark: list[PortfolioBenchmarkPoint] = []
    benchmark_summary: Optional[PortfolioBenchmarkSummary] = None
    comparison: Optional[PortfolioComparisonSummary] = None
    risk_metrics: Optional[PortfolioRiskMetrics] = None