"""
Fundamental Data Collector

DE-FA-004.0 — Fundamental Decision Engine Foundation.

Retrieves company fundamental data from yfinance and converts it into
QMI normalized schemas. The collector preserves the existing current
snapshot and statement history while adding derived trend metrics and explicit data-quality diagnostics.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Optional

import pandas as pd
import yfinance as yf

from app.fundamental.schemas import (
    BalanceSheetPeriod,
    CashFlowPeriod,
    CompanyProfile,
    FinancialHealthMetrics,
    FundamentalAnalysisResult,
    FundamentalDataQuality,
    FundamentalStatements,
    FundamentalTrendMetrics,
    FundamentalIntelligenceBlock,
    FundamentalStatementIntelligence,
    FundamentalQualityDimension,
    FundamentalQualityIntelligence,
    GrowthMetrics,
    IncomeStatementPeriod,
    ProfitabilityMetrics,
    ValuationMetrics,
)


class FundamentalCollector:
    """Retrieve and normalize fundamental company data."""

    def __init__(self) -> None:
        self.provider = "yfinance"

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        """Convert provider values to float safely."""

        if value is None:
            return None

        try:
            number = float(value)
        except (TypeError, ValueError):
            return None

        if pd.isna(number):
            return None

        return number

    @staticmethod
    def _period_label(value: Any) -> str:
        """Normalize dataframe column labels into ISO-like period strings."""

        if isinstance(value, pd.Timestamp):
            return value.date().isoformat()

        if isinstance(value, datetime):
            return value.date().isoformat()

        try:
            parsed = pd.to_datetime(value, errors="coerce")
            if not pd.isna(parsed):
                return parsed.date().isoformat()
        except Exception:
            pass

        return str(value)

    @staticmethod
    def _safe_statement(ticker: yf.Ticker, attribute: str) -> pd.DataFrame:
        """
        Read a yfinance statement safely.

        yfinance can return None or an empty DataFrame for companies with
        incomplete provider coverage. DE-FA-001 treats those cases as
        missing data rather than fatal errors.
        """

        try:
            frame = getattr(ticker, attribute)
        except Exception:
            return pd.DataFrame()

        if frame is None or not isinstance(frame, pd.DataFrame):
            return pd.DataFrame()

        if frame.empty:
            return pd.DataFrame()

        return frame.copy()

    @staticmethod
    def _row_value(
        frame: pd.DataFrame,
        column: Any,
        candidates: Iterable[str],
    ) -> Optional[float]:
        """Return the first numeric value found among candidate row names."""

        if frame.empty or column not in frame.columns:
            return None

        normalized_index = {
            str(index).strip().lower(): index
            for index in frame.index
        }

        for candidate in candidates:
            key = candidate.strip().lower()
            row = normalized_index.get(key)
            if row is None:
                continue

            value = frame.at[row, column]
            try:
                number = float(value)
            except (TypeError, ValueError):
                continue

            if pd.isna(number):
                continue

            return number

        return None

    def _income_periods(
        self,
        frame: pd.DataFrame,
        period_type: str,
        currency: Optional[str],
    ) -> list[IncomeStatementPeriod]:
        """Normalize an income statement dataframe into QMI periods."""

        if frame.empty:
            return []

        periods: list[IncomeStatementPeriod] = []

        for column in frame.columns:
            periods.append(
                IncomeStatementPeriod(
                    period=self._period_label(column),
                    period_type=period_type,
                    currency=currency,
                    revenue=self._row_value(
                        frame,
                        column,
                        ("Total Revenue", "Operating Revenue"),
                    ),
                    cost_of_revenue=self._row_value(
                        frame,
                        column,
                        ("Cost Of Revenue", "Reconciled Cost Of Revenue"),
                    ),
                    gross_profit=self._row_value(
                        frame,
                        column,
                        ("Gross Profit",),
                    ),
                    operating_income=self._row_value(
                        frame,
                        column,
                        ("Operating Income",),
                    ),
                    ebit=self._row_value(
                        frame,
                        column,
                        ("EBIT",),
                    ),
                    ebitda=self._row_value(
                        frame,
                        column,
                        ("EBITDA", "Normalized EBITDA"),
                    ),
                    pretax_income=self._row_value(
                        frame,
                        column,
                        ("Pretax Income", "Pre Tax Income"),
                    ),
                    tax_provision=self._row_value(
                        frame,
                        column,
                        ("Tax Provision",),
                    ),
                    net_income=self._row_value(
                        frame,
                        column,
                        (
                            "Net Income",
                            "Net Income Common Stockholders",
                            "Net Income Including Noncontrolling Interests",
                        ),
                    ),
                    basic_eps=self._row_value(
                        frame,
                        column,
                        ("Basic EPS",),
                    ),
                    diluted_eps=self._row_value(
                        frame,
                        column,
                        ("Diluted EPS",),
                    ),
                )
            )

        return sorted(periods, key=lambda item: item.period, reverse=True)

    def _balance_periods(
        self,
        frame: pd.DataFrame,
        period_type: str,
        currency: Optional[str],
    ) -> list[BalanceSheetPeriod]:
        """Normalize a balance-sheet dataframe into QMI periods."""

        if frame.empty:
            return []

        periods: list[BalanceSheetPeriod] = []

        for column in frame.columns:
            cash = self._row_value(
                frame,
                column,
                (
                    "Cash Cash Equivalents And Short Term Investments",
                    "Cash And Cash Equivalents",
                    "Cash Financial",
                ),
            )

            total_debt = self._row_value(
                frame,
                column,
                ("Total Debt",),
            )

            short_term_debt = self._row_value(
                frame,
                column,
                (
                    "Current Debt",
                    "Current Debt And Capital Lease Obligation",
                ),
            )

            long_term_debt = self._row_value(
                frame,
                column,
                (
                    "Long Term Debt",
                    "Long Term Debt And Capital Lease Obligation",
                ),
            )

            if total_debt is None:
                debt_parts = [
                    value
                    for value in (short_term_debt, long_term_debt)
                    if value is not None
                ]
                total_debt = sum(debt_parts) if debt_parts else None

            periods.append(
                BalanceSheetPeriod(
                    period=self._period_label(column),
                    period_type=period_type,
                    currency=currency,
                    cash_and_equivalents=cash,
                    total_cash=cash,
                    current_assets=self._row_value(
                        frame,
                        column,
                        ("Current Assets", "Total Current Assets"),
                    ),
                    total_assets=self._row_value(
                        frame,
                        column,
                        ("Total Assets",),
                    ),
                    current_liabilities=self._row_value(
                        frame,
                        column,
                        (
                            "Current Liabilities",
                            "Total Current Liabilities",
                        ),
                    ),
                    total_liabilities=self._row_value(
                        frame,
                        column,
                        (
                            "Total Liabilities Net Minority Interest",
                            "Total Liabilities",
                        ),
                    ),
                    short_term_debt=short_term_debt,
                    long_term_debt=long_term_debt,
                    total_debt=total_debt,
                    stockholders_equity=self._row_value(
                        frame,
                        column,
                        (
                            "Stockholders Equity",
                            "Total Equity Gross Minority Interest",
                        ),
                    ),
                )
            )

        return sorted(periods, key=lambda item: item.period, reverse=True)

    def _cash_flow_periods(
        self,
        frame: pd.DataFrame,
        period_type: str,
        currency: Optional[str],
    ) -> list[CashFlowPeriod]:
        """Normalize a cash-flow dataframe into QMI periods."""

        if frame.empty:
            return []

        periods: list[CashFlowPeriod] = []

        for column in frame.columns:
            operating_cash_flow = self._row_value(
                frame,
                column,
                (
                    "Operating Cash Flow",
                    "Total Cash From Operating Activities",
                ),
            )

            capital_expenditure = self._row_value(
                frame,
                column,
                ("Capital Expenditure", "Capital Expenditures"),
            )

            free_cash_flow = self._row_value(
                frame,
                column,
                ("Free Cash Flow",),
            )

            # yfinance commonly reports CapEx as a negative cash outflow.
            if (
                free_cash_flow is None
                and operating_cash_flow is not None
                and capital_expenditure is not None
            ):
                free_cash_flow = (
                    operating_cash_flow + capital_expenditure
                    if capital_expenditure < 0
                    else operating_cash_flow - capital_expenditure
                )

            periods.append(
                CashFlowPeriod(
                    period=self._period_label(column),
                    period_type=period_type,
                    currency=currency,
                    operating_cash_flow=operating_cash_flow,
                    capital_expenditure=capital_expenditure,
                    free_cash_flow=free_cash_flow,
                    investing_cash_flow=self._row_value(
                        frame,
                        column,
                        ("Investing Cash Flow",),
                    ),
                    financing_cash_flow=self._row_value(
                        frame,
                        column,
                        ("Financing Cash Flow",),
                    ),
                    end_cash_position=self._row_value(
                        frame,
                        column,
                        ("End Cash Position",),
                    ),
                )
            )

        return sorted(periods, key=lambda item: item.period, reverse=True)

    @staticmethod
    def _sum_values(
        periods: list[Any],
        attribute: str,
        limit: int = 4,
    ) -> Optional[float]:
        """Sum the latest non-null quarterly values for a flow metric."""

        values = [
            getattr(period, attribute)
            for period in periods[:limit]
            if getattr(period, attribute) is not None
        ]

        if not values:
            return None

        return float(sum(values))

    def _build_ttm_income(
        self,
        periods: list[IncomeStatementPeriod],
        currency: Optional[str],
    ) -> Optional[IncomeStatementPeriod]:
        """Build TTM income values from the latest four quarters."""

        if not periods:
            return None

        return IncomeStatementPeriod(
            period="TTM",
            period_type="ttm",
            currency=currency,
            revenue=self._sum_values(periods, "revenue"),
            cost_of_revenue=self._sum_values(periods, "cost_of_revenue"),
            gross_profit=self._sum_values(periods, "gross_profit"),
            operating_income=self._sum_values(periods, "operating_income"),
            ebit=self._sum_values(periods, "ebit"),
            ebitda=self._sum_values(periods, "ebitda"),
            pretax_income=self._sum_values(periods, "pretax_income"),
            tax_provision=self._sum_values(periods, "tax_provision"),
            net_income=self._sum_values(periods, "net_income"),
            basic_eps=self._sum_values(periods, "basic_eps"),
            diluted_eps=self._sum_values(periods, "diluted_eps"),
        )

    def _build_ttm_cash_flow(
        self,
        periods: list[CashFlowPeriod],
        currency: Optional[str],
    ) -> Optional[CashFlowPeriod]:
        """Build TTM cash-flow values from the latest four quarters."""

        if not periods:
            return None

        return CashFlowPeriod(
            period="TTM",
            period_type="ttm",
            currency=currency,
            operating_cash_flow=self._sum_values(
                periods,
                "operating_cash_flow",
            ),
            capital_expenditure=self._sum_values(
                periods,
                "capital_expenditure",
            ),
            free_cash_flow=self._sum_values(
                periods,
                "free_cash_flow",
            ),
            investing_cash_flow=self._sum_values(
                periods,
                "investing_cash_flow",
            ),
            financing_cash_flow=self._sum_values(
                periods,
                "financing_cash_flow",
            ),
            end_cash_position=periods[0].end_cash_position,
        )


    @staticmethod
    def _safe_ratio(numerator: Optional[float], denominator: Optional[float]) -> Optional[float]:
        """Return numerator / denominator when both values are usable."""
        if numerator is None or denominator in (None, 0):
            return None
        return float(numerator / denominator)

    @staticmethod
    def _growth(current: Optional[float], previous: Optional[float]) -> Optional[float]:
        """Return period-over-period growth using the absolute prior base."""
        if current is None or previous in (None, 0):
            return None
        return float((current - previous) / abs(previous))

    @staticmethod
    def _cagr(current: Optional[float], oldest: Optional[float], years: int) -> Optional[float]:
        """Return CAGR when both endpoints are positive and the span is valid."""
        if current is None or oldest is None or years <= 0:
            return None
        if current <= 0 or oldest <= 0:
            return None
        return float((current / oldest) ** (1 / years) - 1)

    @staticmethod
    def _first_available(*values: Optional[float]) -> Optional[float]:
        """Return the first non-null value without converting missing data to zero."""
        for value in values:
            if value is not None:
                return float(value)
        return None

    def _normalize_from_statements(
        self,
        valuation: ValuationMetrics,
        profitability: ProfitabilityMetrics,
        growth: GrowthMetrics,
        health: FinancialHealthMetrics,
        statements: FundamentalStatements,
        market_price: Optional[float],
        market_currency: Optional[str],
        financial_currency: Optional[str],
    ) -> tuple[
        ValuationMetrics,
        ProfitabilityMetrics,
        GrowthMetrics,
        FinancialHealthMetrics,
    ]:
        """Reconstruct missing snapshot metrics from normalized statements."""
        ttm_income = statements.ttm_income
        ttm_cash = statements.ttm_cash_flow
        latest_balance = statements.latest_balance_sheet

        revenue = self._first_available(
            health.total_revenue,
            ttm_income.revenue if ttm_income else None,
            statements.annual_income[0].revenue if statements.annual_income else None,
        )
        ebitda = self._first_available(
            health.ebitda,
            ttm_income.ebitda if ttm_income else None,
            statements.annual_income[0].ebitda if statements.annual_income else None,
        )
        net_income = self._first_available(
            health.net_income,
            ttm_income.net_income if ttm_income else None,
            statements.annual_income[0].net_income if statements.annual_income else None,
        )
        operating_cash_flow = self._first_available(
            health.operating_cash_flow,
            ttm_cash.operating_cash_flow if ttm_cash else None,
            statements.annual_cash_flow[0].operating_cash_flow if statements.annual_cash_flow else None,
        )
        free_cash_flow = self._first_available(
            health.free_cash_flow,
            ttm_cash.free_cash_flow if ttm_cash else None,
            statements.annual_cash_flow[0].free_cash_flow if statements.annual_cash_flow else None,
        )
        total_cash = self._first_available(
            health.total_cash,
            latest_balance.total_cash if latest_balance else None,
        )
        total_debt = self._first_available(
            health.total_debt,
            latest_balance.total_debt if latest_balance else None,
        )

        current_assets = latest_balance.current_assets if latest_balance else None
        current_liabilities = latest_balance.current_liabilities if latest_balance else None
        equity = latest_balance.stockholders_equity if latest_balance else None

        current_ratio = self._first_available(
            health.current_ratio,
            self._safe_ratio(current_assets, current_liabilities),
        )
        debt_to_equity = self._first_available(
            health.debt_to_equity,
            self._safe_ratio(total_debt, equity),
        )

        gross_margin = self._first_available(
            profitability.gross_margin,
            self._safe_ratio(ttm_income.gross_profit if ttm_income else None, revenue),
        )
        operating_margin = self._first_available(
            profitability.operating_margin,
            self._safe_ratio(ttm_income.operating_income if ttm_income else None, revenue),
        )
        net_margin = self._first_available(
            profitability.net_margin,
            self._safe_ratio(net_income, revenue),
        )

        market_cap = valuation.market_cap
        if (
            market_cap is None
            and market_price is not None
            and valuation.shares_outstanding is not None
        ):
            # Price and shares both belong to the traded security, so this is
            # safe in market currency.
            market_cap = market_price * valuation.shares_outstanding

        same_currency = bool(
            market_currency
            and financial_currency
            and market_currency.upper() == financial_currency.upper()
        )

        # Never combine an ADR's USD market value with CNY/EUR/etc. financial
        # statement balances. Provider ratios remain valid when Yahoo supplies
        # them directly; statement-derived valuation fallbacks require a common
        # currency until an explicit FX layer exists.
        enterprise_value = valuation.enterprise_value
        if (
            enterprise_value is None
            and same_currency
            and market_cap is not None
            and total_debt is not None
            and total_cash is not None
        ):
            enterprise_value = market_cap + total_debt - total_cash

        price_to_sales = valuation.price_to_sales
        price_to_book = valuation.price_to_book
        enterprise_to_revenue = valuation.enterprise_to_revenue
        enterprise_to_ebitda = valuation.enterprise_to_ebitda

        if same_currency:
            price_to_sales = self._first_available(
                price_to_sales,
                self._safe_ratio(market_cap, revenue),
            )
            price_to_book = self._first_available(
                price_to_book,
                self._safe_ratio(market_cap, equity),
            )
            enterprise_to_revenue = self._first_available(
                enterprise_to_revenue,
                self._safe_ratio(enterprise_value, revenue),
            )
            enterprise_to_ebitda = self._first_available(
                enterprise_to_ebitda,
                self._safe_ratio(enterprise_value, ebitda),
            )

        revenue_growth = growth.revenue_growth
        earnings_growth = growth.earnings_growth
        if len(statements.annual_income) >= 2:
            revenue_growth = self._first_available(
                revenue_growth,
                self._growth(statements.annual_income[0].revenue, statements.annual_income[1].revenue),
            )
            earnings_growth = self._first_available(
                earnings_growth,
                self._growth(statements.annual_income[0].net_income, statements.annual_income[1].net_income),
            )

        return (
            valuation.model_copy(update={
                "market_cap": market_cap,
                "enterprise_value": enterprise_value,
                "price_to_book": price_to_book,
                "price_to_sales": price_to_sales,
                "enterprise_to_revenue": enterprise_to_revenue,
                "enterprise_to_ebitda": enterprise_to_ebitda,
            }),
            profitability.model_copy(update={
                "gross_margin": gross_margin,
                "operating_margin": operating_margin,
                "net_margin": net_margin,
            }),
            growth.model_copy(update={
                "revenue_growth": revenue_growth,
                "earnings_growth": earnings_growth,
            }),
            health.model_copy(update={
                "total_revenue": revenue,
                "ebitda": ebitda,
                "net_income": net_income,
                "operating_cash_flow": operating_cash_flow,
                "free_cash_flow": free_cash_flow,
                "total_cash": total_cash,
                "total_debt": total_debt,
                "debt_to_equity": debt_to_equity,
                "current_ratio": current_ratio,
            }),
        )

    def _build_trends(
        self,
        statements: FundamentalStatements,
        health: FinancialHealthMetrics,
    ) -> FundamentalTrendMetrics:
        """Build provider-independent trend metrics from normalized statements."""
        annual_income = statements.annual_income
        annual_cash = statements.annual_cash_flow
        ttm_income = statements.ttm_income
        ttm_cash = statements.ttm_cash_flow
        latest_balance = statements.latest_balance_sheet

        revenue_yoy = None
        net_income_yoy = None
        operating_income_yoy = None
        revenue_cagr_3y = None

        if len(annual_income) >= 2:
            revenue_yoy = self._growth(annual_income[0].revenue, annual_income[1].revenue)
            net_income_yoy = self._growth(annual_income[0].net_income, annual_income[1].net_income)
            operating_income_yoy = self._growth(
                annual_income[0].operating_income,
                annual_income[1].operating_income,
            )

        # Four annual endpoints represent approximately a three-year span.
        if len(annual_income) >= 4:
            revenue_cagr_3y = self._cagr(
                annual_income[0].revenue,
                annual_income[3].revenue,
                3,
            )

        free_cash_flow_yoy = None
        if len(annual_cash) >= 2:
            free_cash_flow_yoy = self._growth(
                annual_cash[0].free_cash_flow,
                annual_cash[1].free_cash_flow,
            )

        ttm_revenue = ttm_income.revenue if ttm_income else None
        gross_margin_ttm = self._safe_ratio(
            ttm_income.gross_profit if ttm_income else None,
            ttm_revenue,
        )
        operating_margin_ttm = self._safe_ratio(
            ttm_income.operating_income if ttm_income else None,
            ttm_revenue,
        )
        net_margin_ttm = self._safe_ratio(
            ttm_income.net_income if ttm_income else None,
            ttm_revenue,
        )
        free_cash_flow_margin_ttm = self._safe_ratio(
            ttm_cash.free_cash_flow if ttm_cash else None,
            ttm_revenue,
        )

        total_cash = (
            latest_balance.total_cash
            if latest_balance and latest_balance.total_cash is not None
            else health.total_cash
        )
        total_debt = (
            latest_balance.total_debt
            if latest_balance and latest_balance.total_debt is not None
            else health.total_debt
        )

        net_cash = None
        if total_cash is not None and total_debt is not None:
            net_cash = float(total_cash - total_debt)

        debt_to_cash = self._safe_ratio(total_debt, total_cash)

        return FundamentalTrendMetrics(
            revenue_yoy=revenue_yoy,
            revenue_cagr_3y=revenue_cagr_3y,
            net_income_yoy=net_income_yoy,
            operating_income_yoy=operating_income_yoy,
            free_cash_flow_yoy=free_cash_flow_yoy,
            gross_margin_ttm=gross_margin_ttm,
            operating_margin_ttm=operating_margin_ttm,
            net_margin_ttm=net_margin_ttm,
            free_cash_flow_margin_ttm=free_cash_flow_margin_ttm,
            net_cash=net_cash,
            debt_to_cash=debt_to_cash,
        )


    @staticmethod
    def _intel_confidence(count: int) -> str:
        if count >= 4:
            return "HIGH"
        if count >= 2:
            return "MEDIUM"
        return "LOW"

    @staticmethod
    def _trend_delta(current: Optional[float], previous: Optional[float], threshold: float = 0.02) -> str:
        if current is None or previous is None:
            return "UNKNOWN"
        delta = current - previous
        if delta > threshold:
            return "IMPROVING"
        if delta < -threshold:
            return "DETERIORATING"
        return "STABLE"

    def _build_statement_intelligence(
        self,
        statements: FundamentalStatements,
        trends: FundamentalTrendMetrics,
        health: FinancialHealthMetrics,
    ) -> FundamentalStatementIntelligence:
        """Interpret normalized statements without inventing missing values."""
        income_evidence: list[str] = []
        income_points = 0.0
        income_checks = 0

        for value, positive, strong, labels in (
            (trends.revenue_yoy, 0.0, 0.10, ("Revenue is contracting year over year", "Revenue is growing year over year", "Revenue is growing strongly year over year")),
            (trends.revenue_cagr_3y, 0.0, 0.10, ("Three-year revenue CAGR is negative", "Three-year revenue CAGR is positive", "Three-year revenue CAGR is strong")),
        ):
            if value is not None:
                income_checks += 1
                if value >= strong:
                    income_points += 1.0; income_evidence.append(labels[2])
                elif value > positive:
                    income_points += 0.65; income_evidence.append(labels[1])
                else:
                    income_evidence.append(labels[0])

        for value, name in ((trends.operating_margin_ttm, "operating"), (trends.net_margin_ttm, "net")):
            if value is not None:
                income_checks += 1
                if value > 0:
                    income_points += 1.0; income_evidence.append(f"TTM {name} margin is positive")
                elif value > -0.10:
                    income_points += 0.4; income_evidence.append(f"TTM {name} margin remains negative but is improving from prior levels")
                else:
                    income_evidence.append(f"TTM {name} margin is materially negative")

        income_score = round(100 * income_points / income_checks, 1) if income_checks else None

        profitability_is_positive = (
            trends.net_margin_ttm is not None
            and trends.net_margin_ttm > 0
            and trends.operating_margin_ttm is not None
            and trends.operating_margin_ttm > 0
        )

        recovery_evidence = (
            trends.revenue_yoy is not None
            and trends.revenue_yoy > 0
            and (
                trends.operating_income_yoy is not None
                and trends.operating_income_yoy > 0
            )
        )

        if income_score is None:
            income_state = "UNKNOWN"
        elif income_score >= 70 and profitability_is_positive:
            income_state = "STRONG"
        elif income_score >= 45 and recovery_evidence:
            income_state = "RECOVERING"
        elif income_score >= 45:
            income_state = "MIXED"
        else:
            income_state = "WEAK"

        cash_evidence: list[str] = []
        cash_points = 0.0
        cash_checks = 0
        for value, label in ((health.operating_cash_flow, "Operating cash flow"), (health.free_cash_flow, "Free cash flow")):
            if value is not None:
                cash_checks += 1
                if value > 0:
                    cash_points += 1.0; cash_evidence.append(f"{label} is positive")
                else:
                    cash_evidence.append(f"{label} is negative")
        if trends.free_cash_flow_yoy is not None:
            cash_checks += 1
            if trends.free_cash_flow_yoy > 0:
                cash_points += 0.8; cash_evidence.append("Free cash flow is improving year over year")
            else:
                cash_evidence.append("Free cash flow is deteriorating year over year")
        if trends.free_cash_flow_margin_ttm is not None:
            cash_checks += 1
            if trends.free_cash_flow_margin_ttm >= 0.05:
                cash_points += 1.0; cash_evidence.append("TTM free-cash-flow margin is healthy")
            elif trends.free_cash_flow_margin_ttm >= 0:
                cash_points += 0.65; cash_evidence.append("TTM free-cash-flow margin is positive")
            else:
                cash_evidence.append("TTM free-cash-flow margin is negative")

        cash_score = round(100 * cash_points / cash_checks, 1) if cash_checks else None
        cash_state = "UNKNOWN" if cash_score is None else ("STRONG" if cash_score >= 70 else "RECOVERING" if cash_score >= 45 else "WEAK")

        balance_evidence: list[str] = []
        balance_points = 0.0
        balance_checks = 0
        if trends.net_cash is not None:
            balance_checks += 1
            if trends.net_cash > 0:
                balance_points += 1.0; balance_evidence.append("Balance sheet holds net cash")
            else:
                balance_evidence.append("Balance sheet holds net debt")
        if health.current_ratio is not None:
            balance_checks += 1
            if health.current_ratio >= 1.5:
                balance_points += 1.0; balance_evidence.append("Short-term liquidity is strong")
            elif health.current_ratio >= 1.0:
                balance_points += 0.65; balance_evidence.append("Short-term liquidity is adequate")
            else:
                balance_evidence.append("Short-term liquidity is weak")
        if trends.debt_to_cash is not None:
            balance_checks += 1
            if trends.debt_to_cash <= 0.75:
                balance_points += 1.0; balance_evidence.append("Cash comfortably covers debt")
            elif trends.debt_to_cash <= 1.0:
                balance_points += 0.7; balance_evidence.append("Cash broadly covers debt")
            else:
                balance_evidence.append("Debt exceeds cash")

        balance_score = round(100 * balance_points / balance_checks, 1) if balance_checks else None
        balance_state = "UNKNOWN" if balance_score is None else ("STRONG" if balance_score >= 70 else "STABLE" if balance_score >= 45 else "WEAK")

        revenue_trend = "UNKNOWN" if trends.revenue_yoy is None else ("IMPROVING" if trends.revenue_yoy > 0 else "DETERIORATING" if trends.revenue_yoy < 0 else "STABLE")
        margin_trend = "UNKNOWN"
        if len(statements.annual_income) >= 2:
            a, b = statements.annual_income[0], statements.annual_income[1]
            margin_trend = self._trend_delta(self._safe_ratio(a.operating_income, a.revenue), self._safe_ratio(b.operating_income, b.revenue))

        profitability_state = "UNKNOWN" if trends.net_margin_ttm is None else ("PROFITABLE" if trends.net_margin_ttm > 0 else "LOSS_MAKING")
        liquidity_state = "UNKNOWN" if health.current_ratio is None else ("STRONG" if health.current_ratio >= 1.5 else "ADEQUATE" if health.current_ratio >= 1.0 else "WEAK")

        scores = [x for x in (income_score, cash_score, balance_score) if x is not None]
        regime_score = round(sum(scores) / len(scores), 1) if scores else None
        if regime_score is None:
            regime = "UNKNOWN"
        elif (
            regime_score >= 75
            and profitability_state == "PROFITABLE"
            and cash_state == "STRONG"
        ):
            regime = "EXPANSION"
        elif (
            revenue_trend == "IMPROVING"
            and margin_trend == "IMPROVING"
            and profitability_state == "LOSS_MAKING"
        ):
            regime = "RECOVERY"
        elif (
            revenue_trend == "IMPROVING"
            and cash_state == "RECOVERING"
        ):
            regime = "RECOVERY"
        elif regime_score >= 55:
            regime = "STABLE"
        elif revenue_trend == "DETERIORATING" or margin_trend == "DETERIORATING":
            regime = "DETERIORATION"
        else:
            regime = "WEAK"

        return FundamentalStatementIntelligence(
            income_statement=FundamentalIntelligenceBlock(state=income_state, score=income_score, confidence=self._intel_confidence(income_checks), evidence=income_evidence),
            cash_flow=FundamentalIntelligenceBlock(state=cash_state, score=cash_score, confidence=self._intel_confidence(cash_checks), evidence=cash_evidence),
            balance_sheet=FundamentalIntelligenceBlock(state=balance_state, score=balance_score, confidence=self._intel_confidence(balance_checks), evidence=balance_evidence),
            revenue_trend=revenue_trend,
            margin_trend=margin_trend,
            profitability_state=profitability_state,
            cash_flow_state=cash_state,
            balance_sheet_state=balance_state,
            liquidity_state=liquidity_state,
            fundamental_regime=regime,
            regime_score=regime_score,
            confidence=self._intel_confidence(income_checks + cash_checks + balance_checks),
        )

    @staticmethod
    def _quality_state(score: Optional[float]) -> str:
        if score is None:
            return "UNKNOWN"
        if score >= 80:
            return "STRONG"
        if score >= 65:
            return "GOOD"
        if score >= 50:
            return "ADEQUATE"
        if score >= 35:
            return "WEAK"
        return "POOR"

    @staticmethod
    def _valuation_state(score: Optional[float], checks: int) -> str:
        if checks < 2 or score is None:
            return "LIMITED_DATA"
        if score >= 75:
            return "ATTRACTIVE"
        if score >= 55:
            return "REASONABLE"
        if score >= 35:
            return "ELEVATED"
        return "EXPENSIVE"

    def _build_quality_intelligence(
        self,
        valuation: ValuationMetrics,
        profitability: ProfitabilityMetrics,
        growth: GrowthMetrics,
        health: FinancialHealthMetrics,
        trends: FundamentalTrendMetrics,
        statements: FundamentalStatements,
        data_quality: FundamentalDataQuality,
    ) -> FundamentalQualityIntelligence:
        """Build DE-FA-003.0 multi-dimensional fundamental quality intelligence."""

        # -------------------------
        # 1) BUSINESS QUALITY
        # -------------------------
        business_points = 0.0
        business_checks = 0
        business_evidence: list[str] = []

        if trends.gross_margin_ttm is not None:
            business_checks += 1
            if trends.gross_margin_ttm >= 0.30:
                business_points += 1.0
                business_evidence.append("Gross margin is strong")
            elif trends.gross_margin_ttm >= 0.15:
                business_points += 0.75
                business_evidence.append("Gross margin is healthy")
            elif trends.gross_margin_ttm > 0:
                business_points += 0.45
                business_evidence.append("Gross margin is positive but modest")
            else:
                business_evidence.append("Gross margin is weak")

        if trends.operating_margin_ttm is not None:
            business_checks += 1
            if trends.operating_margin_ttm >= 0.15:
                business_points += 1.0
                business_evidence.append("Operating margin is strong")
            elif trends.operating_margin_ttm > 0:
                business_points += 0.75
                business_evidence.append("Operating margin is positive")
            elif trends.operating_margin_ttm > -0.10:
                business_points += 0.40
                business_evidence.append("Operating margin is negative but within recovery range")
            else:
                business_evidence.append("Operating margin is materially negative")

        if trends.net_margin_ttm is not None:
            business_checks += 1
            if trends.net_margin_ttm >= 0.10:
                business_points += 1.0
                business_evidence.append("Net margin is healthy")
            elif trends.net_margin_ttm > 0:
                business_points += 0.70
                business_evidence.append("Net margin is positive")
            elif trends.net_margin_ttm > -0.10:
                business_points += 0.35
                business_evidence.append("Net margin remains negative but is contained")
            else:
                business_evidence.append("Net margin is materially negative")

        if profitability.return_on_equity is not None:
            business_checks += 1
            if profitability.return_on_equity >= 0.15:
                business_points += 1.0
                business_evidence.append("Return on equity is strong")
            elif profitability.return_on_equity > 0:
                business_points += 0.60
                business_evidence.append("Return on equity is positive")
            else:
                business_evidence.append("Return on equity is negative")

        business_score = (
            round(100 * business_points / business_checks, 1)
            if business_checks else None
        )

        # -------------------------
        # 2) FINANCIAL QUALITY
        # -------------------------
        financial_points = 0.0
        financial_checks = 0
        financial_evidence: list[str] = []

        if health.current_ratio is not None:
            financial_checks += 1
            if health.current_ratio >= 1.5:
                financial_points += 1.0
                financial_evidence.append("Liquidity is strong")
            elif health.current_ratio >= 1.0:
                financial_points += 0.70
                financial_evidence.append("Liquidity is adequate")
            else:
                financial_evidence.append("Liquidity is weak")

        if trends.net_cash is not None:
            financial_checks += 1
            if trends.net_cash > 0:
                financial_points += 1.0
                financial_evidence.append("Balance sheet is in net cash")
            else:
                financial_evidence.append("Balance sheet is in net debt")

        if trends.debt_to_cash is not None:
            financial_checks += 1
            if trends.debt_to_cash <= 0.75:
                financial_points += 1.0
                financial_evidence.append("Cash coverage of debt is strong")
            elif trends.debt_to_cash <= 1.0:
                financial_points += 0.75
                financial_evidence.append("Cash broadly covers debt")
            elif trends.debt_to_cash <= 1.5:
                financial_points += 0.40
                financial_evidence.append("Debt is moderately above cash")
            else:
                financial_evidence.append("Debt materially exceeds cash")

        if health.operating_cash_flow is not None:
            financial_checks += 1
            if health.operating_cash_flow > 0:
                financial_points += 1.0
                financial_evidence.append("Operating cash flow is positive")
            else:
                financial_evidence.append("Operating cash flow is negative")

        if health.free_cash_flow is not None:
            financial_checks += 1
            if health.free_cash_flow > 0:
                financial_points += 1.0
                financial_evidence.append("Free cash flow is positive")
            elif trends.free_cash_flow_yoy is not None and trends.free_cash_flow_yoy > 0:
                financial_points += 0.45
                financial_evidence.append("Free cash flow remains negative but is improving")
            else:
                financial_evidence.append("Free cash flow is negative")

        financial_score = (
            round(100 * financial_points / financial_checks, 1)
            if financial_checks else None
        )

        # -------------------------
        # 3) GROWTH QUALITY
        # -------------------------
        growth_points = 0.0
        growth_checks = 0
        growth_evidence: list[str] = []

        if trends.revenue_yoy is not None:
            growth_checks += 1
            if trends.revenue_yoy >= 0.20:
                growth_points += 1.0
                growth_evidence.append("Revenue growth is strong")
            elif trends.revenue_yoy > 0:
                growth_points += 0.65
                growth_evidence.append("Revenue growth is positive")
            else:
                growth_evidence.append("Revenue growth is negative")

        if trends.revenue_cagr_3y is not None:
            growth_checks += 1
            if trends.revenue_cagr_3y >= 0.15:
                growth_points += 1.0
                growth_evidence.append("Three-year revenue CAGR is strong")
            elif trends.revenue_cagr_3y > 0:
                growth_points += 0.65
                growth_evidence.append("Three-year revenue CAGR is positive")
            else:
                growth_evidence.append("Three-year revenue CAGR is negative")

        if trends.operating_income_yoy is not None:
            growth_checks += 1
            if trends.operating_income_yoy >= 0.20:
                growth_points += 1.0
                growth_evidence.append("Operating income is improving strongly")
            elif trends.operating_income_yoy > 0:
                growth_points += 0.70
                growth_evidence.append("Operating income is improving")
            else:
                growth_evidence.append("Operating income is deteriorating")

        if trends.net_income_yoy is not None:
            growth_checks += 1
            if trends.net_income_yoy >= 0.20:
                growth_points += 1.0
                growth_evidence.append("Net income is improving strongly")
            elif trends.net_income_yoy > 0:
                growth_points += 0.70
                growth_evidence.append("Net income is improving")
            else:
                growth_evidence.append("Net income is deteriorating")

        if trends.free_cash_flow_yoy is not None:
            growth_checks += 1
            if trends.free_cash_flow_yoy >= 0.20:
                growth_points += 1.0
                growth_evidence.append("Free cash flow is improving strongly")
            elif trends.free_cash_flow_yoy > 0:
                growth_points += 0.70
                growth_evidence.append("Free cash flow is improving")
            else:
                growth_evidence.append("Free cash flow is deteriorating")

        growth_score = (
            round(100 * growth_points / growth_checks, 1)
            if growth_checks else None
        )

        # -------------------------
        # 4) VALUATION CONTEXT
        # -------------------------
        valuation_points = 0.0
        valuation_checks = 0
        valuation_evidence: list[str] = []

        currency_mismatch = bool(data_quality.currency_mismatch)

        # P/E is dimensionless and can still be used when supplied directly.
        if valuation.forward_pe is not None and valuation.forward_pe > 0:
            valuation_checks += 1
            if valuation.forward_pe <= 15:
                valuation_points += 1.0
                valuation_evidence.append("Forward P/E is attractive")
            elif valuation.forward_pe <= 25:
                valuation_points += 0.75
                valuation_evidence.append("Forward P/E is reasonable")
            elif valuation.forward_pe <= 40:
                valuation_points += 0.45
                valuation_evidence.append("Forward P/E is elevated")
            else:
                valuation_evidence.append("Forward P/E is expensive")

        if valuation.price_to_book is not None and valuation.price_to_book > 0:
            valuation_checks += 1
            if valuation.price_to_book <= 2:
                valuation_points += 1.0
                valuation_evidence.append("Price-to-book is attractive")
            elif valuation.price_to_book <= 5:
                valuation_points += 0.65
                valuation_evidence.append("Price-to-book is reasonable")
            elif valuation.price_to_book <= 10:
                valuation_points += 0.35
                valuation_evidence.append("Price-to-book is elevated")
            else:
                valuation_evidence.append("Price-to-book is very high")

        if (
            not currency_mismatch
            and valuation.price_to_sales is not None
            and valuation.price_to_sales > 0
        ):
            valuation_checks += 1
            if valuation.price_to_sales <= 2:
                valuation_points += 1.0
                valuation_evidence.append("Price-to-sales is attractive")
            elif valuation.price_to_sales <= 5:
                valuation_points += 0.65
                valuation_evidence.append("Price-to-sales is reasonable")
            elif valuation.price_to_sales <= 10:
                valuation_points += 0.35
                valuation_evidence.append("Price-to-sales is elevated")
            else:
                valuation_evidence.append("Price-to-sales is expensive")

        if (
            not currency_mismatch
            and valuation.enterprise_to_revenue is not None
            and valuation.enterprise_to_revenue > 0
        ):
            valuation_checks += 1
            if valuation.enterprise_to_revenue <= 2:
                valuation_points += 1.0
                valuation_evidence.append("EV/Revenue is attractive")
            elif valuation.enterprise_to_revenue <= 5:
                valuation_points += 0.65
                valuation_evidence.append("EV/Revenue is reasonable")
            elif valuation.enterprise_to_revenue <= 10:
                valuation_points += 0.35
                valuation_evidence.append("EV/Revenue is elevated")
            else:
                valuation_evidence.append("EV/Revenue is expensive")

        # EV-based ratios are ignored while market and financial currencies differ.
        if not currency_mismatch and valuation.enterprise_to_ebitda is not None:
            valuation_checks += 1
            if valuation.enterprise_to_ebitda <= 0:
                valuation_evidence.append(
                    "EV/EBITDA is not meaningful because EBITDA is non-positive"
                )
            elif valuation.enterprise_to_ebitda <= 12:
                valuation_points += 1.0
                valuation_evidence.append("EV/EBITDA is attractive")
            elif valuation.enterprise_to_ebitda <= 20:
                valuation_points += 0.65
                valuation_evidence.append("EV/EBITDA is reasonable")
            elif valuation.enterprise_to_ebitda <= 30:
                valuation_points += 0.35
                valuation_evidence.append("EV/EBITDA is elevated")
            else:
                valuation_evidence.append("EV/EBITDA is expensive")

        if currency_mismatch:
            valuation_evidence.append(
                "Cross-currency sales and enterprise-value multiples are excluded "
                "until explicit FX normalization is available"
            )

        valuation_score = (
            round(100 * valuation_points / valuation_checks, 1)
            if valuation_checks else None
        )
        valuation_state = self._valuation_state(valuation_score, valuation_checks)

        # -------------------------
        # COMPOSITE QUALITY
        # -------------------------
        weighted_dimensions = [
            (business_score, 0.35),
            (financial_score, 0.35),
            (growth_score, 0.30),
        ]

        if not currency_mismatch:
            weighted_dimensions.append((valuation_score, 0.15))
        available = [(score, weight) for score, weight in weighted_dimensions if score is not None]

        if available:
            weight_total = sum(weight for _, weight in available)
            quality_score = round(
                sum(score * weight for score, weight in available) / weight_total,
                1,
            )
        else:
            quality_score = None

        if quality_score is None:
            quality_regime = "UNKNOWN"
        elif quality_score >= 80:
            quality_regime = "HIGH_QUALITY"
        elif quality_score >= 65:
            quality_regime = "GOOD"
        elif quality_score >= 50:
            quality_regime = "IMPROVING"
        elif quality_score >= 35:
            quality_regime = "FRAGILE"
        else:
            quality_regime = "WEAK"

        dimension_count = len(available)
        if data_quality.completeness_score >= 80 and dimension_count >= 3:
            confidence = "HIGH"
        elif data_quality.completeness_score >= 60 and dimension_count >= 2:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        if currency_mismatch and confidence == "HIGH":
            confidence = "MEDIUM"

        return FundamentalQualityIntelligence(
            business_quality=FundamentalQualityDimension(
                state=self._quality_state(business_score),
                score=business_score,
                confidence=self._intel_confidence(business_checks),
                evidence=business_evidence,
            ),
            financial_quality=FundamentalQualityDimension(
                state=self._quality_state(financial_score),
                score=financial_score,
                confidence=self._intel_confidence(financial_checks),
                evidence=financial_evidence,
            ),
            growth_quality=FundamentalQualityDimension(
                state=self._quality_state(growth_score),
                score=growth_score,
                confidence=self._intel_confidence(growth_checks),
                evidence=growth_evidence,
            ),
            valuation_context=FundamentalQualityDimension(
                state=valuation_state,
                score=valuation_score,
                confidence=(
                    "LOW"
                    if currency_mismatch or valuation_checks < 2
                    else self._intel_confidence(valuation_checks)
                ),
                evidence=valuation_evidence,
            ),
            quality_score=quality_score,
            quality_regime=quality_regime,
            valuation_state=valuation_state,
            confidence=confidence,
        )

    def _build_data_quality(
        self,
        valuation: ValuationMetrics,
        profitability: ProfitabilityMetrics,
        growth: GrowthMetrics,
        health: FinancialHealthMetrics,
        statements: FundamentalStatements,
        profile: CompanyProfile,
    ) -> FundamentalDataQuality:
        """Quantify coverage without treating unavailable fields as zero."""
        snapshot_values = [
            valuation.market_cap,
            valuation.enterprise_value,
            valuation.forward_pe,
            valuation.price_to_book,
            valuation.price_to_sales,
            profitability.gross_margin,
            profitability.operating_margin,
            profitability.net_margin,
            profitability.return_on_assets,
            profitability.return_on_equity,
            growth.revenue_growth,
            growth.earnings_growth,
            health.total_revenue,
            health.ebitda,
            health.net_income,
            health.operating_cash_flow,
            health.free_cash_flow,
            health.total_cash,
            health.total_debt,
            health.current_ratio,
        ]
        available = sum(value is not None for value in snapshot_values)
        total = len(snapshot_values)
        snapshot_score = (available / total * 100.0) if total else 0.0

        statement_checks = [
            bool(statements.annual_income),
            bool(statements.quarterly_income),
            bool(statements.annual_balance_sheet),
            bool(statements.quarterly_balance_sheet),
            bool(statements.annual_cash_flow),
            bool(statements.quarterly_cash_flow),
            statements.ttm_income is not None,
            statements.ttm_cash_flow is not None,
            statements.latest_balance_sheet is not None,
        ]
        statement_score = sum(statement_checks) / len(statement_checks) * 100.0

        completeness = round(0.55 * snapshot_score + 0.45 * statement_score, 2)
        if completeness >= 90:
            grade = "Excellent"
        elif completeness >= 75:
            grade = "Good"
        elif completeness >= 60:
            grade = "Fair"
        elif completeness >= 40:
            grade = "Limited"
        else:
            grade = "Poor"

        warnings: list[str] = []

        market_currency = profile.market_currency or profile.currency
        financial_currency = profile.financial_currency or profile.currency
        currency_mismatch = bool(
            market_currency
            and financial_currency
            and market_currency.upper() != financial_currency.upper()
        )

        if currency_mismatch:
            warnings.append(
                "Market currency and financial-statement currency differ; "
                "cross-currency valuation fallbacks are disabled until FX normalization is available"
            )

        if not statements.quarterly_income:
            warnings.append("Quarterly income statement history is unavailable")
        if not statements.quarterly_cash_flow:
            warnings.append("Quarterly cash-flow history is unavailable")
        if statements.latest_balance_sheet is None:
            warnings.append("Balance-sheet history is unavailable")
        if completeness < 60:
            warnings.append("Provider coverage is insufficient for high-confidence fundamental interpretation")

        return FundamentalDataQuality(
            provider=self.provider,
            completeness_score=completeness,
            completeness_grade=grade,
            snapshot_fields_available=available,
            snapshot_fields_total=total,
            annual_income_periods=len(statements.annual_income),
            quarterly_income_periods=len(statements.quarterly_income),
            annual_balance_periods=len(statements.annual_balance_sheet),
            quarterly_balance_periods=len(statements.quarterly_balance_sheet),
            annual_cash_flow_periods=len(statements.annual_cash_flow),
            quarterly_cash_flow_periods=len(statements.quarterly_cash_flow),
            has_ttm_income=statements.ttm_income is not None,
            has_ttm_cash_flow=statements.ttm_cash_flow is not None,
            has_latest_balance_sheet=statements.latest_balance_sheet is not None,
            market_currency=market_currency,
            financial_currency=financial_currency,
            currency_mismatch=currency_mismatch,
            warnings=warnings,
        )

    def get_fundamentals(self, symbol: str) -> FundamentalAnalysisResult:
        """Retrieve normalized fundamentals for a market symbol."""

        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            raise ValueError("Symbol cannot be empty.")

        ticker = yf.Ticker(normalized_symbol)

        try:
            info = ticker.info or {}
        except Exception:
            info = {}

        market_price = self._to_float(
            info.get("currentPrice")
            or info.get("regularMarketPrice")
            or info.get("previousClose")
        )

        market_currency = info.get("currency")
        financial_currency = info.get("financialCurrency") or market_currency

        profile = CompanyProfile(
            symbol=normalized_symbol,
            company_name=info.get("longName") or info.get("shortName"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            country=info.get("country"),
            currency=market_currency,
            market_currency=market_currency,
            financial_currency=financial_currency,
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
            shares_outstanding=self._to_float(
                info.get("sharesOutstanding")
            ),
            float_shares=self._to_float(info.get("floatShares")),
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

        currency = profile.financial_currency or profile.currency

        annual_income = self._income_periods(
            self._safe_statement(ticker, "income_stmt"),
            "annual",
            currency,
        )
        quarterly_income = self._income_periods(
            self._safe_statement(ticker, "quarterly_income_stmt"),
            "quarterly",
            currency,
        )

        annual_balance_sheet = self._balance_periods(
            self._safe_statement(ticker, "balance_sheet"),
            "annual",
            currency,
        )
        quarterly_balance_sheet = self._balance_periods(
            self._safe_statement(ticker, "quarterly_balance_sheet"),
            "quarterly",
            currency,
        )

        annual_cash_flow = self._cash_flow_periods(
            self._safe_statement(ticker, "cashflow"),
            "annual",
            currency,
        )
        quarterly_cash_flow = self._cash_flow_periods(
            self._safe_statement(ticker, "quarterly_cashflow"),
            "quarterly",
            currency,
        )

        statements = FundamentalStatements(
            annual_income=annual_income,
            quarterly_income=quarterly_income,
            ttm_income=self._build_ttm_income(
                quarterly_income,
                currency,
            ),
            annual_balance_sheet=annual_balance_sheet,
            quarterly_balance_sheet=quarterly_balance_sheet,
            latest_balance_sheet=(
                quarterly_balance_sheet[0]
                if quarterly_balance_sheet
                else annual_balance_sheet[0]
                if annual_balance_sheet
                else None
            ),
            annual_cash_flow=annual_cash_flow,
            quarterly_cash_flow=quarterly_cash_flow,
            ttm_cash_flow=self._build_ttm_cash_flow(
                quarterly_cash_flow,
                currency,
            ),
        )

        (
            valuation,
            profitability,
            growth,
            financial_health,
        ) = self._normalize_from_statements(
            valuation=valuation,
            profitability=profitability,
            growth=growth,
            health=financial_health,
            statements=statements,
            market_price=market_price,
            market_currency=profile.market_currency or profile.currency,
            financial_currency=profile.financial_currency or profile.currency,
        )

        trends = self._build_trends(statements, financial_health)
        statement_intelligence = self._build_statement_intelligence(
            statements,
            trends,
            financial_health,
        )
        data_quality = self._build_data_quality(
            valuation,
            profitability,
            growth,
            financial_health,
            statements,
            profile,
        )
        quality_intelligence = self._build_quality_intelligence(
            valuation=valuation,
            profitability=profitability,
            growth=growth,
            health=financial_health,
            trends=trends,
            statements=statements,
            data_quality=data_quality,
        )

        return FundamentalAnalysisResult(
            symbol=normalized_symbol,
            profile=profile,
            valuation=valuation,
            profitability=profitability,
            growth=growth,
            financial_health=financial_health,
            statements=statements,
            trends=trends,
            data_quality=data_quality,
            statement_intelligence=statement_intelligence,
            quality_intelligence=quality_intelligence,
            data_source=self.provider,
            engine_version="DE-FA-004.0",
        )
