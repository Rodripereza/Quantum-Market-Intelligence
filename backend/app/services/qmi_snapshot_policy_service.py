from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class QMISnapshotPolicyService:
    """
    DE-CORE-006.1 — Snapshot Policy Engine

    Decides WHEN a DE-CORE-005.2 observation deserves persistence.

    Separation of responsibilities:
    - Snapshot Policy: decides SAVE / SKIP.
    - Decision History Repository (DE-CORE-006.0): performs persistence.

    Initial materiality policy:
    - first snapshot -> SAVE
    - force=True -> SAVE
    - new UTC calendar day -> SAVE
    - categorical decision/risk/business state change -> SAVE
    - combined score move >= 3.0 points -> SAVE
    - Business Momentum move >= 5.0 points -> SAVE
    - divergence spread move >= 10.0 points -> SAVE
    - otherwise -> SKIP

    Price-change materiality is intentionally not activated yet because
    DE-CORE-005.2 does not currently expose a canonical current_price field.
    """

    ENGINE = "QMI Snapshot Policy Engine"
    ENGINE_ID = "DE-CORE-006.1"
    VERSION = "0.1.0"

    COMBINED_SCORE_THRESHOLD = 3.0
    BUSINESS_SCORE_THRESHOLD = 5.0
    DIVERGENCE_SPREAD_THRESHOLD = 10.0

    CATEGORICAL_FIELDS = (
        ("action", "ACTION_CHANGED"),
        ("intensity", "INTENSITY_CHANGED"),
        ("policy_state", "POLICY_STATE_CHANGED"),
        ("strategic_bias", "STRATEGIC_BIAS_CHANGED"),
        ("confidence", "CONFIDENCE_CHANGED"),
        ("integrated_posture", "INTEGRATED_POSTURE_CHANGED"),
        ("timing_gate", "TIMING_GATE_CHANGED"),
        ("technical_posture", "TECHNICAL_POSTURE_CHANGED"),
        ("technical_risk", "TECHNICAL_RISK_CHANGED"),
        ("technical_timing", "TECHNICAL_TIMING_CHANGED"),
        ("execution_state", "EXECUTION_STATE_CHANGED"),
        ("fundamental_stance", "FUNDAMENTAL_STANCE_CHANGED"),
        ("business_momentum_regime", "BUSINESS_REGIME_CHANGED"),
        ("business_momentum_trend", "BUSINESS_TREND_CHANGED"),
        ("business_divergence_state", "DIVERGENCE_STATE_CHANGED"),
        ("business_divergence_severity", "DIVERGENCE_SEVERITY_CHANGED"),
        ("alignment_state", "ALIGNMENT_STATE_CHANGED"),
    )

    def evaluate(
        self,
        *,
        symbol: str,
        action_policy_response: dict[str, Any],
        previous_snapshot: dict[str, Any] | None,
        force: bool = False,
        evaluated_at: datetime | None = None,
    ) -> dict[str, Any]:
        normalized_symbol = symbol.strip().upper()
        current = self._normalize_current(action_policy_response)

        if not current.get("available"):
            return self._decision(
                symbol=normalized_symbol,
                decision="SKIP",
                reason="POLICY_UNAVAILABLE",
                previous_snapshot=previous_snapshot,
                current=current,
                material_changes=[],
                force=force,
                evaluated_at=evaluated_at,
            )

        if force:
            return self._decision(
                symbol=normalized_symbol,
                decision="SAVE",
                reason="FORCED",
                previous_snapshot=previous_snapshot,
                current=current,
                material_changes=[
                    {
                        "field": "force",
                        "previous": False,
                        "current": True,
                        "delta": None,
                    }
                ],
                force=True,
                evaluated_at=evaluated_at,
            )

        if previous_snapshot is None:
            return self._decision(
                symbol=normalized_symbol,
                decision="SAVE",
                reason="FIRST_SNAPSHOT",
                previous_snapshot=None,
                current=current,
                material_changes=[],
                force=False,
                evaluated_at=evaluated_at,
            )

        now = evaluated_at or datetime.now(timezone.utc)
        previous_created = self._parse_datetime(previous_snapshot.get("created_at"))

        if previous_created and previous_created.date() != now.astimezone(timezone.utc).date():
            return self._decision(
                symbol=normalized_symbol,
                decision="SAVE",
                reason="NEW_UTC_DAY",
                previous_snapshot=previous_snapshot,
                current=current,
                material_changes=[
                    {
                        "field": "calendar_day",
                        "previous": previous_created.date().isoformat(),
                        "current": now.astimezone(timezone.utc).date().isoformat(),
                        "delta": None,
                    }
                ],
                force=False,
                evaluated_at=now,
            )

        material_changes: list[dict[str, Any]] = []

        for field, reason in self.CATEGORICAL_FIELDS:
            before = self._upper(previous_snapshot.get(field))
            after = self._upper(current.get(field))

            if self._meaningful_categorical_change(before, after):
                material_changes.append(
                    {
                        "field": field,
                        "previous": before,
                        "current": after,
                        "delta": None,
                        "reason": reason,
                    }
                )

        combined_delta = self._delta(
            previous_snapshot.get("combined_score"),
            current.get("combined_score"),
        )
        if (
            combined_delta is not None
            and abs(combined_delta) >= self.COMBINED_SCORE_THRESHOLD
        ):
            material_changes.append(
                {
                    "field": "combined_score",
                    "previous": self._number_or_none(
                        previous_snapshot.get("combined_score")
                    ),
                    "current": current.get("combined_score"),
                    "delta": round(combined_delta, 2),
                    "threshold": self.COMBINED_SCORE_THRESHOLD,
                    "reason": "COMBINED_SCORE_MATERIAL_MOVE",
                }
            )

        business_delta = self._delta(
            previous_snapshot.get("business_momentum_score"),
            current.get("business_momentum_score"),
        )
        if (
            business_delta is not None
            and abs(business_delta) >= self.BUSINESS_SCORE_THRESHOLD
        ):
            material_changes.append(
                {
                    "field": "business_momentum_score",
                    "previous": self._number_or_none(
                        previous_snapshot.get("business_momentum_score")
                    ),
                    "current": current.get("business_momentum_score"),
                    "delta": round(business_delta, 2),
                    "threshold": self.BUSINESS_SCORE_THRESHOLD,
                    "reason": "BUSINESS_MOMENTUM_MATERIAL_MOVE",
                }
            )

        divergence_delta = self._delta(
            previous_snapshot.get("business_divergence_spread"),
            current.get("business_divergence_spread"),
        )
        if (
            divergence_delta is not None
            and abs(divergence_delta) >= self.DIVERGENCE_SPREAD_THRESHOLD
        ):
            material_changes.append(
                {
                    "field": "business_divergence_spread",
                    "previous": self._number_or_none(
                        previous_snapshot.get("business_divergence_spread")
                    ),
                    "current": current.get("business_divergence_spread"),
                    "delta": round(divergence_delta, 2),
                    "threshold": self.DIVERGENCE_SPREAD_THRESHOLD,
                    "reason": "DIVERGENCE_MATERIAL_MOVE",
                }
            )

        if material_changes:
            return self._decision(
                symbol=normalized_symbol,
                decision="SAVE",
                reason=self._primary_reason(material_changes),
                previous_snapshot=previous_snapshot,
                current=current,
                material_changes=material_changes,
                force=False,
                evaluated_at=now,
            )

        return self._decision(
            symbol=normalized_symbol,
            decision="SKIP",
            reason="NO_MATERIAL_CHANGE",
            previous_snapshot=previous_snapshot,
            current=current,
            material_changes=[],
            force=False,
            evaluated_at=now,
        )

    def _normalize_current(
        self,
        action_policy_response: dict[str, Any],
    ) -> dict[str, Any]:
        policy = (
            action_policy_response.get("action_policy")
            if isinstance(action_policy_response, dict)
            else {}
        ) or {}

        source = policy.get("source") or {}
        business = policy.get("business_context") or {}

        return {
            "available": bool(policy.get("available")),
            "action": self._upper(policy.get("action")),
            "intensity": self._upper(policy.get("intensity")),
            "policy_state": self._upper(policy.get("policy_state")),
            "strategic_bias": self._upper(policy.get("strategic_bias")),
            "confidence": self._upper(policy.get("confidence")),
            "combined_score": self._number_or_none(policy.get("combined_score")),
            "integrated_posture": self._upper(policy.get("integrated_posture")),
            "timing_gate": self._upper(policy.get("timing_gate")),
            "technical_posture": self._upper(source.get("technical_posture")),
            "technical_risk": self._upper(source.get("technical_risk")),
            "technical_timing": self._upper(source.get("technical_timing")),
            "execution_state": self._upper(source.get("execution_state")),
            "fundamental_stance": self._upper(source.get("fundamental_stance")),
            "business_momentum_score": self._number_or_none(
                business.get("score", source.get("business_momentum_score"))
            ),
            "business_momentum_regime": self._upper(
                business.get("regime", source.get("business_momentum_regime"))
            ),
            "business_momentum_trend": self._upper(
                business.get("trend", source.get("business_momentum_trend"))
            ),
            "business_divergence_state": self._upper(
                business.get(
                    "divergence_state",
                    source.get("business_divergence_state"),
                )
            ),
            "business_divergence_spread": self._number_or_none(
                business.get("divergence_spread")
            ),
            "business_divergence_severity": self._upper(
                business.get(
                    "divergence_severity",
                    source.get("business_divergence_severity"),
                )
            ),
            "alignment_state": self._upper(source.get("alignment_state")),
        }

    def _decision(
        self,
        *,
        symbol: str,
        decision: str,
        reason: str,
        previous_snapshot: dict[str, Any] | None,
        current: dict[str, Any],
        material_changes: list[dict[str, Any]],
        force: bool,
        evaluated_at: datetime | None,
    ) -> dict[str, Any]:
        now = evaluated_at or datetime.now(timezone.utc)

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "symbol": symbol,
            "snapshot_decision": decision,
            "should_save": decision == "SAVE",
            "reason": reason,
            "forced": bool(force),
            "evaluated_at": now.astimezone(timezone.utc).isoformat(),
            "previous_snapshot_id": (
                previous_snapshot.get("id") if previous_snapshot else None
            ),
            "previous_action": (
                self._upper(previous_snapshot.get("action"))
                if previous_snapshot
                else None
            ),
            "current_action": current.get("action"),
            "material_changes": material_changes,
            "thresholds": {
                "combined_score_points": self.COMBINED_SCORE_THRESHOLD,
                "business_momentum_points": self.BUSINESS_SCORE_THRESHOLD,
                "divergence_spread_points": self.DIVERGENCE_SPREAD_THRESHOLD,
            },
            "price_materiality": {
                "active": False,
                "reason": (
                    "DE-CORE-005.2 does not yet expose a canonical "
                    "current_price field."
                ),
            },
        }

    @staticmethod
    def _primary_reason(material_changes: list[dict[str, Any]]) -> str:
        if not material_changes:
            return "NO_MATERIAL_CHANGE"

        priority = (
            "ACTION_CHANGED",
            "POLICY_STATE_CHANGED",
            "TIMING_GATE_CHANGED",
            "TECHNICAL_POSTURE_CHANGED",
            "TECHNICAL_RISK_CHANGED",
            "STRATEGIC_BIAS_CHANGED",
            "FUNDAMENTAL_STANCE_CHANGED",
            "BUSINESS_TREND_CHANGED",
            "BUSINESS_REGIME_CHANGED",
            "DIVERGENCE_STATE_CHANGED",
            "DIVERGENCE_SEVERITY_CHANGED",
            "COMBINED_SCORE_MATERIAL_MOVE",
            "BUSINESS_MOMENTUM_MATERIAL_MOVE",
            "DIVERGENCE_MATERIAL_MOVE",
        )

        reasons = {
            item.get("reason")
            for item in material_changes
            if item.get("reason")
        }

        for candidate in priority:
            if candidate in reasons:
                return candidate

        return next(iter(reasons), "MATERIAL_CHANGE")

    @staticmethod
    def _meaningful_categorical_change(
        before: str | None,
        after: str | None,
    ) -> bool:
        if before == after:
            return False

        # Missing data becoming available is useful information.
        if before is None and after is not None:
            return True

        # Do not create noise if a previously available optional field
        # temporarily disappears from one computation.
        if before is not None and after is None:
            return False

        return True

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not value:
            return None

        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc)

    @staticmethod
    def _upper(value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text.upper() if text else None

    @staticmethod
    def _number_or_none(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _delta(cls, before: Any, after: Any) -> float | None:
        before_number = cls._number_or_none(before)
        after_number = cls._number_or_none(after)

        if before_number is None or after_number is None:
            return None

        return after_number - before_number
