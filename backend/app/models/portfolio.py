from sqlmodel import SQLModel, Field
from typing import Optional


class PortfolioPosition(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    ticker: str
    company: str

    shares: float

    average_price: float

    currency: str = "USD"

    sector: str = ""

    notes: str = ""