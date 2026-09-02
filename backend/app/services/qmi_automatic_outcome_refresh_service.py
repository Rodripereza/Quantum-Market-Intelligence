from __future__ import annotations

from typing import Any

from app.services.qmi_outcome_tracking_service import (
    QMIOutcomeTrackingService,
)


class QMIAutomaticOutcomeRefreshService:
    """
    DE-CORE-006.5.1 — Automatic Outcome Refresh

    Bridges scheduled market observation with DE-CORE-006.5 Outcome Tracking.

    Responsibilities:
    - refresh/create outcomes after a scheduled ticker analysis
    - advance PENDING -> PARTIAL -> COMPLETE as market sessions arrive
    - keep outcome refresh independent from Decision Engine logic

    This service does NOT:
    - judge whether QMI was right or wrong
    - recalibrate weights
    - train models
    """

    ENGINE = "QMI Automatic Outcome Refresh"
    ENGINE_ID = "DE-CORE-006.5.1"
    VERSION = "0.1.0"

    def __init__(
        self,
        outcome_service: QMIOutcomeTrackingService | None = None,
    ) -> None:
        self.outcome_service = outcome_service or QMIOutcomeTrackingService()

    def refresh_symbol(
        self,
        symbol: str,
        *,
        snapshot_limit: int = 250,
        fail_open: bool = True,
    ) -> dict[str, Any]:
        normalized_symbol = str(symbol or "").strip().upper()

        if not normalized_symbol:
            return self._error(
                symbol="",
                error="Ticker symbol is required.",
                fail_open=fail_open,
            )

        try:
            result = self.outcome_service.refresh_symbol(
                normalized_symbol,
                snapshot_limit=snapshot_limit,
            )

            outcomes = result.get("outcomes") or []

            status_counts = {
                "PENDING": 0,
                "PARTIAL": 0,
                "COMPLETE": 0,
            }

            for item in outcomes:
                status = str(item.get("status") or "PENDING").upper()
                status_counts[status] = status_counts.get(status, 0) + 1

            latest = outcomes[-1] if outcomes else None

            return {
                "engine": self.ENGINE,
                "engine_id": self.ENGINE_ID,
                "version": self.VERSION,
                "status": "operational",
                "symbol": normalized_symbol,
                "refreshed_count": int(result.get("refreshed_count") or 0),
                "status_counts": status_counts,
                "latest_snapshot_id": (
                    latest.get("snapshot_id") if latest else None
                ),
                "latest_outcome_status": (
                    latest.get("status") if latest else None
                ),
                "latest_available_forward_sessions": (
                    latest.get("available_forward_sessions")
                    if latest
                    else None
                ),
                "fail_open": bool(fail_open),
            }

        except Exception as exc:
            if not fail_open:
                raise

            return self._error(
                symbol=normalized_symbol,
                error=f"{type(exc).__name__}: {exc}",
                fail_open=True,
            )

    def refresh_pending(
        self,
        *,
        limit: int = 500,
        fail_open: bool = True,
    ) -> dict[str, Any]:
        try:
            result = self.outcome_service.refresh_pending(limit=limit)

            return {
                "engine": self.ENGINE,
                "engine_id": self.ENGINE_ID,
                "version": self.VERSION,
                "status": "operational",
                "mode": "PENDING_REFRESH",
                "refreshed_count": int(result.get("refreshed_count") or 0),
                "fail_open": bool(fail_open),
            }

        except Exception as exc:
            if not fail_open:
                raise

            return self._error(
                symbol=None,
                error=f"{type(exc).__name__}: {exc}",
                fail_open=True,
            )

    def _error(
        self,
        *,
        symbol: str | None,
        error: str,
        fail_open: bool,
    ) -> dict[str, Any]:
        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "degraded",
            "symbol": symbol,
            "refreshed_count": 0,
            "fail_open": bool(fail_open),
            "error": error,
        }
