"""
Fundamental Analysis Service — DE-FA-004.0

Orchestrates fundamental data collection and produces
QMI-level interpretations.
"""

from app.fundamental.collector import FundamentalCollector
from app.fundamental.business_momentum import AdaptiveBusinessMomentumEngine
from app.fundamental.architecture import FundamentalArchitectureService
from app.fundamental.data_foundation import FinancialDataFoundationService
from app.fundamental.statement_history import FinancialStatementHistoryService
from app.fundamental.statement_provider_adapter import StatementProviderAdapter
from app.fundamental.growth_trend_engine import FundamentalGrowthTrendEngine
from app.fundamental.profitability_quality_engine import FundamentalProfitabilityQualityEngine
from app.fundamental.financial_health_engine import FundamentalFinancialHealthEngine
from app.fundamental.cash_flow_intelligence_engine import FundamentalCashFlowIntelligenceEngine
from app.fundamental.valuation_intelligence_engine import FundamentalValuationIntelligenceEngine
from app.fundamental.expectations_intelligence_engine import FundamentalExpectationsIntelligenceEngine
from app.fundamental.company_intelligence_engine import FundamentalCompanyIntelligenceEngine
from app.fundamental.fundamental_decision_engine import FundamentalDecisionEngine
from app.fundamental.schemas import (
    FundamentalAnalysisResult,
    FundamentalDecision,
    FundamentalInsight,
)


