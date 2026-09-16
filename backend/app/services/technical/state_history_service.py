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
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS technical_driver_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL, period TEXT NOT NULL, interval TEXT NOT NULL,
                    engine TEXT NOT NULL, score REAL, state TEXT, confidence REAL,
                    effective_weight_pct REAL, normalized_contribution REAL,
                    vote TEXT, source TEXT, created_at TEXT NOT NULL
                )
                """
            )
            columns = {
                row["name"]
                for row in connection.execute("PRAGMA table_info(technical_driver_snapshots)").fetchall()
            }
            if "decision_posture" not in columns:
                connection.execute(
                    "ALTER TABLE technical_driver_snapshots ADD COLUMN decision_posture TEXT"
                )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_driver_snapshots_symbol_created
                ON technical_driver_snapshots(symbol, created_at DESC)
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

    def record_driver_snapshot(
        self,
        *,
        symbol: str,
        period: str,
        interval: str,
        confluence_response: dict[str, Any],
        decision_posture: str | None = None,
    ) -> dict[str, Any]:
        normalized_symbol = symbol.strip().upper()
        diagnostics = ((confluence_response.get("technical_confluence") or {}).get("diagnostics") or {})
        contributions = diagnostics.get("engine_contributions") or []
        created_at = datetime.now(timezone.utc).isoformat()
        rows = []
        with self._connect() as connection:
            for item in contributions:
                if not isinstance(item, dict) or item.get("available") is False:
                    continue
                engine = str(item.get("engine") or "").strip().lower()
                if not engine:
                    continue
                cursor = connection.execute(
                    """INSERT INTO technical_driver_snapshots
                    (symbol,period,interval,engine,score,state,confidence,effective_weight_pct,normalized_contribution,vote,source,created_at,decision_posture)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (normalized_symbol,period,interval,engine,self._number_or_none(item.get("score")),
                     item.get("state"),self._number_or_none(item.get("confidence")),
                     self._number_or_none(item.get("effective_weight_pct")),
                     self._number_or_none(item.get("normalized_contribution")),
                     item.get("vote"),item.get("source"),created_at,
                     str(decision_posture).upper() if decision_posture else None),
                )
                rows.append({"id": int(cursor.lastrowid), "engine": engine})
            connection.commit()
        return {"symbol": normalized_symbol, "recorded": bool(rows), "driver_count": len(rows), "created_at": created_at}

    def latest_driver_snapshot(self, symbol: str) -> dict[str, Any] | None:
        normalized_symbol = symbol.strip().upper()
        with self._connect() as connection:
            stamp = connection.execute(
                """SELECT created_at FROM technical_driver_snapshots
                   WHERE symbol=? ORDER BY id DESC LIMIT 1""", (normalized_symbol,)
            ).fetchone()
            if not stamp:
                return None
            rows = connection.execute(
                """SELECT * FROM technical_driver_snapshots
                   WHERE symbol=? AND created_at=? ORDER BY id ASC""",
                (normalized_symbol, stamp["created_at"]),
            ).fetchall()
        return {"symbol": normalized_symbol, "created_at": stamp["created_at"], "drivers": [dict(r) for r in rows]}

    def driver_history(self, symbol: str, *, limit: int = 12) -> list[dict[str, Any]]:
        normalized_symbol = symbol.strip().upper()
        limit = max(1, min(int(limit), 100))
        with self._connect() as connection:
            stamps = connection.execute(
                """SELECT created_at FROM technical_driver_snapshots
                   WHERE symbol=? GROUP BY created_at
                   ORDER BY MAX(id) DESC LIMIT ?""",
                (normalized_symbol, limit),
            ).fetchall()
            result = []
            for stamp in reversed(stamps):
                rows = connection.execute(
                    """SELECT engine, score, state, confidence, effective_weight_pct,
                              normalized_contribution
                       FROM technical_driver_snapshots
                       WHERE symbol=? AND created_at=? ORDER BY id ASC""",
                    (normalized_symbol, stamp["created_at"]),
                ).fetchall()
                result.append({"created_at": stamp["created_at"], "drivers": [dict(row) for row in rows]})
        return result

    def evolution_timeline(self, symbol: str, *, limit: int = 12) -> dict[str, Any]:
        normalized_symbol = symbol.strip().upper()
        limit = max(2, min(int(limit), 50))
        states = list(reversed(self.history(normalized_symbol, limit=limit)))
        drivers = self.driver_history(normalized_symbol, limit=limit)
        state_points = [{
            "id": row.get("id"), "created_at": row.get("created_at"),
            "state": row.get("state"), "state_score": row.get("state_score"),
            "direction_score": row.get("direction_score"),
            "transition_readiness": row.get("transition_readiness_score"),
            "transition_probability": row.get("next_state_probability"),
            "risk_score": row.get("risk_score"), "risk_state": row.get("risk_state"),
            "price": row.get("current_price"),
        } for row in states]
        driver_series: dict[str, list[dict[str, Any]]] = {}
        for snapshot in drivers:
            for row in snapshot.get("drivers", []):
                engine = str(row.get("engine") or "").lower()
                if engine:
                    driver_series.setdefault(engine, []).append({
                        "created_at": snapshot.get("created_at"), "score": row.get("score"),
                        "confidence": row.get("confidence"), "weight_pct": row.get("effective_weight_pct"),
                        "contribution": row.get("normalized_contribution"), "state": row.get("state"),
                    })
        return {"symbol": normalized_symbol, "available": len(state_points) >= 2 or len(drivers) >= 2,
                "state_points": state_points, "driver_snapshots": drivers,
                "driver_series": driver_series, "point_count": max(len(state_points), len(drivers)),
                "limit": limit}

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
