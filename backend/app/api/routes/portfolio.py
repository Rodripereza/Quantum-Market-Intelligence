from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.portfolio import PortfolioPosition
from app.schemas.portfolio_schema import (
    PortfolioPositionSnapshot,
    PortfolioSectorAllocation,
    PortfolioSnapshot,
)
from app.services.market.market_service import MarketService


router = APIRouter(
    prefix="/api/portfolio",
    tags=["Portfolio"],
)

market_service = MarketService()


# ============================================================
# HELPERS
# ============================================================

def build_position_snapshot(
    position: PortfolioPosition,
) -> PortfolioPositionSnapshot:
    """
    Combina la posición persistida en SQLite con la cotización
    actual obtenida desde el Market Engine.
    """

    current_price = position.average_price
    previous_close = None

    try:
        quote = market_service.get_quote(position.ticker)

        market_price = quote.get("price")
        market_previous_close = quote.get("previous_close")

        if market_price is not None:
            current_price = float(market_price)

        if market_previous_close is not None:
            previous_close = float(market_previous_close)

    except Exception:
        # Si Yahoo no responde, Portfolio continúa operativo
        # utilizando el precio medio como fallback.
        current_price = position.average_price
        previous_close = None

    shares = float(position.shares)
    average_price = float(position.average_price)

    cost_basis = shares * average_price
    market_value = shares * current_price

    unrealized_pl = market_value - cost_basis

    unrealized_pl_pct = (
        (unrealized_pl / cost_basis) * 100
        if cost_basis > 0
        else 0.0
    )

    return PortfolioPositionSnapshot(
        id=position.id,
        ticker=position.ticker,
        company=position.company,
        sector=position.sector or "Unclassified",
        currency=position.currency or "USD",
        shares=shares,
        average_price=average_price,
        current_price=current_price,
        previous_close=previous_close,
        cost_basis=cost_basis,
        market_value=market_value,
        unrealized_pl=unrealized_pl,
        unrealized_pl_pct=unrealized_pl_pct,
        weight=0.0,
        notes=position.notes or "",
    )


def build_portfolio_snapshot(
    positions: list[PortfolioPosition],
) -> PortfolioSnapshot:
    """
    Construye la valoración completa del portfolio.
    """

    snapshots = [
        build_position_snapshot(position)
        for position in positions
    ]

    total_value = sum(
        position.market_value
        for position in snapshots
    )

    total_cost = sum(
        position.cost_basis
        for position in snapshots
    )

    total_pl = total_value - total_cost

    total_pl_pct = (
        (total_pl / total_cost) * 100
        if total_cost > 0
        else 0.0
    )

    # --------------------------------------------------------
    # Position weights
    # --------------------------------------------------------

    for position in snapshots:
        position.weight = (
            (position.market_value / total_value) * 100
            if total_value > 0
            else 0.0
        )

    largest_position_weight = (
        max(
            position.weight
            for position in snapshots
        )
        if snapshots
        else 0.0
    )

    # --------------------------------------------------------
    # Sector allocation
    # --------------------------------------------------------

    sector_values: dict[str, float] = {}

    for position in snapshots:
        sector = position.sector or "Unclassified"

        sector_values[sector] = (
            sector_values.get(sector, 0.0)
            + position.market_value
        )

    sector_allocation = [
        PortfolioSectorAllocation(
            sector=sector,
            value=value,
            weight=(
                (value / total_value) * 100
                if total_value > 0
                else 0.0
            ),
        )
        for sector, value in sector_values.items()
    ]

    sector_allocation.sort(
        key=lambda item: item.value,
        reverse=True,
    )

    return PortfolioSnapshot(
        positions=snapshots,
        total_value=total_value,
        total_cost=total_cost,
        total_pl=total_pl,
        total_pl_pct=total_pl_pct,
        largest_position_weight=largest_position_weight,
        sector_allocation=sector_allocation,
    )


# ============================================================
# GET PORTFOLIO SNAPSHOT
# ============================================================