class FundamentalService:
    """Orchestrate the QMI fundamental analysis workflow."""

    def __init__(
        self,
        collector: FundamentalCollector | None = None,
    ) -> None:
        self.collector = collector or FundamentalCollector()
        self.business_momentum_engine = AdaptiveBusinessMomentumEngine()
        self.architecture_service = FundamentalArchitectureService()
        self.data_foundation_service = FinancialDataFoundationService()
        self.statement_history_service = FinancialStatementHistoryService()
        self.statement_provider_adapter = StatementProviderAdapter()
        self.growth_trend_engine = FundamentalGrowthTrendEngine()
        self.profitability_quality_engine = FundamentalProfitabilityQualityEngine()
        self.financial_health_engine = FundamentalFinancialHealthEngine()
        self.cash_flow_intelligence_engine = FundamentalCashFlowIntelligenceEngine()
        self.valuation_intelligence_engine = FundamentalValuationIntelligenceEngine()
        self.expectations_intelligence_engine = FundamentalExpectationsIntelligenceEngine()
        self.company_intelligence_engine = FundamentalCompanyIntelligenceEngine()
        self.fundamental_decision_engine = FundamentalDecisionEngine()

    @staticmethod
    def _get_company_specific_momentum(symbol: str) -> dict:
        """
        Load optional company-specific business drivers.

        Missing or unavailable company intelligence never raises a hard failure
        in the universal Fundamental Engine. The adaptive engine simply excludes
        those drivers and renormalizes the remaining weights.
        """
        normalized = symbol.strip().upper()

        if normalized != "NIO":
            return {}

        try:
            from app.company_intelligence.nio.service import NioDeliveryService

            nio_response = NioDeliveryService().analyze()
            payload = (
                nio_response.model_dump()
                if hasattr(nio_response, "model_dump")
                else nio_response
            )

            momentum = (payload or {}).get("delivery_momentum")
            if not momentum:
                return {}

            return {"nio_delivery_momentum": momentum}

        except Exception:
            # Company-specific enrichment is optional by design.
            # Fundamental analysis must remain operational for every ticker.
            return {}

    def analyze(self, symbol: str) -> FundamentalInsight:
        """
        Generate a normalized and interpreted fundamental analysis.
        """

        data = self.collector.get_fundamentals(symbol)

        company_specific = self._get_company_specific_momentum(symbol)
        business_momentum_payload = self.business_momentum_engine.analyze(
            data=data,
            company_specific=company_specific,
        )

        data_foundation_payload = self.data_foundation_service.audit(
            symbol=symbol,
            data=data,
        )

        statement_provider_payload = self.statement_provider_adapter.adapt(
            data=data,
        )
        statement_history_payload = self.statement_history_service.normalize(
            symbol=symbol,
            annual=statement_provider_payload["annual"],
            quarterly=statement_provider_payload["quarterly"],
            provider=statement_provider_payload["provider"],
        )
        statement_history_payload["provider_adapter"] = {
            "engine_id": statement_provider_payload["engine_id"],
            "version": statement_provider_payload["version"],
            "contracts": statement_provider_payload["contracts"],
            "ttm": statement_provider_payload["ttm"],
            "latest_balance_sheet": statement_provider_payload["latest_balance_sheet"],
            "source_quality": statement_provider_payload["source_quality"],
        }

        growth_trend_payload = self.growth_trend_engine.analyze(
            statement_history=statement_history_payload,
        )

        profitability_quality_payload = self.profitability_quality_engine.analyze(
            data=data,
            statement_history=statement_history_payload,
            growth_trend=growth_trend_payload,
        )

        financial_health_payload = self.financial_health_engine.analyze(
            data=data,
            statement_history=statement_history_payload,
        )

        cash_flow_intelligence_payload = self.cash_flow_intelligence_engine.analyze(
            data=data,
            statement_history=statement_history_payload,
            profitability_quality=profitability_quality_payload,
        )

        valuation_intelligence_payload = self.valuation_intelligence_engine.analyze(
            data=data,
            growth_trend=growth_trend_payload,
            profitability_quality=profitability_quality_payload,
            cash_flow_intelligence=cash_flow_intelligence_payload,
        )

        expectations_intelligence_payload = self.expectations_intelligence_engine.analyze(
            data=data,
            growth_trend=growth_trend_payload,
            profitability_quality=profitability_quality_payload,
            cash_flow_intelligence=cash_flow_intelligence_payload,
            valuation_intelligence=valuation_intelligence_payload,
        )

        architecture_payload = self.architecture_service.build(
            data=data,
            company_specific=company_specific,
        )

        score = self._calculate_score(data)
        rating = self._get_rating(score)

        strengths = self._detect_strengths(data)
        weaknesses = self._detect_weaknesses(data)
        warnings = self._detect_warnings(data)
        data.fundamental_score = score

        company_intelligence_payload = self.company_intelligence_engine.analyze(
            data=data,
        )

        decision = self.fundamental_decision_engine.analyze(
            data=data,
            growth_trend=growth_trend_payload,
            profitability_quality=profitability_quality_payload,
            financial_health=financial_health_payload,
            cash_flow_intelligence=cash_flow_intelligence_payload,
            valuation_intelligence=valuation_intelligence_payload,
            expectations_intelligence=expectations_intelligence_payload,
            company_intelligence=company_intelligence_payload,
            business_momentum=business_momentum_payload,
            legacy_score=score,
        )

        return FundamentalInsight(
            data=data,
            score=score,
            rating=rating,
            strengths=strengths,
            weaknesses=weaknesses,
            warnings=warnings,
            decision=decision,
            business_momentum=business_momentum_payload,
            architecture=architecture_payload,
            data_foundation=data_foundation_payload,
            statement_history=statement_history_payload,
            growth_trend=growth_trend_payload,
            profitability_quality=profitability_quality_payload,
            financial_health_intelligence=financial_health_payload,
            cash_flow_intelligence=cash_flow_intelligence_payload,
            valuation_intelligence=valuation_intelligence_payload,
            expectations_intelligence=expectations_intelligence_payload,
            company_intelligence=company_intelligence_payload,
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

        # DE-FA-004.0 — normalized statement-derived confirmation. These adjustments
        # are deliberately smaller than the snapshot rules to avoid double-counting.
        trends = data.trends

        if trends.revenue_cagr_3y is not None:
            if trends.revenue_cagr_3y >= 0.15:
                score += 4
            elif trends.revenue_cagr_3y < 0:
                score -= 4

        if trends.free_cash_flow_margin_ttm is not None:
            if trends.free_cash_flow_margin_ttm >= 0.10:
                score += 4
            elif trends.free_cash_flow_margin_ttm < 0:
                score -= 4

        if trends.net_cash is not None:
            if trends.net_cash > 0:
                score += 3
            elif trends.net_cash < 0:
                score -= 3

        # Low provider coverage caps confidence in the numerical score.
        if data.data_quality.completeness_score < 40:
            score = min(score, 60.0)

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
    def _build_decision(
        data: FundamentalAnalysisResult,
        legacy_score: float,
        strengths: list[str],
        weaknesses: list[str],
        warnings: list[str],
    ) -> FundamentalDecision:
        """Consolidate quality, regime and legacy score into a fundamental stance."""

        quality = data.quality_intelligence
        statement = data.statement_intelligence

        quality_score = quality.quality_score
        regime_score = statement.regime_score

        weighted: list[tuple[float, float]] = []

        if quality_score is not None:
            weighted.append((quality_score, 0.45))

        if regime_score is not None:
            weighted.append((regime_score, 0.35))

        weighted.append((legacy_score, 0.20))

        total_weight = sum(weight for _, weight in weighted)
        decision_score = round(
            sum(score * weight for score, weight in weighted) / total_weight,
            1,
        )

        if decision_score >= 80:
            stance = "VERY_POSITIVE"
        elif decision_score >= 68:
            stance = "POSITIVE"
        elif decision_score >= 55:
            stance = "CONSTRUCTIVE"
        elif decision_score >= 42:
            stance = "CAUTIOUS"
        else:
            stance = "NEGATIVE"

        if (
            statement.fundamental_regime == "RECOVERY"
            and stance in {"CAUTIOUS", "CONSTRUCTIVE"}
            and quality_score is not None
            and quality_score >= 65
        ):
            stance = "CONSTRUCTIVE"

        if (
            statement.profitability_state == "LOSS_MAKING"
            and stance == "VERY_POSITIVE"
        ):
            stance = "POSITIVE"

        confidence_inputs = [
            quality.confidence,
            statement.confidence,
            data.data_quality.completeness_grade.upper(),
        ]

        high_votes = sum(
            item in {"HIGH", "GOOD", "EXCELLENT"}
            for item in confidence_inputs
        )

        if high_votes >= 2 and data.data_quality.completeness_score >= 75:
            conviction = "HIGH"
        elif data.data_quality.completeness_score >= 60:
            conviction = "MEDIUM"
        else:
            conviction = "LOW"

        thesis: list[str] = []
        catalysts: list[str] = []
        risks: list[str] = []

        if statement.revenue_trend == "IMPROVING":
            thesis.append("Revenue trend is improving")

        if statement.margin_trend == "IMPROVING":
            thesis.append("Margins are improving")

        if statement.balance_sheet_state == "STRONG":
            thesis.append("Balance sheet is strong")

        if quality.growth_quality.state == "STRONG":
            catalysts.append("Growth quality is strong")

        if statement.cash_flow_state == "RECOVERING":
            catalysts.append("Cash flow is recovering")

        if quality.financial_quality.state in {"GOOD", "STRONG"}:
            catalysts.append("Financial quality is supportive")

        if statement.profitability_state == "LOSS_MAKING":
            risks.append("Business remains loss-making")

        if quality.business_quality.state in {"WEAK", "POOR"}:
            risks.append("Business quality remains weak")

        if quality.valuation_context.state in {"ELEVATED", "EXPENSIVE"}:
            risks.append("Valuation context is elevated")

        if data.data_quality.currency_mismatch:
            risks.append("Cross-currency valuation comparability is limited")

        for item in weaknesses:
            if item not in risks:
                risks.append(item)

        return FundamentalDecision(
            stance=stance,
            decision_score=decision_score,
            conviction=conviction,
            quality_score=quality_score,
            regime_score=regime_score,
            legacy_score=legacy_score,
            thesis=thesis,
            catalysts=catalysts,
            risks=risks,
        )

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

        if (
            data.trends.revenue_cagr_3y is not None
            and data.trends.revenue_cagr_3y >= 0.15
        ):
            strengths.append("Strong three-year revenue CAGR")

        if (
            data.trends.free_cash_flow_margin_ttm is not None
            and data.trends.free_cash_flow_margin_ttm >= 0.10
        ):
            strengths.append("Healthy TTM free-cash-flow margin")

        if data.trends.net_cash is not None and data.trends.net_cash > 0:
            strengths.append("Net cash balance sheet")

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

        if (
            data.trends.revenue_cagr_3y is not None
            and data.trends.revenue_cagr_3y < 0
        ):
            weaknesses.append("Negative three-year revenue CAGR")

        if (
            data.trends.free_cash_flow_margin_ttm is not None
            and data.trends.free_cash_flow_margin_ttm < 0
        ):
            weaknesses.append("Negative TTM free-cash-flow margin")

        if data.trends.net_cash is not None and data.trends.net_cash < 0:
            weaknesses.append("Net debt balance sheet")

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

        if data.data_quality.completeness_score < 60:
            warnings.append(
                f"Fundamental dataset coverage is {data.data_quality.completeness_grade.lower()} "
                f"({data.data_quality.completeness_score:.1f}%)"
            )

        for warning in data.data_quality.warnings:
            if warning not in warnings:
                warnings.append(warning)

        return warnings