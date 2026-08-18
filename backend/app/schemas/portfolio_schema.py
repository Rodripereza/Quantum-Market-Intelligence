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