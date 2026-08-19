from concurrent.futures import ThreadPoolExecutor, as_completed

from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.portfolio import PortfolioPosition
from app.schemas.portfolio_schema import (
    PortfolioBenchmarkPoint,
    PortfolioBenchmarkSummary,
    PortfolioComparisonSummary,
    PortfolioHistoryPoint,
    PortfolioHistoryResponse,
    PortfolioHistorySummary,
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
# LIVE SNAPSHOT HELPERS
# ============================================================

def build_position_snapshot(
    position: PortfolioPosition,
) -> PortfolioPositionSnapshot:
    """
    Combina una posición persistida en SQLite con su cotización
    actual obtenida mediante MarketService.
    """

    current_price = float(position.average_price)
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
        # QMI mantiene operativo Portfolio aunque el proveedor
        # de mercado no esté disponible temporalmente.
        current_price = float(position.average_price)
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
    Construye el snapshot completo del portfolio valorado
    con precios actuales.
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
# HISTORICAL PERFORMANCE HELPERS
# ============================================================

def resolve_portfolio_currency(
    positions: list[PortfolioPosition],
) -> str:
    """
    Determina la moneda del portfolio.

    QMI todavía no realiza conversión FX. Si existen posiciones
    con distintas monedas, se identifica el portfolio como MULTI.
    """

    currencies = {
        (position.currency or "USD").upper()
        for position in positions
    }

    if len(currencies) == 1:
        return next(iter(currencies))

    if len(currencies) == 0:
        return "USD"

    return "MULTI"

def build_portfolio_history(
    positions: list[PortfolioPosition],
    period: str,
    interval: str,
) -> PortfolioHistoryResponse:
    """
    Construye una serie histórica mark-to-market utilizando
    las posiciones ACTUALES y precios históricos reales.

    Además compara la evolución del portfolio con el S&P 500
    normalizando ambas series a base 100.

    Importante:
    Esto todavía no es un historial transaccional.
    No existen fechas de compra/venta en el modelo actual.
    """

    currency = resolve_portfolio_currency(positions)

    if not positions:
        return PortfolioHistoryResponse(
            period=period,
            interval=interval,
            currency=currency,
            positions=0,
            history=[],
            summary=PortfolioHistorySummary(
                start_value=0.0,
                end_value=0.0,
                absolute_return=0.0,
                return_pct=0.0,
                max_value=0.0,
                min_value=0.0,
                observations=0,
            ),
            benchmark=[],
            benchmark_summary=None,
            comparison=None,
        )

    total_cost = sum(
        float(position.shares)
        * float(position.average_price)
        for position in positions
    )

    histories_by_ticker: dict[str, dict[str, float]] = {}

    benchmark_symbol = "^GSPC"
    benchmark_name = "S&P 500"
    benchmark_history: dict[str, float] = {}

    # --------------------------------------------------------
    # Download portfolio + benchmark histories in parallel
    # --------------------------------------------------------

    def download_history(symbol: str) -> tuple[str, dict[str, float]]:
        try:
            history = market_service.get_history(
                symbol=symbol,
                period=period,
                interval=interval,
            )

            ticker_history: dict[str, float] = {}

            for point in history:
                date = point.get("date")
                close = point.get("close")

                if date is None or close is None:
                    continue

                ticker_history[str(date)] = float(close)

            return symbol, ticker_history

        except Exception:
            return symbol, {}

    portfolio_symbols = list(
        dict.fromkeys(
            position.ticker
            for position in positions
        )
    )

    requested_symbols = [
        *portfolio_symbols,
        benchmark_symbol,
    ]

    max_workers = min(
        len(requested_symbols),
        8,
    )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [
            executor.submit(
                download_history,
                symbol,
            )
            for symbol in requested_symbols
        ]

        for future in as_completed(futures):
            symbol, ticker_history = future.result()

            if not ticker_history:
                continue

            if symbol == benchmark_symbol:
                benchmark_history = ticker_history
            else:
                histories_by_ticker[symbol] = ticker_history

    if not histories_by_ticker:
        return PortfolioHistoryResponse(
            period=period,
            interval=interval,
            currency=currency,
            positions=len(positions),
            history=[],
            summary=PortfolioHistorySummary(
                start_value=0.0,
                end_value=0.0,
                absolute_return=0.0,
                return_pct=0.0,
                max_value=0.0,
                min_value=0.0,
                observations=0,
            ),
            benchmark=[],
            benchmark_summary=None,
            comparison=None,
        )

    # --------------------------------------------------------
    # Use common dates for all available portfolio assets
    # --------------------------------------------------------

    date_sets = [
        set(history.keys())
        for history in histories_by_ticker.values()
    ]

    common_dates = set.intersection(*date_sets)
    sorted_dates = sorted(common_dates)

    history_points: list[PortfolioHistoryPoint] = []

    # --------------------------------------------------------
    # Build historical portfolio value
    # --------------------------------------------------------

    for date in sorted_dates:
        market_value = 0.0
        usable_positions = 0

        for position in positions:
            ticker_history = histories_by_ticker.get(
                position.ticker
            )

            if ticker_history is None:
                continue

            close = ticker_history.get(date)

            if close is None:
                continue

            market_value += (
                float(position.shares)
                * float(close)
            )

            usable_positions += 1

        if usable_positions == 0:
            continue

        profit_loss = market_value - total_cost

        return_pct = (
            (profit_loss / total_cost) * 100
            if total_cost > 0
            else 0.0
        )

        history_points.append(
            PortfolioHistoryPoint(
                date=date,
                market_value=round(
                    market_value,
                    4,
                ),
                cost_basis=round(
                    total_cost,
                    4,
                ),
                profit_loss=round(
                    profit_loss,
                    4,
                ),
                return_pct=round(
                    return_pct,
                    4,
                ),
                normalized_value=None,
            )
        )

    # --------------------------------------------------------
    # Portfolio summary
    # --------------------------------------------------------

    if not history_points:
        summary = PortfolioHistorySummary(
            start_value=0.0,
            end_value=0.0,
            absolute_return=0.0,
            return_pct=0.0,
            max_value=0.0,
            min_value=0.0,
            observations=0,
        )

    else:
        start_value = history_points[0].market_value
        end_value = history_points[-1].market_value

        absolute_return = (
            end_value - start_value
        )

        period_return_pct = (
            (absolute_return / start_value) * 100
            if start_value > 0
            else 0.0
        )

        values = [
            point.market_value
            for point in history_points
        ]

        summary = PortfolioHistorySummary(
            start_value=round(
                start_value,
                4,
            ),
            end_value=round(
                end_value,
                4,
            ),
            absolute_return=round(
                absolute_return,
                4,
            ),
            return_pct=round(
                period_return_pct,
                4,
            ),
            max_value=round(
                max(values),
                4,
            ),
            min_value=round(
                min(values),
                4,
            ),
            observations=len(history_points),
        )

    # --------------------------------------------------------
    # Portfolio vs S&P 500 comparison
    # --------------------------------------------------------

    benchmark_points: list[PortfolioBenchmarkPoint] = []
    benchmark_summary = None
    comparison = None

    if history_points and benchmark_history:
        portfolio_by_date = {
            point.date: point
            for point in history_points
        }

        comparison_dates = sorted(
            set(portfolio_by_date.keys())
            & set(benchmark_history.keys())
        )

        if comparison_dates:
            start_date = comparison_dates[0]
            end_date = comparison_dates[-1]

            portfolio_start_value = (
                portfolio_by_date[start_date].market_value
            )
            portfolio_end_value = (
                portfolio_by_date[end_date].market_value
            )

            benchmark_start_value = (
                benchmark_history[start_date]
            )
            benchmark_end_value = (
                benchmark_history[end_date]
            )

            # Normalize portfolio to base 100 using only
            # dates that can be compared directly with the benchmark.
            if portfolio_start_value > 0:
                for date in comparison_dates:
                    point = portfolio_by_date[date]

                    point.normalized_value = round(
                        (
                            point.market_value
                            / portfolio_start_value
                        )
                        * 100,
                        4,
                    )

            portfolio_period_return = (
                (
                    portfolio_end_value
                    - portfolio_start_value
                )
                / portfolio_start_value
                * 100
                if portfolio_start_value > 0
                else 0.0
            )

            benchmark_period_return = (
                (
                    benchmark_end_value
                    - benchmark_start_value
                )
                / benchmark_start_value
                * 100
                if benchmark_start_value > 0
                else 0.0
            )

            for date in comparison_dates:
                benchmark_value = benchmark_history[date]

                normalized_value = (
                    (
                        benchmark_value
                        / benchmark_start_value
                    )
                    * 100
                    if benchmark_start_value > 0
                    else 100.0
                )

                benchmark_return_pct = (
                    (
                        benchmark_value
                        - benchmark_start_value
                    )
                    / benchmark_start_value
                    * 100
                    if benchmark_start_value > 0
                    else 0.0
                )

                benchmark_points.append(
                    PortfolioBenchmarkPoint(
                        date=date,
                        benchmark_value=round(
                            benchmark_value,
                            4,
                        ),
                        normalized_value=round(
                            normalized_value,
                            4,
                        ),
                        return_pct=round(
                            benchmark_return_pct,
                            4,
                        ),
                    )
                )

            benchmark_summary = PortfolioBenchmarkSummary(
                symbol=benchmark_symbol,
                name=benchmark_name,
                start_value=round(
                    benchmark_start_value,
                    4,
                ),
                end_value=round(
                    benchmark_end_value,
                    4,
                ),
                return_pct=round(
                    benchmark_period_return,
                    4,
                ),
                observations=len(
                    benchmark_points
                ),
            )

            alpha_pct = (
                portfolio_period_return
                - benchmark_period_return
            )

            comparison = PortfolioComparisonSummary(
                portfolio_return_pct=round(
                    portfolio_period_return,
                    4,
                ),
                benchmark_return_pct=round(
                    benchmark_period_return,
                    4,
                ),
                alpha_pct=round(
                    alpha_pct,
                    4,
                ),
            )

    return PortfolioHistoryResponse(
        period=period,
        interval=interval,
        currency=currency,
        positions=len(positions),
        history=history_points,
        summary=summary,
        benchmark=benchmark_points,
        benchmark_summary=benchmark_summary,
        comparison=comparison,
    )


# ============================================================
# GET PORTFOLIO SNAPSHOT
# ============================================================

@router.get(
    "/",
    response_model=PortfolioSnapshot,
)
def get_positions(
    session: Session = Depends(get_session),
) -> PortfolioSnapshot:
    """
    Portfolio completo valorado con precios actuales.
    """

    statement = select(
        PortfolioPosition
    ).order_by(
        PortfolioPosition.id
    )

    positions = list(
        session.exec(statement).all()
    )

    return build_portfolio_snapshot(
        positions
    )


# ============================================================
# GET PORTFOLIO HISTORY
# ============================================================

@router.get(
    "/history",
    response_model=PortfolioHistoryResponse,
)
def get_portfolio_history(
    period: str = "1y",
    interval: str = "1d",
    session: Session = Depends(get_session),
) -> PortfolioHistoryResponse:
    """
    Devuelve la valoración histórica de las posiciones actuales.
    """

    statement = select(
        PortfolioPosition
    ).order_by(
        PortfolioPosition.id
    )

    positions = list(
        session.exec(statement).all()
    )

    return build_portfolio_history(
        positions=positions,
        period=period,
        interval=interval,
    )


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
    # Automatic market profile enrichment
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
    # Refresh company metadata
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