from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class QMIObservationRegistryService:
    """
    DE-CORE-006.4.1 — Persistent Observation Registry

    Persistent watchlist for DE-CORE-006.4 Scheduled Observation Engine.

    Storage:
        backend/data/qmi_observation_registry.db

    Responsibilities:
    - persist registered tickers
    - persist per-ticker enabled/disabled state
    - survive FastAPI / PC restarts
    - provide deterministic ticker registry to the scheduler

    This service does NOT run market analysis and does NOT train models.
    """

    ENGINE = "QMI Persistent Observation Registry"
    ENGINE_ID = "DE-CORE-006.4.1"
    VERSION = "0.1.0"

    def __init__(self, database_path: str | Path | None = None) -> None:
        if database_path is None:
            backend_root = Path(__file__).resolve().parents[2]
            database_path = backend_root / "data" / "qmi_observation_registry.db"

        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()
        self._seed_defaults()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS qmi_observation_registry (
                    symbol TEXT PRIMARY KEY,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )
            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_qmi_observation_registry_enabled
                ON qmi_observation_registry(enabled, symbol)
                """
            )
            connection.commit()

    def _seed_defaults(self) -> None:
        with self._connect() as connection:
            count = connection.execute(
                "SELECT COUNT(*) AS count FROM qmi_observation_registry"
            ).fetchone()["count"]

            if int(count) == 0:
                now = self._now()
                connection.execute(
                    """
                    INSERT INTO qmi_observation_registry (
                        symbol,
                        enabled,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    ("NIO", 1, now, now),
                )
                connection.commit()

    def list_tickers(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT symbol, enabled, created_at, updated_at
                FROM qmi_observation_registry
                ORDER BY symbol ASC
                """
            ).fetchall()

        return [self._serialize(row) for row in rows]

    def enabled_symbols(self) -> list[str]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT symbol
                FROM qmi_observation_registry
                WHERE enabled = 1
                ORDER BY symbol ASC
                """
            ).fetchall()

        return [str(row["symbol"]) for row in rows]

    def get_ticker(self, symbol: str) -> dict[str, Any] | None:
        normalized = self._normalize_symbol(symbol)

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT symbol, enabled, created_at, updated_at
                FROM qmi_observation_registry
                WHERE symbol = ?
                """,
                (normalized,),
            ).fetchone()

        return self._serialize(row) if row else None

    def register_ticker(
        self,
        symbol: str,
        *,
        enabled: bool = True,
    ) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        now = self._now()

        with self._connect() as connection:
            existing = connection.execute(
                """
                SELECT created_at
                FROM qmi_observation_registry
                WHERE symbol = ?
                """,
                (normalized,),
            ).fetchone()

            if existing:
                connection.execute(
                    """
                    UPDATE qmi_observation_registry
                    SET enabled = ?, updated_at = ?
                    WHERE symbol = ?
                    """,
                    (1 if enabled else 0, now, normalized),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO qmi_observation_registry (
                        symbol,
                        enabled,
                        created_at,
                        updated_at
                    )
                    VALUES (?, ?, ?, ?)
                    """,
                    (normalized, 1 if enabled else 0, now, now),
                )

            connection.commit()

        item = self.get_ticker(normalized)
        if item is None:
            raise RuntimeError("Ticker registration failed.")
        return item

    def set_ticker_enabled(
        self,
        symbol: str,
        enabled: bool,
    ) -> dict[str, Any]:
        normalized = self._normalize_symbol(symbol)
        now = self._now()

        with self._connect() as connection:
            cursor = connection.execute(
                """
                UPDATE qmi_observation_registry
                SET enabled = ?, updated_at = ?
                WHERE symbol = ?
                """,
                (1 if enabled else 0, now, normalized),
            )

            if cursor.rowcount == 0:
                raise ValueError(f"Ticker {normalized} is not registered.")

            connection.commit()

        item = self.get_ticker(normalized)
        if item is None:
            raise RuntimeError("Ticker update failed.")
        return item

    def remove_ticker(self, symbol: str) -> bool:
        normalized = self._normalize_symbol(symbol)

        with self._connect() as connection:
            cursor = connection.execute(
                """
                DELETE FROM qmi_observation_registry
                WHERE symbol = ?
                """,
                (normalized,),
            )
            connection.commit()

        return cursor.rowcount > 0

    def summary(self) -> dict[str, Any]:
        tickers = self.list_tickers()
        enabled_count = sum(1 for item in tickers if item["enabled"])

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "database": str(self.database_path),
            "registered_count": len(tickers),
            "enabled_count": enabled_count,
            "disabled_count": len(tickers) - enabled_count,
            "tickers": tickers,
        }

    @staticmethod
    def _serialize(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "symbol": str(row["symbol"]),
            "enabled": bool(row["enabled"]),
            "created_at": row["created_at"],
            "updated_at": row["updated_at"],
        }

    @staticmethod
    def _normalize_symbol(symbol: str) -> str:
        normalized = str(symbol or "").strip().upper()
        if not normalized:
            raise ValueError("Ticker symbol is required.")
        if len(normalized) > 20:
            raise ValueError("Ticker symbol is too long.")
        return normalized

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
