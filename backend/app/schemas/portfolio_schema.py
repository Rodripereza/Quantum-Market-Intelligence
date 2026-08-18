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


class PortfolioHistorySummary(BaseModel):
    start_value: float
    end_value: float

    absolute_return: float
    return_pct: float

    max_value: float
    min_value: float

    observations: int


class PortfolioHistoryResponse(BaseModel):
    period: str
    interval: str

    currency: str

    positions: int

    history: list[PortfolioHistoryPoint]

    summary: PortfolioHistorySummary