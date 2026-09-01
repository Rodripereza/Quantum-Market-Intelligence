from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class QMIDecisionHistoryService:
    """
    DE-CORE-006.0 — Decision History & State Transition Engine

    Persists DE-CORE-005.2 action-policy snapshots and creates a transition
    audit event only when the QMI action changes.

    Storage:
    backend/data/qmi_decision_history.db

    The history database is intentionally isolated from the portfolio ORM.
    This mirrors the existing DE-TA-014.1 technical-state history pattern.
    """

    ENGINE = "QMI Decision History & State Transition Engine"
    ENGINE_ID = "DE-CORE-006.0"
    VERSION = "0.1.0"

    def __init__(self, database_path: str | Path | None = None) -> None:
        if database_path is None:
            backend_root = Path(__file__).resolve().parents[3]
            database_path = backend_root / "data" / "qmi_decision_history.db"

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
                CREATE TABLE IF NOT EXISTS qmi_decision_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    period TEXT NOT NULL,
                    interval TEXT NOT NULL,

                    action TEXT NOT NULL,
                    intensity TEXT,
                    policy_state TEXT,
                    strategic_bias TEXT,
                    confidence TEXT,

                    combined_score REAL,
                    integrated_posture TEXT,
                    timing_gate TEXT,

                    technical_posture TEXT,
                    technical_risk TEXT,
                    technical_timing TEXT,
                    execution_state TEXT,

                    fundamental_stance TEXT,

                    business_momentum_score REAL,
                    business_momentum_regime TEXT,
                    business_momentum_trend TEXT,
                    business_momentum_confidence TEXT,

                    business_divergence_state TEXT,
                    business_divergence_spread REAL,
                    business_divergence_severity TEXT,

                    alignment_state TEXT,

                    source_engine_id TEXT,
                    source_engine_version TEXT,
                    source_cross_engine_id TEXT,

                    created_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_qmi_decision_snapshots_symbol_created
                ON qmi_decision_snapshots(symbol, created_at DESC)
                """
            )

            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS qmi_decision_transitions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,

                    from_action TEXT NOT NULL,
                    to_action TEXT NOT NULL,

                    from_snapshot_id INTEGER,
                    to_snapshot_id INTEGER,

                    transition_type TEXT NOT NULL,
                    transition_direction TEXT,
                    primary_driver TEXT,

                    combined_score_before REAL,
                    combined_score_after REAL,
                    combined_score_delta REAL,

                    technical_posture_before TEXT,
                    technical_posture_after TEXT,
                    technical_risk_before TEXT,
                    technical_risk_after TEXT,

                    fundamental_stance_before TEXT,
                    fundamental_stance_after TEXT,

                    business_score_before REAL,
                    business_score_after REAL,
                    business_score_delta REAL,

                    strategic_bias_before TEXT,
                    strategic_bias_after TEXT,

                    divergence_state_before TEXT,
                    divergence_state_after TEXT,
                    divergence_spread_before REAL,
                    divergence_spread_after REAL,
                    divergence_spread_delta REAL,

                    metadata_json TEXT,
                    created_at TEXT NOT NULL
                )
                """
            )

            connection.execute(
                """
                CREATE INDEX IF NOT EXISTS
                idx_qmi_decision_transitions_symbol_created
                ON qmi_decision_transitions(symbol, created_at DESC)
                """
            )

            connection.commit()

    def record_snapshot(
        self,
        *,
        symbol: str,
        period: str,
        interval: str,
        action_policy_response: dict[str, Any],
    ) -> dict[str, Any]:
        normalized_symbol = symbol.strip().upper()

        policy = (
            action_policy_response.get("action_policy")
            if isinstance(action_policy_response, dict)
            else {}
        ) or {}

        if not policy.get("available"):
            raise ValueError(
                "Cannot persist QMI decision history because action policy is unavailable."
            )

        source = policy.get("source") or {}
        business = policy.get("business_context") or {}

        action = str(policy.get("action") or "WAIT").upper()
        created_at = datetime.now(timezone.utc).isoformat()
        previous = self.latest_snapshot(normalized_symbol)

        values = {
            "symbol": normalized_symbol,
            "period": period,
            "interval": interval,
            "action": action,
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
            "business_momentum_confidence": self._upper(
                business.get("confidence")
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
            "source_engine_id": action_policy_response.get("engine_id"),
            "source_engine_version": action_policy_response.get("version"),
            "source_cross_engine_id": action_policy_response.get(
                "source_cross_engine_id"
            )
            or source.get("cross_engine_id"),
            "created_at": created_at,
        }

        columns = list(values.keys())
        placeholders = ", ".join("?" for _ in columns)

        with self._connect() as connection:
            cursor = connection.execute(
                f"""
                INSERT INTO qmi_decision_snapshots (
                    {", ".join(columns)}
                )
                VALUES ({placeholders})
                """,
                tuple(values[column] for column in columns),
            )
            snapshot_id = int(cursor.lastrowid)

            action_changed = bool(
                previous
                and str(previous.get("action") or "").upper() != action
            )

            transition_event = None

            if action_changed:
                transition_event = self._record_transition(
                    connection=connection,
                    previous=previous,
                    current={**values, "id": snapshot_id},
                    created_at=created_at,
                )

            connection.commit()

        snapshot = self.get_snapshot(snapshot_id)

        return {
            "snapshot": snapshot,
            "action_changed": action_changed,
            "transition_event": transition_event,
            "previous_action": previous.get("action") if previous else None,
            "database": str(self.database_path),
        }

    def _record_transition(
        self,
        *,
        connection: sqlite3.Connection,
        previous: dict[str, Any],
        current: dict[str, Any],
        created_at: str,
    ) -> dict[str, Any]:
        combined_before = self._number_or_none(previous.get("combined_score"))
        combined_after = self._number_or_none(current.get("combined_score"))
        business_before = self._number_or_none(
            previous.get("business_momentum_score")
        )
        business_after = self._number_or_none(
            current.get("business_momentum_score")
        )
        divergence_before = self._number_or_none(
            previous.get("business_divergence_spread")
        )
        divergence_after = self._number_or_none(
            current.get("business_divergence_spread")
        )

        combined_delta = self._delta(combined_before, combined_after)
        business_delta = self._delta(business_before, business_after)
        divergence_delta = self._delta(divergence_before, divergence_after)

        direction = self._transition_direction(
            str(previous.get("action") or "WAIT"),
            str(current.get("action") or "WAIT"),
        )

        primary_driver, driver_detail = self._detect_primary_driver(
            previous=previous,
            current=current,
            combined_delta=combined_delta,
            business_delta=business_delta,
            divergence_delta=divergence_delta,
        )

        metadata = {
            "driver_detail": driver_detail,
            "policy_state": {
                "from": previous.get("policy_state"),
                "to": current.get("policy_state"),
            },
            "timing_gate": {
                "from": previous.get("timing_gate"),
                "to": current.get("timing_gate"),
            },
            "business_regime": {
                "from": previous.get("business_momentum_regime"),
                "to": current.get("business_momentum_regime"),
            },
            "business_trend": {
                "from": previous.get("business_momentum_trend"),
                "to": current.get("business_momentum_trend"),
            },
            "alignment": {
                "from": previous.get("alignment_state"),
                "to": current.get("alignment_state"),
            },
        }

        cursor = connection.execute(
            """
            INSERT INTO qmi_decision_transitions (
                symbol,
                from_action,
                to_action,
                from_snapshot_id,
                to_snapshot_id,
                transition_type,
                transition_direction,
                primary_driver,
                combined_score_before,
                combined_score_after,
                combined_score_delta,
                technical_posture_before,
                technical_posture_after,
                technical_risk_before,
                technical_risk_after,
                fundamental_stance_before,
                fundamental_stance_after,
                business_score_before,
                business_score_after,
                business_score_delta,
                strategic_bias_before,
                strategic_bias_after,
                divergence_state_before,
                divergence_state_after,
                divergence_spread_before,
                divergence_spread_after,
                divergence_spread_delta,
                metadata_json,
                created_at
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                current.get("symbol"),
                previous.get("action"),
                current.get("action"),
                previous.get("id"),
                current.get("id"),
                "ACTION_CHANGE",
                direction,
                primary_driver,
                combined_before,
                combined_after,
                combined_delta,
                previous.get("technical_posture"),
                current.get("technical_posture"),
                previous.get("technical_risk"),
                current.get("technical_risk"),
                previous.get("fundamental_stance"),
                current.get("fundamental_stance"),
                business_before,
                business_after,
                business_delta,
                previous.get("strategic_bias"),
                current.get("strategic_bias"),
                previous.get("business_divergence_state"),
                current.get("business_divergence_state"),
                divergence_before,
                divergence_after,
                divergence_delta,
                json.dumps(metadata),
                created_at,
            ),
        )

        return {
            "id": int(cursor.lastrowid),
            "symbol": current.get("symbol"),
            "from_action": previous.get("action"),
            "to_action": current.get("action"),
            "transition_type": "ACTION_CHANGE",
            "transition_direction": direction,
            "primary_driver": primary_driver,
            "driver_detail": driver_detail,
            "created_at": created_at,
        }

    def _detect_primary_driver(
        self,
        *,
        previous: dict[str, Any],
        current: dict[str, Any],
        combined_delta: float | None,
        business_delta: float | None,
        divergence_delta: float | None,
    ) -> tuple[str, str]:
        changes: list[tuple[str, float, str]] = []

        if previous.get("timing_gate") != current.get("timing_gate"):
            changes.append(
                (
                    "TECHNICAL_TIMING_GATE",
                    100.0,
                    f"Timing gate changed from {previous.get('timing_gate')} "
                    f"to {current.get('timing_gate')}.",
                )
            )

        if previous.get("technical_posture") != current.get("technical_posture"):
            changes.append(
                (
                    "TECHNICAL_POSTURE",
                    95.0,
                    f"Technical posture changed from "
                    f"{previous.get('technical_posture')} to "
                    f"{current.get('technical_posture')}.",
                )
            )

        if previous.get("technical_risk") != current.get("technical_risk"):
            changes.append(
                (
                    "TECHNICAL_RISK",
                    90.0,
                    f"Technical risk changed from {previous.get('technical_risk')} "
                    f"to {current.get('technical_risk')}.",
                )
            )

        if previous.get("fundamental_stance") != current.get("fundamental_stance"):
            changes.append(
                (
                    "FUNDAMENTAL_STANCE",
                    80.0,
                    f"Fundamental stance changed from "
                    f"{previous.get('fundamental_stance')} to "
                    f"{current.get('fundamental_stance')}.",
                )
            )

        if previous.get("business_momentum_trend") != current.get(
            "business_momentum_trend"
        ):
            changes.append(
                (
                    "BUSINESS_MOMENTUM_TREND",
                    75.0,
                    f"Business Momentum trend changed from "
                    f"{previous.get('business_momentum_trend')} to "
                    f"{current.get('business_momentum_trend')}.",
                )
            )

        if previous.get("business_divergence_state") != current.get(
            "business_divergence_state"
        ):
            changes.append(
                (
                    "BUSINESS_DIVERGENCE",
                    70.0,
                    f"Business divergence changed from "
                    f"{previous.get('business_divergence_state')} to "
                    f"{current.get('business_divergence_state')}.",
                )
            )

        if combined_delta is not None and abs(combined_delta) >= 5.0:
            changes.append(
                (
                    "INTEGRATED_SCORE",
                    abs(combined_delta),
                    f"Integrated score moved {combined_delta:+.1f} points.",
                )
            )

        if business_delta is not None and abs(business_delta) >= 5.0:
            changes.append(
                (
                    "BUSINESS_MOMENTUM_SCORE",
                    abs(business_delta),
                    f"Business Momentum moved {business_delta:+.1f} points.",
                )
            )

        if divergence_delta is not None and abs(divergence_delta) >= 10.0:
            changes.append(
                (
                    "DIVERGENCE_SPREAD",
                    abs(divergence_delta) / 2.0,
                    f"Business/technical divergence moved "
                    f"{divergence_delta:+.1f} points.",
                )
            )

        if not changes:
            return (
                "MULTI_FACTOR_REASSESSMENT",
                "Action changed without a single dominant categorical driver.",
            )

        changes.sort(key=lambda item: item[1], reverse=True)
        return changes[0][0], changes[0][2]

    @staticmethod
    def _transition_direction(from_action: str, to_action: str) -> str:
        # Higher value = more constructive / less defensive.
        rank = {
            "EXIT": 0,
            "REDUCE": 1,
            "WAIT": 2,
            "HOLD": 3,
            "ADD": 4,
        }
        before = rank.get(str(from_action).upper(), 2)
        after = rank.get(str(to_action).upper(), 2)

        if after > before:
            return "UPGRADE"
        if after < before:
            return "DOWNGRADE"
        return "LATERAL"

    def latest_snapshot(self, symbol: str) -> dict[str, Any] | None:
        normalized_symbol = symbol.strip().upper()
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT *
                FROM qmi_decision_snapshots
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
                FROM qmi_decision_snapshots
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
                FROM qmi_decision_snapshots
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
                FROM qmi_decision_transitions
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
                FROM qmi_decision_snapshots
                WHERE symbol = ?
                """,
                (normalized_symbol,),
            ).fetchone()["count"]

            transition_count = connection.execute(
                """
                SELECT COUNT(*) AS count
                FROM qmi_decision_transitions
                WHERE symbol = ?
                """,
                (normalized_symbol,),
            ).fetchone()["count"]

            action_rows = connection.execute(
                """
                SELECT action, COUNT(*) AS count
                FROM qmi_decision_snapshots
                WHERE symbol = ?
                GROUP BY action
                ORDER BY count DESC
                """,
                (normalized_symbol,),
            ).fetchall()

        return {
            "symbol": normalized_symbol,
            "latest_snapshot": latest,
            "snapshot_count": int(snapshot_count),
            "transition_count": int(transition_count),
            "action_distribution": {
                row["action"]: int(row["count"])
                for row in action_rows
            },
        }

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

    @staticmethod
    def _delta(before: float | None, after: float | None) -> float | None:
        if before is None or after is None:
            return None
        return round(after - before, 2)
