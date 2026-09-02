from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Callable

from app.services.qmi_observation_registry_service import (
    QMIObservationRegistryService,
)
from app.services.qmi_automatic_outcome_refresh_service import (
    QMIAutomaticOutcomeRefreshService,
)


class QMIScheduledObservationService:
    """
    DE-CORE-006.5.1 — Scheduled Observation + Automatic Outcome Refresh

    The scheduler no longer owns an in-memory ticker dictionary.
    Every cycle reads the persistent registry from SQLite.

    Pipeline:
      Registry
        -> DE-CORE-006.4 Scheduler
        -> DE-CORE-005.2 Decision Policy
        -> DE-CORE-006.2 Automatic Observation
        -> DE-CORE-006.1 Snapshot Policy
        -> DE-CORE-006.0 Historical Persistence

    No auto-training or model-weight modification occurs here.
    """

    ENGINE = "QMI Scheduled Observation Engine"
    ENGINE_ID = "DE-CORE-006.5.1"
    VERSION = "0.1.2"

    DEFAULT_INTERVAL_SECONDS = 24 * 60 * 60

    def __init__(
        self,
        registry_service: QMIObservationRegistryService | None = None,
        automatic_outcome_service: QMIAutomaticOutcomeRefreshService | None = None,
    ) -> None:
        self.registry_service = (
            registry_service or QMIObservationRegistryService()
        )
        self.automatic_outcome_service = (
            automatic_outcome_service or QMIAutomaticOutcomeRefreshService()
        )
        self._enabled = True
        self._interval_seconds = self.DEFAULT_INTERVAL_SECONDS
        self._task: asyncio.Task | None = None
        self._runner: Callable[..., Any] | None = None
        self._started_at: str | None = None
        self._last_cycle_at: str | None = None
        self._last_results: list[dict[str, Any]] = []

    def configure_runner(self, runner: Callable[..., Any]) -> None:
        self._runner = runner

    async def start(self) -> None:
        if self._task and not self._task.done():
            return

        self._started_at = self._now()
        self._task = asyncio.create_task(self._loop())

    async def stop(self) -> None:
        if not self._task:
            return

        self._task.cancel()

        try:
            await self._task
        except asyncio.CancelledError:
            pass
        finally:
            self._task = None

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(self._interval_seconds)

            if self._enabled:
                await self.run_cycle()

    async def run_cycle(self) -> dict[str, Any]:
        if self._runner is None:
            return {
                "status": "degraded",
                "reason": "RUNNER_NOT_CONFIGURED",
                "results": [],
            }

        symbols = self.registry_service.enabled_symbols()
        results: list[dict[str, Any]] = []

        for symbol in symbols:
            try:
                response = await asyncio.to_thread(
                    self._runner,
                    symbol=symbol,
                    period="1y",
                    interval="1d",
                    pivot_window=3,
                    history_limit=500,
                    observe=True,
                )

                observation = response.get("observation_pipeline") or {}

                outcome_refresh = (
                    self.automatic_outcome_service.refresh_symbol(
                        symbol,
                        snapshot_limit=250,
                        fail_open=True,
                    )
                )

                results.append(
                    {
                        "symbol": symbol,
                        "status": "ok",
                        "action": (
                            (response.get("action_policy") or {}).get("action")
                        ),
                        "snapshot_decision": observation.get(
                            "snapshot_decision"
                        ),
                        "reason": observation.get("reason"),
                        "saved": bool(observation.get("saved")),
                        "snapshot_id": observation.get("snapshot_id"),
                        "outcome_refresh": {
                            "engine_id": outcome_refresh.get("engine_id"),
                            "status": outcome_refresh.get("status"),
                            "refreshed_count": outcome_refresh.get(
                                "refreshed_count"
                            ),
                            "status_counts": outcome_refresh.get(
                                "status_counts"
                            ),
                            "latest_snapshot_id": outcome_refresh.get(
                                "latest_snapshot_id"
                            ),
                            "latest_outcome_status": outcome_refresh.get(
                                "latest_outcome_status"
                            ),
                            "latest_available_forward_sessions": (
                                outcome_refresh.get(
                                    "latest_available_forward_sessions"
                                )
                            ),
                            "error": outcome_refresh.get("error"),
                        },
                    }
                )

            except Exception as exc:
                results.append(
                    {
                        "symbol": symbol,
                        "status": "error",
                        "error": f"{type(exc).__name__}: {exc}",
                    }
                )

        self._last_cycle_at = self._now()
        self._last_results = results

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "status": "operational",
            "cycle_at": self._last_cycle_at,
            "enabled_ticker_count": len(symbols),
            "results": results,
        }

    def status(self) -> dict[str, Any]:
        task_running = bool(self._task and not self._task.done())
        registry = self.registry_service.summary()

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "enabled": self._enabled,
            "task_running": task_running,
            "interval_seconds": self._interval_seconds,
            "interval_hours": self._interval_seconds / 3600,
            "started_at": self._started_at,
            "last_cycle_at": self._last_cycle_at,
            "registered_tickers": registry["tickers"],
            "registry": {
                "engine_id": registry["engine_id"],
                "persistent": True,
                "database": registry["database"],
                "registered_count": registry["registered_count"],
                "enabled_count": registry["enabled_count"],
                "disabled_count": registry["disabled_count"],
            },
            "last_results": self._last_results,
            "automatic_outcome_refresh": {
                "enabled": True,
                "engine_id": self.automatic_outcome_service.ENGINE_ID,
                "fail_open": True,
            },
            "auto_training": False,
        }

    def set_enabled(self, enabled: bool) -> dict[str, Any]:
        self._enabled = bool(enabled)
        return self.status()

    def register_ticker(
        self,
        symbol: str,
        enabled: bool = True,
    ) -> dict[str, Any]:
        self.registry_service.register_ticker(
            symbol,
            enabled=enabled,
        )
        return self.status()

    def remove_ticker(self, symbol: str) -> dict[str, Any]:
        self.registry_service.remove_ticker(symbol)
        return self.status()

    def set_ticker_enabled(
        self,
        symbol: str,
        enabled: bool,
    ) -> dict[str, Any]:
        self.registry_service.set_ticker_enabled(
            symbol,
            enabled,
        )
        return self.status()

    def registry_status(self) -> dict[str, Any]:
        return self.registry_service.summary()

    def refresh_pending_outcomes(
        self,
        *,
        limit: int = 500,
    ) -> dict[str, Any]:
        return self.automatic_outcome_service.refresh_pending(
            limit=limit,
            fail_open=True,
        )

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()


scheduled_observation_service = QMIScheduledObservationService()
