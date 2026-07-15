"""
Fundamental Analysis Service

Orchestrates fundamental data collection and produces
QMI-level interpretations.
"""

from app.fundamental.collector import FundamentalCollector
from app.fundamental.schemas import (
    FundamentalAnalysisResult,
    FundamentalInsight,
)


class FundamentalService:
    """Orchestrate the QMI fundamental analysis workflow."""

    def __init__(
        self,
        collector: FundamentalCollector | None = None,
    ) -> None:
        self.collector = collector or FundamentalCollector()

    def analyze(self, symbol: str) -> FundamentalInsight:
        """
        Generate a normalized and interpreted fundamental analysis.
        """

        data = self.collector.get_fundamentals(symbol)

        score = self._calculate_score(data)
        rating = self._get_rating(score)

        strengths = self._detect_strengths(data)
        weaknesses = self._detect_weaknesses(data)
        warnings = self._detect_warnings(data)

        data.fundamental_score = score

        return FundamentalInsight(
            data=data,
            score=score,
            rating=rating,
            strengths=strengths,
            weaknesses=weaknesses,
            warnings=warnings,
        )

    def _calculate_score(
        self,
        data: FundamentalAnalysisResult,
    ) -> float:
        """
        Calculate the initial QMI Fundamental Score.

        This first version uses a simple rule-based model.
        """

        score = 50.0

        profitability = data.profitability
        growth = data.growth
        health = data.financial_health
        valuation = data.valuation

        if profitability.net_margin is not None:
            if profitability.net_margin > 0.15:
                score += 10
            elif profitability.net_margin > 0:
                score += 5
            else:
                score -= 10

        if profitability.return_on_equity is not None:
            if profitability.return_on_equity > 0.20:
                score += 10
            elif profitability.return_on_equity > 0:
                score += 5
            else:
                score -= 8

        if growth.revenue_growth is not None:
            if growth.revenue_growth > 0.20:
                score += 10
            elif growth.revenue_growth > 0:
                score += 5
            else:
                score -= 5

        if health.current_ratio is not None:
            if health.current_ratio >= 1.5:
                score += 8
            elif health.current_ratio >= 1.0:
                score += 3
            else:
                score -= 8

        if health.free_cash_flow is not None:
            if health.free_cash_flow > 0:
                score += 8
            else:
                score -= 8

        if valuation.forward_pe is not None:
            if 0 < valuation.forward_pe <= 20:
                score += 7
            elif valuation.forward_pe > 40:
                score -= 5

        return round(max(0.0, min(score, 100.0)), 2)

    @staticmethod
    def _get_rating(score: float) -> str:
        if score >= 85:
            return "Excellent"
        if score >= 70:
            return "Good"
        if score >= 55:
            return "Neutral"
        if score >= 40:
            return "Weak"
        return "Poor"

    @staticmethod
    def _detect_strengths(
        data: FundamentalAnalysisResult,
    ) -> list[str]:
        strengths: list[str] = []

        if (
            data.growth.revenue_growth is not None
            and data.growth.revenue_growth > 0.20
        ):
            strengths.append("Strong revenue growth")

        if (
            data.profitability.net_margin is not None
            and data.profitability.net_margin > 0.10
        ):
            strengths.append("Healthy net margin")

        if (
            data.profitability.return_on_equity is not None
            and data.profitability.return_on_equity > 0.15
        ):
            strengths.append("Strong return on equity")

        if (
            data.financial_health.current_ratio is not None
            and data.financial_health.current_ratio >= 1.5
        ):
            strengths.append("Strong short-term liquidity")

        if (
            data.financial_health.free_cash_flow is not None
            and data.financial_health.free_cash_flow > 0
        ):
            strengths.append("Positive free cash flow")

        return strengths

    @staticmethod
    def _detect_weaknesses(
        data: FundamentalAnalysisResult,
    ) -> list[str]:
        weaknesses: list[str] = []

        if (
            data.profitability.net_margin is not None
            and data.profitability.net_margin < 0
        ):
            weaknesses.append("Negative net margin")

        if (
            data.profitability.return_on_equity is not None
            and data.profitability.return_on_equity < 0
        ):
            weaknesses.append("Negative return on equity")

        if (
            data.financial_health.current_ratio is not None
            and data.financial_health.current_ratio < 1
        ):
            weaknesses.append("Weak short-term liquidity")

        if (
            data.financial_health.free_cash_flow is not None
            and data.financial_health.free_cash_flow < 0
        ):
            weaknesses.append("Negative free cash flow")

        if (
            data.valuation.forward_pe is not None
            and data.valuation.forward_pe > 40
        ):
            weaknesses.append("High forward valuation")

        return weaknesses

    @staticmethod
    def _detect_warnings(
        data: FundamentalAnalysisResult,
    ) -> list[str]:
        warnings: list[str] = []

        missing_metrics = 0

        key_metrics = [
            data.valuation.forward_pe,
            data.profitability.net_margin,
            data.profitability.return_on_equity,
            data.growth.revenue_growth,
            data.financial_health.current_ratio,
            data.financial_health.free_cash_flow,
        ]

        for metric in key_metrics:
            if metric is None:
                missing_metrics += 1

        if missing_metrics >= 3:
            warnings.append(
                "Fundamental score is based on incomplete provider data"
            )

        if data.financial_health.total_debt is None:
            warnings.append("Total debt data is unavailable")

        return warnings