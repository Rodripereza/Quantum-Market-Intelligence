from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class TechnicalStateHistoryService:
    """
    DE-TA-014.1 — Persistent State History & Transition Audit

    Persists DE-TA-014.0 state snapshots and creates an audit event whenever
    the technical state changes.

    Storage:
    backend/data/technical_state_history.db

    This module uses sqlite3 from the Python standard library so it remains
    isolated from the main QMI ORM/database layer.
    """

    def __init__(self, database_path: str | Path | None = None) -> None:
        if database_path is None:
            backend_root = Path(__file__).resolve().parents[4]
            database_path = (
                backend_root
                / "data"
                / "technical_state_history.db"
            )

        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._create_schema()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _create_schema(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS technical_state_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    period TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    current_price REAL,
                    state TEXT NOT NULL,
                    state_score REAL,
                    execution_state TEXT,
                    risk_state TEXT,
                    next_state TEXT,
                    next_state_probability REAL,
                    transition_readiness_state TEXT,
                    transition_readiness_score REAL,
                    direction_score REAL,
                    risk_score REAL,
                    primary_scenario TEXT,
                    primary_score REAL,
                    engine_id TEXT NOT NULL,
                    engine_version TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_state_snapshots_symbol_created
                ON technical_state_snapshots(symbol, created_at DESC)
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS technical_state_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    from_snapshot_id INTEGER,
                    to_snapshot_id INTEGER,
                    transition_type TEXT NOT NULL,
                    state_score REAL,
                    transition_readiness_score REAL,
                    direction_score REAL,
                    risk_score REAL,
                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_state_transitions_symbol_created
                ON technical_state_transitions(symbol, created_at DESC)
                """
            )

    def record_snapshot(
        self,
        *,
        symbol: str,
        period: str,
        interval: str,
        current_price: float | None,
        transition_response: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_symbol = symbol.strip().upper()

        transition = (
            transition_response.get("technical_state_transition") or {}
        )
        current_state = transition.get("current_state") or {}
        next_state = transition.get("next_state_candidate") or {}
        readiness = transition.get("transition_readiness") or {}
        source = transition.get("source_context") or {}

        state = str(current_state.get("state") or "UNKNOWN").upper()
        created_at = datetime.now(timezone.utc).isoformat()

        previous = self.latest_snapshot(normalized_symbol)

        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO technical_state_snapshots (
                    symbol,
                    period,
                    interval,
                    current_price,
                    state,
                    state_score,
                    execution_state,
                    risk_state,
                    next_state,
                    next_state_probability,
                    transition_readiness_state,
                    transition_readiness_score,
                    direction_score,
                    risk_score,
                    primary_scenario,
                    primary_score,
                    engine_id,
                    engine_version,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized_symbol,
                    period,
                    interval,
                    self._number_or_none(current_price),
                    state,
                    self._number_or_none(current_state.get("state_score")),
                    current_state.get("execution_state"),
                    current_state.get("risk_state"),
                    next_state.get("state"),
                    self._number_or_none(next_state.get("probability")),
                    readiness.get("state"),
                    self._number_or_none(readiness.get("score")),
                    self._number_or_none(source.get("direction_score")),
                    self._number_or_none(source.get("risk_score")),
                    source.get("primary_scenario"),
                    self._number_or_none(source.get("primary_score")),
                    transition_response.get("engine_id", "DE-TA-014.0"),
                    transition_response.get("version"),
                    created_at,
                ),
            )

            snapshot_id = int(cursor.lastrowid)

            state_changed = bool(
                previous
                and str(previous.get("state") or "").upper() != state
            )

            transition_event = None

            if state_changed:
                metadata = {
                    "period": period,
                    "interval": interval,
                    "current_price": current_price,
                    "next_state_candidate": next_state.get("state"),
                    "next_state_probability": next_state.get("probability"),
                    "primary_scenario": source.get("primary_scenario"),
                }

                transition_cursor = connection.execute(
                    """
                    INSERT INTO technical_state_transitions (
                        symbol,
                        from_state,
                        to_state,
                        from_snapshot_id,
                        to_snapshot_id,
                        transition_type,
                        state_score,
                        transition_readiness_score,
                        direction_score,
                        risk_score,
                        metadata_json,
                        created_at
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        normalized_symbol,
                        previous.get("state"),
                        state,
                        previous.get("id"),
                        snapshot_id,
                        "STATE_CHANGE",
                        self._number_or_none(
                            current_state.get("state_score")
                        ),
                        self._number_or_none(readiness.get("score")),
                        self._number_or_none(source.get("direction_score")),
                        self._number_or_none(source.get("risk_score")),
                        json.dumps(metadata),
                        created_at,
                    ),
                )

                transition_event = {
                    "id": int(transition_cursor.lastrowid),
                    "symbol": normalized_symbol,
                    "from_state": previous.get("state"),
                    "to_state": state,
                    "transition_type": "STATE_CHANGE",
                    "created_at": created_at,
                }

            connection.commit()

        snapshot = self.get_snapshot(snapshot_id)

        return {
            "snapshot": snapshot,
            "state_changed": state_changed,
            "transition_event": transition_event,
            "previous_state": (
                previous.get("state") if previous else None
            ),
            "database": str(self.database_path),
        }

    def latest_snapshot(self, symbol: str) -> dict[str, Any] | None:
        normalized_symbol = symbol.strip().upper()

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM technical_state_snapshots
                WHERE symbol = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (normalized_symbol,),
            ).fetchone()

        return dict(row) if row else None

    def get_snapshot(self, snapshot_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM technical_state_snapshots
                WHERE id = ?
                """,
                (snapshot_id,),
            ).fetchone()

        return dict(row) if row else None

    def history(
        self,
        symbol: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        normalized_symbol = symbol.strip().upper()
        limit = max(1, min(int(limit), 1000))

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM technical_state_snapshots
                WHERE symbol = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (normalized_symbol, limit),
            ).fetchall()

        return [dict(row) for row in rows]

    def transitions(
        self,
        symbol: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        normalized_symbol = symbol.strip().upper()
        limit = max(1, min(int(limit), 1000))

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM technical_state_transitions
                WHERE symbol = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (normalized_symbol, limit),
            ).fetchall()

        result: list[dict[str, Any]] = []

        for row in rows:
            item = dict(row)

            raw_metadata = item.pop("metadata_json", None)
            if raw_metadata:
                try:
                    item["metadata"] = json.loads(raw_metadata)
                except json.JSONDecodeError:
                    item["metadata"] = None
            else:
                item["metadata"] = None

            result.append(item)

        return result

    def summary(self, symbol: str) -> dict[str, Any]:
        normalized_symbol = symbol.strip().upper()
        latest = self.latest_snapshot(normalized_symbol)

        with self._connect() as connection:
            snapshot_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM technical_state_snapshots
                WHERE symbol = ?
                """,
                (normalized_symbol,),
            ).fetchone()["count"]

            transition_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM technical_state_transitions
                WHERE symbol = ?
                """,
                (normalized_symbol,),
            ).fetchone()["count"]

            state_rows = connection.execute(
                """
                SELECT state, COUNT(*) AS count
                FROM technical_state_snapshots
                WHERE symbol = ?
                GROUP BY state
                ORDER BY count DESC
                """,
                (normalized_symbol,),
            ).fetchall()

        return {
            "symbol": normalized_symbol,
            "latest_snapshot": latest,
            "snapshot_count": int(snapshot_count),
            "transition_count": int(transition_count),
            "state_distribution": {
                row["state"]: int(row["count"])
                for row in state_rows
            },
        }

    @staticmethod
    def _number_or_none(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None
