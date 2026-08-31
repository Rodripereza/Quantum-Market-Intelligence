from __future__ import annotations

from statistics import mean
from typing import Any, Dict, List, Optional


class NioDeliveryMomentumEngine:
    """
    DE-NIO-DM-001.0

    Converts NIO delivery history plus ASP intelligence into normalized
    business-momentum signals for downstream Fundamental / Decision engines.

    This engine does NOT generate BUY/SELL signals directly.
    """

    ENGINE_ID = "DE-NIO-DM-001.1"
    VERSION = "0.1.1"

    @staticmethod
    def _clamp(value: float, low: float = 0.0, high: float = 100.0) -> float:
        return max(low, min(high, float(value)))

    @staticmethod
    def _score_linear(value: Optional[float], bearish: float, bullish: float) -> float:
        if value is None:
            return 50.0
        if bullish == bearish:
            return 50.0
        normalized = (float(value) - bearish) / (bullish - bearish)
        return NioDeliveryMomentumEngine._clamp(normalized * 100.0)

    @staticmethod
    def _quarter(month: int) -> int:
        return ((int(month) - 1) // 3) + 1

    @staticmethod
    def _effective_asp(row: Optional[Dict[str, Any]]) -> Optional[float]:
        if not row:
            return None
        reported = row.get("reported_asp_rmb")
        forecast = row.get("forecast_asp_rmb")
        if reported is not None:
            return float(reported)
        if forecast is not None:
            return float(forecast)
        return None

    def _three_month_yoy(self, records: List[Any]) -> Optional[float]:
        if len(records) < 3:
            return None

        latest3 = records[-3:]
        previous_year = {
            (int(r.year), int(r.month)): r
            for r in records
        }

        current_total = 0
        prior_total = 0

        for row in latest3:
            prior = previous_year.get((int(row.year) - 1, int(row.month)))
            if prior is None:
                return None
            current_total += int(row.total)
            prior_total += int(prior.total)

        if prior_total <= 0:
            return None

        return (current_total / prior_total - 1.0) * 100.0

    def _quarterly_growth(self, records: List[Any]) -> Optional[float]:
        if not records:
            return None

        latest = records[-1]
        current_q = self._quarter(latest.month)
        current_year = int(latest.year)

        current_rows = [
            r for r in records
            if int(r.year) == current_year and self._quarter(r.month) == current_q
        ]
        if not current_rows:
            return None

        completed_months = sorted(int(r.month) for r in current_rows)
        current_total = sum(int(r.total) for r in current_rows)

        if current_q == 1:
            prior_q = 4
            prior_year = current_year - 1
        else:
            prior_q = current_q - 1
            prior_year = current_year

        prior_rows = [
            r for r in records
            if int(r.year) == prior_year and self._quarter(r.month) == prior_q
        ]
        prior_rows = sorted(prior_rows, key=lambda r: int(r.month))

        # Compare like-for-like month count for partial quarters.
        month_count = len(completed_months)
        prior_rows = prior_rows[:month_count]

        if len(prior_rows) != month_count:
            return None

        prior_total = sum(int(r.total) for r in prior_rows)
        if prior_total <= 0:
            return None

        return (current_total / prior_total - 1.0) * 100.0

    def _persistence(self, records: List[Any], window: int = 6) -> Dict[str, Any]:
        recent = records[-window:]
        yoy_values = [
            float(r.yoy_pct)
            for r in recent
            if getattr(r, "yoy_pct", None) is not None
        ]

        if not yoy_values:
            return {
                "positive_months": 0,
                "observed_months": 0,
                "ratio_pct": None,
                "score": 50.0,
            }

        positive = sum(1 for value in yoy_values if value > 0)
        ratio = positive / len(yoy_values) * 100.0

        return {
            "positive_months": positive,
            "observed_months": len(yoy_values),
            "ratio_pct": round(ratio, 1),
            "score": round(self._clamp(ratio), 1),
        }

    def _mix_quality(
        self,
        records: List[Any],
        asp_intelligence: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        latest = records[-1]
        brand_total = sum(int(v) for v in latest.brands.values()) if latest.brands else 0

        nio_share = (
            float(latest.brands.get("NIO", 0)) / brand_total * 100.0
            if brand_total > 0 else None
        )
        onvo_share = (
            float(latest.brands.get("ONVO", 0)) / brand_total * 100.0
            if brand_total > 0 else None
        )
        firefly_share = (
            float(latest.brands.get("FIREFLY", 0)) / brand_total * 100.0
            if brand_total > 0 else None
        )

        premiumization = (
            str((asp_intelligence or {}).get("premiumization_state", "UNKNOWN"))
            .upper()
        )

        premium_map = {
            "STRONG_PREMIUMIZATION": 90.0,
            "PREMIUMIZING": 75.0,
            "STABLE": 55.0,
            "DILUTING": 35.0,
            "STRONG_DILUTION": 15.0,
            "UNKNOWN": 50.0,
        }
        premium_score = premium_map.get(premiumization, 50.0)

        # Core-NIO share is useful context, but premiumization from ASP/model mix
        # is the dominant quality signal.
        core_score = 50.0 if nio_share is None else self._clamp(30.0 + nio_share * 0.7)
        score = premium_score * 0.75 + core_score * 0.25

        return {
            "score": round(self._clamp(score), 1),
            "premiumization_state": premiumization,
            "nio_share_pct": round(nio_share, 1) if nio_share is not None else None,
            "onvo_share_pct": round(onvo_share, 1) if onvo_share is not None else None,
            "firefly_share_pct": round(firefly_share, 1) if firefly_share is not None else None,
        }

    def _asp_momentum(
        self,
        asp_intelligence: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        quarterly = list((asp_intelligence or {}).get("quarterly", []))
        latest = quarterly[-1] if quarterly else None
        qoq = latest.get("asp_qoq_pct") if latest else None

        # -10% QoQ => 0, 0% => 50, +10% => 100.
        score = self._score_linear(qoq, -10.0, 10.0)

        return {
            "score": round(score, 1),
            "qoq_pct": round(float(qoq), 1) if qoq is not None else None,
            "trend": (asp_intelligence or {}).get("asp_trend", "UNKNOWN"),
            "premiumization_state": (asp_intelligence or {}).get(
                "premiumization_state", "UNKNOWN"
            ),
        }

    def _revenue_momentum(
        self,
        records: List[Any],
        asp_intelligence: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        quarterly = list((asp_intelligence or {}).get("quarterly", []))
        if len(quarterly) < 2 or not records:
            return {
                "score": 50.0,
                "qoq_pct": None,
                "latest_revenue_rmb": None,
                "previous_revenue_rmb": None,
                "comparison": "insufficient_data",
                "observed_months": 0,
            }

        latest_qrow = quarterly[-1]
        latest_year = int(latest_qrow.get("year", 0) or 0)
        latest_q = int(latest_qrow.get("quarter_number", 0) or 0)

        if latest_q == 1:
            prior_q = 4
            prior_year = latest_year - 1
        else:
            prior_q = latest_q - 1
            prior_year = latest_year

        prior_qrow = next(
            (
                row
                for row in reversed(quarterly[:-1])
                if int(row.get("year", 0) or 0) == prior_year
                and int(row.get("quarter_number", 0) or 0) == prior_q
            ),
            None,
        )

        if prior_qrow is None:
            return {
                "score": 50.0,
                "qoq_pct": None,
                "latest_revenue_rmb": None,
                "previous_revenue_rmb": None,
                "comparison": "insufficient_prior_quarter",
                "observed_months": 0,
            }

        latest_rows = sorted(
            [
                r for r in records
                if int(r.year) == latest_year
                and self._quarter(r.month) == latest_q
            ],
            key=lambda r: int(r.month),
        )
        observed_months = len(latest_rows)

        prior_rows = sorted(
            [
                r for r in records
                if int(r.year) == prior_year
                and self._quarter(r.month) == prior_q
            ],
            key=lambda r: int(r.month),
        )

        # Partial quarter => compare the same number of months from the prior quarter.
        comparable_prior_rows = prior_rows[:observed_months]

        latest_asp = self._effective_asp(latest_qrow)
        prior_asp = self._effective_asp(prior_qrow)

        latest_deliveries = sum(int(r.total) for r in latest_rows)
        prior_deliveries = sum(int(r.total) for r in comparable_prior_rows)

        comparable = (
            observed_months > 0
            and len(comparable_prior_rows) == observed_months
            and latest_asp is not None
            and prior_asp is not None
            and prior_deliveries > 0
        )

        if not comparable:
            return {
                "score": 50.0,
                "qoq_pct": None,
                "latest_revenue_rmb": None,
                "previous_revenue_rmb": None,
                "comparison": "insufficient_like_for_like_data",
                "observed_months": observed_months,
            }

        latest_revenue = float(latest_asp) * float(latest_deliveries)
        prior_revenue = float(prior_asp) * float(prior_deliveries)

        qoq = (
            (latest_revenue / prior_revenue - 1.0) * 100.0
            if prior_revenue > 0
            else None
        )

        # Revenue growth has wider natural dispersion than ASP.
        score = self._score_linear(qoq, -30.0, 30.0)

        return {
            "score": round(score, 1),
            "qoq_pct": round(qoq, 1) if qoq is not None else None,
            "latest_revenue_rmb": round(latest_revenue, 2),
            "previous_revenue_rmb": round(prior_revenue, 2),
            "latest_deliveries": latest_deliveries,
            "previous_comparable_deliveries": prior_deliveries,
            "latest_asp_rmb": round(float(latest_asp), 2),
            "previous_asp_rmb": round(float(prior_asp), 2),
            "comparison": (
                "full_quarter_qoq"
                if observed_months >= 3
                else "like_for_like_partial_quarter"
            ),
            "observed_months": observed_months,
            "latest_quarter": latest_qrow.get("quarter"),
            "previous_quarter": prior_qrow.get("quarter"),
        }

    def analyze(
        self,
        records: List[Any],
        asp_intelligence: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not records:
            raise ValueError("NIO delivery history is empty.")

        latest = records[-1]
        totals = [int(r.total) for r in records]

        latest_yoy = (
            float(latest.yoy_pct)
            if getattr(latest, "yoy_pct", None) is not None
            else None
        )
        three_month_yoy = self._three_month_yoy(records)
        qoq = self._quarterly_growth(records)

        avg3 = mean(totals[-3:]) if len(totals) >= 3 else mean(totals)
        avg6 = mean(totals[-6:]) if len(totals) >= 6 else mean(totals)
        run_rate = avg3 * 12.0

        # Component normalization.
        monthly_yoy_score = self._score_linear(latest_yoy, -30.0, 70.0)
        three_month_yoy_score = self._score_linear(three_month_yoy, -25.0, 60.0)
        qoq_score = self._score_linear(qoq, -25.0, 35.0)
        run_rate_score = self._score_linear(run_rate, 250000.0, 600000.0)

        persistence = self._persistence(records)
        mix_quality = self._mix_quality(records, asp_intelligence)
        asp_momentum = self._asp_momentum(asp_intelligence)
        revenue_momentum = self._revenue_momentum(records, asp_intelligence)

        # Core DMS: delivery-volume behavior. ASP/revenue are reported alongside it
        # and combined into business_momentum_score, avoiding double counting.
        delivery_score = (
            monthly_yoy_score * 0.25
            + three_month_yoy_score * 0.20
            + qoq_score * 0.15
            + run_rate_score * 0.15
            + float(persistence["score"]) * 0.10
            + float(mix_quality["score"]) * 0.15
        )
        delivery_score = self._clamp(delivery_score)

        # Broader business momentum incorporates monetization.
        business_score = (
            delivery_score * 0.65
            + float(asp_momentum["score"]) * 0.15
            + float(revenue_momentum["score"]) * 0.20
        )
        business_score = self._clamp(business_score)

        evidence: List[str] = []
        risks: List[str] = []

        if latest_yoy is not None:
            if latest_yoy >= 30:
                evidence.append(
                    f"Latest monthly deliveries are growing {latest_yoy:.1f}% year over year."
                )
            elif latest_yoy < 0:
                risks.append(
                    f"Latest monthly deliveries are down {abs(latest_yoy):.1f}% year over year."
                )

        if three_month_yoy is not None:
            if three_month_yoy > 15:
                evidence.append(
                    f"Three-month delivery growth remains strong at {three_month_yoy:.1f}% YoY."
                )
            elif three_month_yoy < 0:
                risks.append(
                    f"Three-month deliveries are {abs(three_month_yoy):.1f}% below the prior-year period."
                )

        if qoq is not None:
            if qoq > 10:
                evidence.append(
                    f"Like-for-like quarterly delivery momentum is accelerating {qoq:.1f}%."
                )
            elif qoq < -10:
                risks.append(
                    f"Like-for-like quarterly delivery momentum is contracting {abs(qoq):.1f}%."
                )

        if run_rate >= 450000:
            evidence.append(
                f"Recent three-month run-rate is approximately {run_rate:,.0f} vehicles annualized."
            )
        elif run_rate < 300000:
            risks.append(
                f"Recent three-month run-rate is only approximately {run_rate:,.0f} vehicles annualized."
            )

        if mix_quality["premiumization_state"] in (
            "PREMIUMIZING",
            "STRONG_PREMIUMIZATION",
        ):
            evidence.append("Current model mix indicates ASP premiumization.")
        elif mix_quality["premiumization_state"] in (
            "DILUTING",
            "STRONG_DILUTION",
        ):
            risks.append("Current model mix indicates ASP dilution.")

        if asp_momentum["qoq_pct"] is not None:
            if asp_momentum["qoq_pct"] > 1:
                evidence.append(
                    f"ASP momentum is positive at {asp_momentum['qoq_pct']:.1f}% QoQ."
                )
            elif asp_momentum["qoq_pct"] < -1:
                risks.append(
                    f"ASP momentum is negative at {asp_momentum['qoq_pct']:.1f}% QoQ."
                )

        if revenue_momentum["qoq_pct"] is not None:
            comparison_label = (
                "like-for-like partial-quarter"
                if revenue_momentum.get("comparison") == "like_for_like_partial_quarter"
                else "quarter-over-quarter"
            )
            if revenue_momentum["qoq_pct"] > 5:
                evidence.append(
                    f"Revenue momentum is positive at {revenue_momentum['qoq_pct']:.1f}% "
                    f"on a {comparison_label} basis."
                )
            elif revenue_momentum["qoq_pct"] < -5:
                risks.append(
                    f"Revenue momentum is negative at {revenue_momentum['qoq_pct']:.1f}% "
                    f"on a {comparison_label} basis."
                )

        observed = sum(
            value is not None
            for value in (latest_yoy, three_month_yoy, qoq, asp_momentum["qoq_pct"])
        )
        price_confidence = str((asp_intelligence or {}).get("confidence", "LOW")).upper()

        if observed >= 4 and price_confidence == "HIGH":
            confidence = "HIGH"
        elif observed >= 2:
            confidence = "MEDIUM"
        else:
            confidence = "LOW"

        regime = (
            "STRONG_EXPANSION" if business_score >= 80
            else "EXPANSION" if business_score >= 65
            else "STABLE" if business_score >= 50
            else "SLOWDOWN" if business_score >= 35
            else "CONTRACTION"
        )

        trend = (
            "ACCELERATING"
            if avg3 > avg6 * 1.05 and (three_month_yoy is None or three_month_yoy > 0)
            else "DECELERATING"
            if avg3 < avg6 * 0.95
            else "STABLE"
        )

        return {
            "engine": "NIO Delivery Momentum Engine",
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "methodology": "normalized_delivery_volume_mix_asp_and_like_for_like_revenue_momentum",
            "latest_period": latest.period,
            "score": round(delivery_score, 1),
            "business_momentum_score": round(business_score, 1),
            "regime": regime,
            "trend": trend,
            "confidence": confidence,
            "components": {
                "monthly_yoy": {
                    "value_pct": round(latest_yoy, 1) if latest_yoy is not None else None,
                    "score": round(monthly_yoy_score, 1),
                    "weight": 0.25,
                },
                "three_month_yoy": {
                    "value_pct": round(three_month_yoy, 1) if three_month_yoy is not None else None,
                    "score": round(three_month_yoy_score, 1),
                    "weight": 0.20,
                },
                "qoq": {
                    "value_pct": round(qoq, 1) if qoq is not None else None,
                    "score": round(qoq_score, 1),
                    "weight": 0.15,
                    "comparison": "like_for_like_partial_quarter",
                },
                "run_rate": {
                    "annualized_deliveries": round(run_rate, 0),
                    "avg_3m": round(avg3, 1),
                    "avg_6m": round(avg6, 1),
                    "score": round(run_rate_score, 1),
                    "weight": 0.15,
                },
                "persistence": {
                    **persistence,
                    "weight": 0.10,
                },
                "mix_quality": {
                    **mix_quality,
                    "weight": 0.15,
                },
                "asp_momentum": asp_momentum,
                "revenue_momentum": revenue_momentum,
            },
            "evidence": evidence,
            "risks": risks,
        }
