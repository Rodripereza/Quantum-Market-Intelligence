from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.services.market.market_service import MarketService
from app.services.qmi_decision_history_service import QMIDecisionHistoryService


class QMIOutcomeTrackingService:
    """
    DE-CORE-006.5 — Outcome Tracking Foundation

    Measures what happened AFTER a persisted QMI decision snapshot.

    This layer is intentionally descriptive:
    - it does NOT label a QMI decision as correct/incorrect
    - it does NOT change model weights
    - it does NOT auto-train

    Horizons are measured in subsequent MARKET SESSIONS:
        +1D, +5D, +20D

    Price anchor policy v0.1:
    - uses the latest available daily close ON OR BEFORE the snapshot date.
    - this prevents using a future trading session.
    - anchor_source is stored explicitly for auditability.

    Storage:
        backend/data/qmi_decision_outcomes.db
    """

    ENGINE = "QMI Outcome Tracking Foundation"
    ENGINE_ID = "DE-CORE-006.5.2"
    VERSION = "0.1.1"

    HORIZONS = (1, 5, 20)

    def __init__(
        self,
        *,
        history_service: QMIDecisionHistoryService | None = None,
        market_service: MarketService | None = None,
        database_path: str | Path | None = None,
    ) -> None:
        self.history_service = history_service or QMIDecisionHistoryService()
        self.market_service = market_service or MarketService()

        if database_path is None:
            backend_root = Path(__file__).resolve().parents[2]
            database_path = backend_root / "data" / "qmi_decision_outcomes.db"

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
                CREATE TABLE IF NOT EXISTS qmi_decision_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    snapshot_id INTEGER NOT NULL UNIQUE,
                    symbol TEXT NOT NULL,
                    action TEXT NOT NULL,
                    decision_created_at TEXT NOT NULL,

                    anchor_date TEXT,
                    anchor_price REAL,
                    anchor_source TEXT,

                    price_1d REAL,
                    return_1d_pct REAL,
                    session_1d_date TEXT,

                    price_5d REAL,
                    return_5d_pct REAL,
                    session_5d_date TEXT,

                    price_20d REAL,
                    return_20d_pct REAL,
                    session_20d_date TEXT,

                    mfe_20d_pct REAL,
                    mae_20d_pct REAL,

                    available_forward_sessions INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL,

                    last_evaluated_at TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_qmi_decision_outcomes_symbol_snapshot
                ON qmi_decision_outcomes(symbol, snapshot_id DESC)
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_qmi_decision_outcomes_status
                ON qmi_decision_outcomes(status, symbol)
                """
            )

            connection.commit()

    def refresh_snapshot(self, snapshot_id: int) -> dict[str, Any]:
        snapshot = self.history_service.get_snapshot(int(snapshot_id))

        if not snapshot:
            raise ValueError(f"Snapshot {snapshot_id} was not found.")

        symbol = str(snapshot.get("symbol") or "").strip().upper()
        if not symbol:
            raise ValueError("Snapshot does not contain a valid symbol.")

        history = self._load_market_history(symbol)
        evaluation = self._evaluate_snapshot(snapshot, history)
        stored = self._upsert(evaluation)

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "outcome": stored,
        }

    def refresh_symbol(
        self,
        symbol: str,
        *,
        snapshot_limit: int = 100,
    ) -> dict[str, Any]:
        normalized_symbol = str(symbol or "").strip().upper()
        if not normalized_symbol:
            raise ValueError("Ticker symbol is required.")

        snapshot_limit = max(1, min(int(snapshot_limit), 1000))
        snapshots = self.history_service.history(
            normalized_symbol,
            limit=snapshot_limit,
        )

        if not snapshots:
            return {
                "engine": self.ENGINE,
                "engine_id": self.ENGINE_ID,
                "version": self.VERSION,
                "status": "operational",
                "symbol": normalized_symbol,
                "snapshot_count": 0,
                "refreshed_count": 0,
                "outcomes": [],
            }

        history = self._load_market_history(normalized_symbol)

        outcomes = []
        for snapshot in reversed(snapshots):
            evaluation = self._evaluate_snapshot(snapshot, history)
            outcomes.append(self._upsert(evaluation))

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "symbol": normalized_symbol,
            "snapshot_count": len(snapshots),
            "refreshed_count": len(outcomes),
            "outcomes": outcomes,
        }

    def refresh_pending(
        self,
        *,
        limit: int = 250,
    ) -> dict[str, Any]:
        limit = max(1, min(int(limit), 1000))

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT snapshot_id, symbol
                FROM qmi_decision_outcomes
                WHERE status != 'COMPLETE'
                ORDER BY snapshot_id ASC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        grouped: dict[str, list[int]] = {}
        for row in rows:
            grouped.setdefault(str(row["symbol"]), []).append(
                int(row["snapshot_id"])
            )

        results = []
        for symbol, snapshot_ids in grouped.items():
            history = self._load_market_history(symbol)

            for snapshot_id in snapshot_ids:
                snapshot = self.history_service.get_snapshot(snapshot_id)
                if not snapshot:
                    continue

                evaluation = self._evaluate_snapshot(snapshot, history)
                results.append(self._upsert(evaluation))

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "requested_limit": limit,
            "refreshed_count": len(results),
            "outcomes": results,
        }

    def history(
        self,
        symbol: str,
        *,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        normalized_symbol = str(symbol or "").strip().upper()
        if not normalized_symbol:
            raise ValueError("Ticker symbol is required.")

        limit = max(1, min(int(limit), 1000))

        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT *
                FROM qmi_decision_outcomes
                WHERE symbol = ?
                ORDER BY snapshot_id DESC
                LIMIT ?
                """,
                (normalized_symbol, limit),
            ).fetchall()

        return [dict(row) for row in rows]

    def get_outcome(self, snapshot_id: int) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM qmi_decision_outcomes
                WHERE snapshot_id = ?
                """,
                (int(snapshot_id),),
            ).fetchone()

        return dict(row) if row else None

    def summary(self, symbol: str) -> dict[str, Any]:
        normalized_symbol = str(symbol or "").strip().upper()
        outcomes = self.history(normalized_symbol, limit=1000)

        status_counts = {
            "PENDING": 0,
            "PARTIAL": 0,
            "COMPLETE": 0,
        }
        for item in outcomes:
            status = str(item.get("status") or "PENDING").upper()
            status_counts[status] = status_counts.get(status, 0) + 1

        return {
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "symbol": normalized_symbol,
            "outcome_count": len(outcomes),
            "status_counts": status_counts,
            "latest_outcome": outcomes[0] if outcomes else None,
            "database": str(self.database_path),
            "assessment_layer": {
                "active": False,
                "note": (
                    "006.5 measures market outcomes only. Decision-quality "
                    "assessment belongs to the later Performance Analytics layer."
                ),
            },
        }

    def _load_market_history(self, symbol: str) -> list[dict[str, Any]]:
        # 5y supports current use and gives enough forward context for older
        # snapshots without requesting unbounded history.
        history = self.market_service.get_history(
            symbol=symbol,
            period="5y",
            interval="1d",
        )

        if not history:
            raise ValueError(
                f"No daily market history is available for {symbol}."
            )

        cleaned = []
        for row in history:
            date = row.get("date")
            close = self._number(row.get("close"))
            high = self._number(row.get("high"))
            low = self._number(row.get("low"))

            if not date or close is None:
                continue

            cleaned.append(
                {
                    "date": str(date),
                    "close": close,
                    "high": high if high is not None else close,
                    "low": low if low is not None else close,
                }
            )

        cleaned.sort(key=lambda item: item["date"])

        if not cleaned:
            raise ValueError(
                f"Market history for {symbol} contains no valid closes."
            )

        return cleaned

    def _evaluate_snapshot(
        self,
        snapshot: dict[str, Any],
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        snapshot_id = int(snapshot["id"])
        symbol = str(snapshot.get("symbol") or "").strip().upper()
        action = str(snapshot.get("action") or "UNKNOWN").upper()
        created_at = str(snapshot.get("created_at") or "")
        snapshot_date = self._utc_date(created_at)

        exact_decision_price = self._number(
            snapshot.get("decision_price")
        )
        exact_captured_at = snapshot.get("decision_price_captured_at")
        exact_source = snapshot.get("decision_price_source")

        anchor_index = None
        for index, row in enumerate(history):
            if row["date"] <= snapshot_date:
                anchor_index = index
            else:
                break

        if anchor_index is None and exact_decision_price is None:
            now = self._now()
            return {
                "snapshot_id": snapshot_id,
                "symbol": symbol,
                "action": action,
                "decision_created_at": created_at,
                "anchor_date": None,
                "anchor_price": None,
                "anchor_source": "DAILY_CLOSE_ON_OR_BEFORE_SNAPSHOT_DATE",
                "price_1d": None,
                "return_1d_pct": None,
                "session_1d_date": None,
                "price_5d": None,
                "return_5d_pct": None,
                "session_5d_date": None,
                "price_20d": None,
                "return_20d_pct": None,
                "session_20d_date": None,
                "mfe_20d_pct": None,
                "mae_20d_pct": None,
                "available_forward_sessions": 0,
                "status": "PENDING",
                "last_evaluated_at": now,
                "created_at": now,
                "updated_at": now,
            }

        if exact_decision_price is not None and exact_decision_price > 0:
            anchor_price = float(exact_decision_price)
            anchor_date = snapshot_date
            anchor_source = exact_source or "EXACT_DECISION_QUOTE"
            forward = [
                row
                for row in history
                if row["date"] > snapshot_date
            ]
        else:
            anchor = history[anchor_index]
            anchor_price = float(anchor["close"])
            anchor_date = anchor["date"]
            anchor_source = "DAILY_CLOSE_ON_OR_BEFORE_SNAPSHOT_DATE"
            forward = history[anchor_index + 1 :]

        horizon_data = {}
        for horizon in self.HORIZONS:
            if len(forward) >= horizon:
                row = forward[horizon - 1]
                price = float(row["close"])
                horizon_data[horizon] = {
                    "price": price,
                    "return_pct": round(
                        ((price / anchor_price) - 1.0) * 100.0,
                        4,
                    ),
                    "date": row["date"],
                }
            else:
                horizon_data[horizon] = {
                    "price": None,
                    "return_pct": None,
                    "date": None,
                }

        observed_20 = forward[:20]
        mfe = None
        mae = None

        if observed_20:
            max_high = max(float(row["high"]) for row in observed_20)
            min_low = min(float(row["low"]) for row in observed_20)

            mfe = round(
                ((max_high / anchor_price) - 1.0) * 100.0,
                4,
            )
            mae = round(
                ((min_low / anchor_price) - 1.0) * 100.0,
                4,
            )

        available = min(len(forward), 20)

        if available >= 20:
            status = "COMPLETE"
        elif available >= 1:
            status = "PARTIAL"
        else:
            status = "PENDING"

        now = self._now()

        return {
            "snapshot_id": snapshot_id,
            "symbol": symbol,
            "action": action,
            "decision_created_at": created_at,
            "anchor_date": anchor_date,
            "anchor_price": anchor_price,
            "anchor_source": anchor_source,
            "price_1d": horizon_data[1]["price"],
            "return_1d_pct": horizon_data[1]["return_pct"],
            "session_1d_date": horizon_data[1]["date"],
            "price_5d": horizon_data[5]["price"],
            "return_5d_pct": horizon_data[5]["return_pct"],
            "session_5d_date": horizon_data[5]["date"],
            "price_20d": horizon_data[20]["price"],
            "return_20d_pct": horizon_data[20]["return_pct"],
            "session_20d_date": horizon_data[20]["date"],
            "mfe_20d_pct": mfe,
            "mae_20d_pct": mae,
            "available_forward_sessions": available,
            "status": status,
            "last_evaluated_at": now,
            "created_at": now,
            "updated_at": now,
        }

    def _upsert(self, values: dict[str, Any]) -> dict[str, Any]:
        existing = self.get_outcome(int(values["snapshot_id"]))

        if existing:
            values["created_at"] = existing.get("created_at") or values["created_at"]

        columns = [
            "snapshot_id",
            "symbol",
            "action",
            "decision_created_at",
            "anchor_date",
            "anchor_price",
            "anchor_source",
            "price_1d",
            "return_1d_pct",
            "session_1d_date",
            "price_5d",
            "return_5d_pct",
            "session_5d_date",
            "price_20d",
            "return_20d_pct",
            "session_20d_date",
            "mfe_20d_pct",
            "mae_20d_pct",
            "available_forward_sessions",
            "status",
            "last_evaluated_at",
            "created_at",
            "updated_at",
        ]

        with self._connect() as connection:
            connection.execute(
                f"""
                INSERT INTO qmi_decision_outcomes (
                    {", ".join(columns)}
                )
                VALUES ({", ".join("?" for _ in columns)})
                ON CONFLICT(snapshot_id) DO UPDATE SET
                    symbol = excluded.symbol,
                    action = excluded.action,
                    decision_created_at = excluded.decision_created_at,
                    anchor_date = excluded.anchor_date,
                    anchor_price = excluded.anchor_price,
                    anchor_source = excluded.anchor_source,
                    price_1d = excluded.price_1d,
                    return_1d_pct = excluded.return_1d_pct,
                    session_1d_date = excluded.session_1d_date,
                    price_5d = excluded.price_5d,
                    return_5d_pct = excluded.return_5d_pct,
                    session_5d_date = excluded.session_5d_date,
                    price_20d = excluded.price_20d,
                    return_20d_pct = excluded.return_20d_pct,
                    session_20d_date = excluded.session_20d_date,
                    mfe_20d_pct = excluded.mfe_20d_pct,
                    mae_20d_pct = excluded.mae_20d_pct,
                    available_forward_sessions = excluded.available_forward_sessions,
                    status = excluded.status,
                    last_evaluated_at = excluded.last_evaluated_at,
                    updated_at = excluded.updated_at
                """,
                tuple(values[column] for column in columns),
            )
            connection.commit()

        stored = self.get_outcome(int(values["snapshot_id"]))
        if stored is None:
            raise RuntimeError("Outcome persistence failed.")
        return stored

    @staticmethod
    def _utc_date(value: str) -> str:
        if not value:
            return datetime.now(timezone.utc).date().isoformat()

        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return value[:10]

        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)

        return parsed.astimezone(timezone.utc).date().isoformat()

    @staticmethod
    def _number(value: Any) -> float | None:
        try:
            if value is None:
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()
