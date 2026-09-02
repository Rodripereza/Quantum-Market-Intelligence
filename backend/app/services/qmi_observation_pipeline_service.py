from __future__ import annotations

from typing import Any

from app.services.qmi_decision_history_service import QMIDecisionHistoryService
from app.services.qmi_snapshot_policy_service import QMISnapshotPolicyService
from app.services.qmi_decision_price_capture_service import (
    QMIDecisionPriceCaptureService,
)


class QMIObservationPipelineService:
    """
    DE-CORE-006.2 — Automatic Observation Pipeline

    Connects a completed DE-CORE-005.2 action-policy calculation to:
      DE-CORE-006.1 Snapshot Policy
          ↓
      DE-CORE-006.0 Decision History Repository

    Important behavior:
    - The Decision Engine remains the primary computation.
    - Observation persistence is side-effect intelligence.
    - Persistence failures are FAIL-OPEN by default: they are reported but do
      not invalidate an otherwise valid QMI action-policy response.
    - Snapshot Policy decides SAVE / SKIP.
    - The repository decides HOW to persist.
    """

    ENGINE = "QMI Automatic Observation Pipeline"
    ENGINE_ID = "DE-CORE-006.5.2"
    VERSION = "0.1.1"

    def __init__(
        self,
        history_service: QMIDecisionHistoryService | None = None,
        snapshot_policy_service: QMISnapshotPolicyService | None = None,
        price_capture_service: QMIDecisionPriceCaptureService | None = None,
    ) -> None:
        self.history_service = history_service or QMIDecisionHistoryService()
        self.snapshot_policy_service = (
            snapshot_policy_service or QMISnapshotPolicyService()
        )
        self.price_capture_service = (
            price_capture_service or QMIDecisionPriceCaptureService()
        )

    def observe(
        self,
        *,
        symbol: str,
        period: str,
        interval: str,
        action_policy_response: dict[str, Any],
        force: bool = False,
        fail_open: bool = True,
    ) -> dict[str, Any]:
        normalized_symbol = symbol.strip().upper()

        if not normalized_symbol:
            return self._error_result(
                symbol="",
                error="Ticker symbol is required.",
                fail_open=fail_open,
            )

        try:
            enriched_response, price_capture = self.price_capture_service.enrich(
                symbol=normalized_symbol,
                action_policy_response=action_policy_response,
                fail_open=True,
            )

            previous = self.history_service.latest_snapshot(normalized_symbol)

            snapshot_policy = self.snapshot_policy_service.evaluate(
                symbol=normalized_symbol,
                action_policy_response=enriched_response,
                previous_snapshot=previous,
                force=force,
            )

            persistence = None

            if snapshot_policy.get("should_save"):
                persistence = self.history_service.record_snapshot(
                    symbol=normalized_symbol,
                    period=period,
                    interval=interval,
                    action_policy_response=enriched_response,
                )

            return {
                "engine": self.ENGINE,
                "engine_id": self.ENGINE_ID,
                "version": self.VERSION,
                "status": "operational",
                "symbol": normalized_symbol,
                "mode": "AUTOMATIC",
                "snapshot_decision": snapshot_policy.get("snapshot_decision"),
                "reason": snapshot_policy.get("reason"),
                "saved": persistence is not None,
                "snapshot_id": (
                    persistence.get("snapshot", {}).get("id")
                    if persistence
                    else None
                ),
                "transition_created": bool(
                    persistence and persistence.get("transition_event")
                ),
                "decision_price_capture": price_capture,
                "snapshot_policy": snapshot_policy,
                "persistence": persistence,
            }

        except Exception as exc:
            if not fail_open:
                raise

            return self._error_result(
                symbol=normalized_symbol,
                error=f"{type(exc).__name__}: {exc}",
                fail_open=True,
            )

    def _error_result(
        self,
        *,
        symbol: str,
        error: str,
        fail_open: bool,
    ) -> dict[str, Any]:
        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "degraded",
            "symbol": symbol,
            "mode": "AUTOMATIC",
            "snapshot_decision": "ERROR",
            "reason": "OBSERVATION_PIPELINE_ERROR",
            "saved": False,
            "snapshot_id": None,
            "transition_created": False,
            "decision_price_capture": None,
            "fail_open": bool(fail_open),
            "error": error,
            "snapshot_policy": None,
            "persistence": None,
        }
