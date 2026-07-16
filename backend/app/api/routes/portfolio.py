from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.portfolio import PortfolioPosition


router = APIRouter(
    prefix="/api/portfolio",
    tags=["Portfolio"],
)


@router.get("/", response_model=list[PortfolioPosition])
def get_positions(
    session: Session = Depends(get_session),
) -> list[PortfolioPosition]:
    statement = select(PortfolioPosition).order_by(PortfolioPosition.id)
    return list(session.exec(statement).all())


@router.get("/{position_id}", response_model=PortfolioPosition)
def get_position(
    position_id: int,
    session: Session = Depends(get_session),
) -> PortfolioPosition:
    position = session.get(PortfolioPosition, position_id)

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio position not found",
        )

    return position


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

    session.add(position)
    session.commit()
    session.refresh(position)

    return position


@router.put("/{position_id}", response_model=PortfolioPosition)
def update_position(
    position_id: int,
    updated_position: PortfolioPosition,
    session: Session = Depends(get_session),
) -> PortfolioPosition:
    position = session.get(PortfolioPosition, position_id)

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio position not found",
        )

    position.ticker = updated_position.ticker
    position.company = updated_position.company
    position.shares = updated_position.shares
    position.average_price = updated_position.average_price
    position.currency = updated_position.currency
    position.sector = updated_position.sector
    position.notes = updated_position.notes

    session.add(position)
    session.commit()
    session.refresh(position)

    return position


@router.delete(
    "/{position_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_position(
    position_id: int,
    session: Session = Depends(get_session),
) -> None:
    position = session.get(PortfolioPosition, position_id)

    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Portfolio position not found",
        )

    session.delete(position)
    session.commit()