@router.get("/", response_model=PortfolioSnapshot)
def get_positions(
    session: Session = Depends(get_session),
) -> PortfolioSnapshot:
    """
    Devuelve el portfolio completo valorado con precios
    actuales procedentes del Market Engine.
    """

    statement = select(
        PortfolioPosition
    ).order_by(
        PortfolioPosition.id
    )

    positions = list(
        session.exec(statement).all()
    )

    return build_portfolio_snapshot(positions)


# ============================================================
# GET SINGLE POSITION
# ============================================================

@router.get(
    "/{position_id}",
    response_model=PortfolioPosition,
)
def get_position(
    position_id: int,
    session: Session = Depends(get_session),
) -> PortfolioPosition:
    position = session.get(
        PortfolioPosition,
        position_id,
    )

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio position not found",
        )

    return position


# ============================================================
# CREATE POSITION
# ============================================================

@router.post(
    "/",
    response_model=PortfolioPosition,
    status_code=status.HTTP_201_CREATED,
)
def create_position(
    position: PortfolioPosition,
    session: Session = Depends(get_session),
) -> PortfolioPosition:
    position.id = None

    # --------------------------------------------------------
    # Normalize ticker
    # --------------------------------------------------------

    position.ticker = (
        position.ticker
        .strip()
        .upper()
    )

    if not position.ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker cannot be empty",
        )

    # --------------------------------------------------------
    # Market profile enrichment
    # --------------------------------------------------------

    try:
        profile = market_service.get_profile(
            position.ticker
        )

        position.company = (
            profile.get("company")
            or position.company
            or position.ticker
        )

        position.sector = (
            profile.get("sector")
            or position.sector
            or "Unclassified"
        )

        position.currency = (
            profile.get("currency")
            or position.currency
            or "USD"
        )

    except Exception:
        position.company = (
            position.company
            or position.ticker
        )

        position.sector = (
            position.sector
            or "Unclassified"
        )

        position.currency = (
            position.currency
            or "USD"
        )

    # --------------------------------------------------------
    # Persist
    # --------------------------------------------------------

    session.add(position)
    session.commit()
    session.refresh(position)

    return position


# ============================================================
# UPDATE POSITION
# ============================================================

@router.put(
    "/{position_id}",
    response_model=PortfolioPosition,
)
def update_position(
    position_id: int,
    updated_position: PortfolioPosition,
    session: Session = Depends(get_session),
) -> PortfolioPosition:
    position = session.get(
        PortfolioPosition,
        position_id,
    )

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio position not found",
        )

    normalized_ticker = (
        updated_position.ticker
        .strip()
        .upper()
    )

    if not normalized_ticker:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Ticker cannot be empty",
        )

    position.ticker = normalized_ticker
    position.shares = updated_position.shares
    position.average_price = (
        updated_position.average_price
    )
    position.notes = (
        updated_position.notes or ""
    )

    # --------------------------------------------------------
    # Refresh metadata
    # --------------------------------------------------------

    try:
        profile = market_service.get_profile(
            normalized_ticker
        )

        position.company = (
            profile.get("company")
            or updated_position.company
            or normalized_ticker
        )

        position.sector = (
            profile.get("sector")
            or updated_position.sector
            or "Unclassified"
        )

        position.currency = (
            profile.get("currency")
            or updated_position.currency
            or "USD"
        )

    except Exception:
        position.company = (
            updated_position.company
            or normalized_ticker
        )

        position.sector = (
            updated_position.sector
            or "Unclassified"
        )

        position.currency = (
            updated_position.currency
            or "USD"
        )

    session.add(position)
    session.commit()
    session.refresh(position)

    return position


# ============================================================
# DELETE POSITION
# ============================================================

@router.delete(
    "/{position_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_position(
    position_id: int,
    session: Session = Depends(get_session),
) -> None:
    position = session.get(
        PortfolioPosition,
        position_id,
    )

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio position not found",
        )

    session.delete(position)
    session.commit()