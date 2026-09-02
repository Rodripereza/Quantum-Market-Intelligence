from __future__ import annotations

from collections import defaultdict
from statistics import mean, median
from typing import Any

from app.services.qmi_decision_history_service import QMIDecisionHistoryService
from app.services.qmi_outcome_tracking_service import QMIOutcomeTrackingService


class QMIDecisionPerformanceAnalyticsService:
    """
    DE-CORE-006.6 — Decision Performance Analytics

    Read-only analytical layer over:
      - Decision History (what QMI decided)
      - Outcome Tracking (what happened afterwards)

    v0.1 is deliberately observational:
      - no model training
      - no weight changes
      - no automatic policy calibration

    Directional favorable-rate semantics:
      ACCUMULATE / BUY / INCREASE -> positive return is favorable
      REDUCE / SELL / DECREASE    -> negative return is favorable
      WAIT / HOLD / UNKNOWN       -> not directionally scored
    """

    ENGINE = "QMI Decision Performance Analytics"
    ENGINE_ID = "DE-CORE-006.6"
    VERSION = "0.1.0"
    HORIZONS = (1, 5, 20)

    POSITIVE_ACTIONS = {
        "ACCUMULATE", "BUY", "INCREASE", "ADD", "STRONG_BUY"
    }
    NEGATIVE_ACTIONS = {
        "REDUCE", "SELL", "DECREASE", "TRIM", "STRONG_SELL"
    }

    def __init__(
        self,
        history_service: QMIDecisionHistoryService | None = None,
        outcome_service: QMIOutcomeTrackingService | None = None,
    ) -> None:
        self.history_service = history_service or QMIDecisionHistoryService()
        self.outcome_service = outcome_service or QMIOutcomeTrackingService()

    def analyze_symbol(
        self,
        symbol: str,
        *,
        limit: int = 1000,
    ) -> dict[str, Any]:
        symbol = str(symbol or "").strip().upper()
        if not symbol:
            raise ValueError("Ticker symbol is required.")

        limit = max(1, min(int(limit), 5000))
        outcomes = self.outcome_service.history(symbol, limit=limit)

        records = []
        for outcome in outcomes:
            snapshot = self.history_service.get_snapshot(
                int(outcome["snapshot_id"])
            )
            if not snapshot:
                continue
            records.append(self._record(snapshot, outcome))

        return self._build_report(
            scope="SYMBOL",
            symbol=symbol,
            records=records,
        )

    def analyze_all(
        self,
        symbols: list[str],
        *,
        limit_per_symbol: int = 1000,
    ) -> dict[str, Any]:
        normalized = []
        for symbol in symbols:
            value = str(symbol or "").strip().upper()
            if value and value not in normalized:
                normalized.append(value)

        if not normalized:
            raise ValueError("At least one ticker symbol is required.")

        records = []
        per_symbol = {}

        for symbol in normalized:
            report = self.analyze_symbol(
                symbol,
                limit=limit_per_symbol,
            )
            per_symbol[symbol] = report["summary"]

            outcomes = self.outcome_service.history(
                symbol,
                limit=limit_per_symbol,
            )
            for outcome in outcomes:
                snapshot = self.history_service.get_snapshot(
                    int(outcome["snapshot_id"])
                )
                if snapshot:
                    records.append(self._record(snapshot, outcome))

        report = self._build_report(
            scope="MULTI_SYMBOL",
            symbol=None,
            records=records,
        )
        report["symbols"] = normalized
        report["per_symbol"] = per_symbol
        return report

    def _build_report(
        self,
        *,
        scope: str,
        symbol: str | None,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        status_counts = defaultdict(int)
        action_counts = defaultdict(int)
        exact_anchor_count = 0

        for record in records:
            status_counts[record["outcome_status"]] += 1
            action_counts[record["action"]] += 1
            if record["anchor_source"] == "MARKET_SERVICE_QUOTE":
                exact_anchor_count += 1

        by_action: dict[str, Any] = {}
        for action in sorted(action_counts):
            action_records = [
                record for record in records
                if record["action"] == action
            ]
            by_action[action] = self._segment(action_records, action=action)

        by_confidence: dict[str, Any] = {}
        confidence_values = sorted({
            record["confidence"] for record in records
            if record["confidence"]
        })
        for confidence in confidence_values:
            segment = [
                record for record in records
                if record["confidence"] == confidence
            ]
            by_confidence[confidence] = self._segment(segment)

        horizon_coverage = {}
        for horizon in self.HORIZONS:
            key = f"return_{horizon}d_pct"
            available = sum(
                1 for record in records
                if record.get(key) is not None
            )
            horizon_coverage[f"{horizon}d"] = {
                "available": available,
                "total": len(records),
                "coverage_pct": self._pct(available, len(records)),
            }

        complete = status_counts.get("COMPLETE", 0)

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "scope": scope,
            "symbol": symbol,
            "summary": {
                "decision_count": len(records),
                "outcome_status_counts": {
                    "PENDING": status_counts.get("PENDING", 0),
                    "PARTIAL": status_counts.get("PARTIAL", 0),
                    "COMPLETE": complete,
                },
                "action_counts": dict(action_counts),
                "exact_decision_price_count": exact_anchor_count,
                "exact_decision_price_coverage_pct": self._pct(
                    exact_anchor_count, len(records)
                ),
                "horizon_coverage": horizon_coverage,
                "sample_maturity": self._sample_maturity(records),
            },
            "performance_by_action": by_action,
            "performance_by_confidence": by_confidence,
            "methodology": {
                "returns": (
                    "Raw market return from the persisted decision anchor "
                    "to +1/+5/+20 subsequent market sessions."
                ),
                "favorable_rate": (
                    "Directional diagnostic only. Positive actions are "
                    "favorable when return > 0; negative actions when "
                    "return < 0. WAIT/HOLD are not scored directionally."
                ),
                "mfe_mae": (
                    "MFE/MAE are inherited from Outcome Tracking and are "
                    "descriptive market excursions, not proof of decision quality."
                ),
                "minimum_sample_warning": 20,
                "auto_training": False,
                "weight_changes": False,
            },
        }

    def _segment(
        self,
        records: list[dict[str, Any]],
        *,
        action: str | None = None,
    ) -> dict[str, Any]:
        horizons = {}

        for horizon in self.HORIZONS:
            key = f"return_{horizon}d_pct"
            values = [
                float(record[key])
                for record in records
                if record.get(key) is not None
            ]

            favorable = None
            favorable_n = 0
            favorable_hits = 0

            if action:
                direction = self._action_direction(action)
                if direction != 0:
                    scored = [
                        float(record[key])
                        for record in records
                        if record.get(key) is not None
                    ]
                    favorable_n = len(scored)
                    if favorable_n > 0:
                        if direction > 0:
                            favorable_hits = sum(v > 0 for v in scored)
                        else:
                            favorable_hits = sum(v < 0 for v in scored)
                        favorable = self._pct(
                            favorable_hits,
                            favorable_n,
                        )
                    else:
                        favorable_hits = 0
                        favorable = None

            horizons[f"{horizon}d"] = {
                "sample_size": len(values),
                "average_return_pct": self._avg(values),
                "median_return_pct": self._median(values),
                "min_return_pct": min(values) if values else None,
                "max_return_pct": max(values) if values else None,
                "favorable_rate_pct": favorable,
                "favorable_hits": favorable_hits if favorable is not None else None,
                "directionally_scored_n": favorable_n if favorable is not None else 0,
                "sample_warning": len(values) < 20,
            }

        mfe_values = [
            float(record["mfe_20d_pct"])
            for record in records
            if record.get("mfe_20d_pct") is not None
        ]
        mae_values = [
            float(record["mae_20d_pct"])
            for record in records
            if record.get("mae_20d_pct") is not None
        ]

        return {
            "decision_count": len(records),
            "horizons": horizons,
            "excursion_20d": {
                "sample_size": min(len(mfe_values), len(mae_values)),
                "average_mfe_pct": self._avg(mfe_values),
                "median_mfe_pct": self._median(mfe_values),
                "average_mae_pct": self._avg(mae_values),
                "median_mae_pct": self._median(mae_values),
            },
        }

    def _record(
        self,
        snapshot: dict[str, Any],
        outcome: dict[str, Any],
    ) -> dict[str, Any]:
        return {
            "snapshot_id": int(outcome["snapshot_id"]),
            "symbol": str(outcome.get("symbol") or "").upper(),
            "action": str(
                snapshot.get("action")
                or outcome.get("action")
                or "UNKNOWN"
            ).upper(),
            "confidence": self._upper(snapshot.get("confidence")),
            "intensity": self._upper(snapshot.get("intensity")),
            "policy_state": self._upper(snapshot.get("policy_state")),
            "integrated_posture": self._upper(
                snapshot.get("integrated_posture")
            ),
            "technical_posture": self._upper(
                snapshot.get("technical_posture")
            ),
            "technical_risk": self._upper(
                snapshot.get("technical_risk")
            ),
            "fundamental_stance": self._upper(
                snapshot.get("fundamental_stance")
            ),
            "business_momentum_regime": self._upper(
                snapshot.get("business_momentum_regime")
            ),
            "combined_score": snapshot.get("combined_score"),
            "anchor_source": outcome.get("anchor_source"),
            "anchor_price": outcome.get("anchor_price"),
            "return_1d_pct": outcome.get("return_1d_pct"),
            "return_5d_pct": outcome.get("return_5d_pct"),
            "return_20d_pct": outcome.get("return_20d_pct"),
            "mfe_20d_pct": outcome.get("mfe_20d_pct"),
            "mae_20d_pct": outcome.get("mae_20d_pct"),
            "outcome_status": str(
                outcome.get("status") or "PENDING"
            ).upper(),
        }

    def _sample_maturity(
        self,
        records: list[dict[str, Any]],
    ) -> dict[str, Any]:
        n = len(records)
        available_20d = sum(
            record.get("return_20d_pct") is not None
            for record in records
        )

        if available_20d >= 100:
            state = "ROBUST"
        elif available_20d >= 50:
            state = "DEVELOPING"
        elif available_20d >= 20:
            state = "EARLY"
        else:
            state = "INSUFFICIENT"

        return {
            "state": state,
            "total_decisions": n,
            "complete_20d_samples": available_20d,
            "minimum_for_initial_interpretation": 20,
            "note": (
                "Performance statistics should not be used for automatic "
                "recalibration while sample maturity is insufficient."
            ),
        }

    def _action_direction(self, action: str) -> int:
        action = str(action or "").upper()
        if action in self.POSITIVE_ACTIONS:
            return 1
        if action in self.NEGATIVE_ACTIONS:
            return -1
        return 0

    @staticmethod
    def _avg(values: list[float]) -> float | None:
        return round(mean(values), 4) if values else None

    @staticmethod
    def _median(values: list[float]) -> float | None:
        return round(median(values), 4) if values else None

    @staticmethod
    def _pct(part: int, total: int) -> float:
        if total <= 0:
            return 0.0
        return round((part / total) * 100.0, 2)

    @staticmethod
    def _upper(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text.upper() if text else None
