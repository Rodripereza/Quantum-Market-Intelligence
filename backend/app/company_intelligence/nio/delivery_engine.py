from __future__ import annotations
from statistics import mean
from app.company_intelligence.nio.schemas import (
    NioDeliveryIntelligence,
    NioDeliverySnapshot,
    NioMonthlyDeliveryRecord,
)

class NioDeliveryIntelligenceEngine:
    def analyze(self, records: list[NioMonthlyDeliveryRecord]):
        if not records:
            raise ValueError("NIO delivery history is empty.")

        latest = records[-1]
        totals = [r.total for r in records]
        avg3 = mean(totals[-3:])
        avg6 = mean(totals[-6:]) if len(totals) >= 6 else mean(totals)
        run_rate = avg3 * 12.0

        score = 50.0
        evidence: list[str] = []
        risks: list[str] = []

        if latest.yoy_pct is not None:
            if latest.yoy_pct >= 50:
                score += 20
                evidence.append("Latest monthly deliveries show very strong year-over-year growth.")
            elif latest.yoy_pct >= 20:
                score += 12
                evidence.append("Latest monthly deliveries show strong year-over-year growth.")
            elif latest.yoy_pct > 0:
                score += 5
                evidence.append("Latest monthly deliveries remain positive year over year.")
            else:
                score -= 15
                risks.append("Latest monthly deliveries are below the prior-year level.")

        if avg3 >= avg6 * 1.05:
            score += 12
            evidence.append("Three-month average deliveries are above the six-month average.")
        elif avg3 < avg6 * 0.95:
            score -= 10
            risks.append("Three-month average deliveries are below the six-month average.")
        else:
            evidence.append("Three-month delivery momentum is broadly stable versus six months.")

        if run_rate >= 450000:
            score += 12
            evidence.append("Recent delivery run-rate exceeds 450k vehicles annualized.")
        elif run_rate >= 400000:
            score += 8
            evidence.append("Recent delivery run-rate exceeds 400k vehicles annualized.")
        elif run_rate < 300000:
            score -= 10
            risks.append("Recent annualized delivery run-rate is below 300k vehicles.")

        if latest.mom_pct is not None and latest.mom_pct < -10:
            score -= 4
            risks.append("Latest month declined by more than 10% sequentially.")
        elif latest.mom_pct is not None and latest.mom_pct > 10:
            score += 4
            evidence.append("Latest month accelerated by more than 10% sequentially.")

        latest_brand_total = sum(latest.brands.values()) if latest.brands else 0
        brand_mix = {}
        if latest_brand_total > 0:
            brand_mix = {
                brand: round(value / latest_brand_total * 100.0, 1)
                for brand, value in latest.brands.items()
            }

        non_core = brand_mix.get("ONVO", 0.0) + brand_mix.get("FIREFLY", 0.0)
        if non_core >= 40:
            score += 6
            evidence.append("ONVO and FIREFLY provide meaningful brand diversification.")
            diversification = "EXPANDING"
        elif non_core >= 25:
            score += 3
            evidence.append("Multi-brand contribution is established.")
            diversification = "ESTABLISHED"
        elif latest.brands:
            diversification = "CORE_NIO_DOMINANT"
        else:
            diversification = "LIMITED_DATA"

        score = max(0.0, min(100.0, score))

        prior3 = mean(totals[-4:-1]) if len(totals) >= 4 else avg3
        trend3 = (
            "ACCELERATING" if avg3 > prior3 * 1.03
            else "DECELERATING" if avg3 < prior3 * 0.97
            else "STABLE"
        )
        momentum = (
            "STRONG" if score >= 80 else
            "POSITIVE" if score >= 65 else
            "NEUTRAL" if score >= 50 else
            "WEAK" if score >= 35 else "NEGATIVE"
        )
        regime = (
            "EXPANSION" if score >= 80 else
            "GROWTH" if score >= 65 else
            "STABLE_GROWTH" if score >= 50 else
            "SLOWDOWN" if score >= 35 else "CONTRACTION"
        )

        snapshot = NioDeliverySnapshot(
            latest_period=latest.period,
            latest_total=latest.total,
            ytd_total=latest.ytd or latest.total,
            yoy_pct=latest.yoy_pct,
            mom_pct=latest.mom_pct,
            avg_3m=round(avg3, 1),
            avg_6m=round(avg6, 1),
            annualized_run_rate=round(run_rate, 0),
            brand_mix=brand_mix,
            latest_brand_deliveries=dict(latest.brands),
            latest_model_deliveries={
                model: payload.deliveries for model, payload in latest.models.items()
            },
        )

        intelligence = NioDeliveryIntelligence(
            delivery_score=round(score, 1),
            momentum_state=momentum,
            trend_3m=trend3,
            brand_diversification=diversification,
            delivery_regime=regime,
            confidence="HIGH" if latest.yoy_pct is not None else "MEDIUM",
            evidence=evidence,
            risks=risks,
        )
        return snapshot, intelligence
