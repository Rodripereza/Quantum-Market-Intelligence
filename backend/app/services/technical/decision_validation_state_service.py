from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class DecisionValidationStateService:
    """DE-DI-016 — Decision Validation State.

    Persists the validation state produced from DE-DI-015 so QMI can distinguish
    a strengthening decision from a weakening one. Observational only.
    """

    ENGINE_ID = "DE-DI-016"
    VERSION = "0.1.0"

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            db_path = Path(__file__).resolve().parents[3] / "data" / "technical_state_history.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._connect() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS decision_validation_snapshots (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    symbol TEXT NOT NULL,
                    period TEXT NOT NULL,
                    interval TEXT NOT NULL,
                    decision_posture TEXT,
                    validation_state TEXT NOT NULL,
                    evidence_gate TEXT,
                    evidence_score REAL,
                    live_evidence_score REAL,
                    historical_alignment TEXT,
                    historical_maturity TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_decision_validation_symbol_created
                ON decision_validation_snapshots(symbol, created_at DESC)
            """)
            conn.commit()

    def evaluate(
        self,
        *,
        symbol: str,
        period: str,
        interval: str,
        evidence_gate: dict[str, Any] | None,
        persist: bool = True,
    ) -> dict[str, Any]:
        gate = (evidence_gate or {}).get("decision_evidence_gate") or {}
        posture = str(gate.get("decision_posture") or "UNKNOWN").upper()
        gate_state = str(gate.get("gate") or "BLOCKED").upper()
        evidence_score = self._num(gate.get("evidence_score"))
        live_score = self._num(gate.get("live_evidence_score"))
        alignment = str(gate.get("historical_alignment") or "UNAVAILABLE").upper()
        maturity = str(gate.get("historical_maturity") or "INSUFFICIENT_HISTORY").upper()

        validation_state = self._validation_state(gate_state, evidence_score)
        previous = self.latest(symbol=symbol, period=period, interval=interval)
        previous_score = self._num(previous.get("evidence_score")) if previous else None
        delta = evidence_score - previous_score if evidence_score is not None and previous_score is not None else None
        trajectory = self._trajectory(delta)

        recent = self.history(symbol=symbol, period=period, interval=interval, limit=11)
        state_history = [row.get("validation_state") for row in reversed(recent) if row.get("validation_state")]
        if not state_history or state_history[-1] != validation_state:
            state_history.append(validation_state)
        persistence = self._persistence(recent, validation_state) + 1

        response = {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_validation_state": {
                "available": evidence_score is not None,
                "decision_posture": posture,
                "validation_state": validation_state,
                "evidence_gate": gate_state,
                "evidence_score": round(evidence_score, 1) if evidence_score is not None else None,
                "previous_evidence_score": round(previous_score, 1) if previous_score is not None else None,
                "evidence_delta": round(delta, 1) if delta is not None else None,
                "trajectory": trajectory,
                "persistence_snapshots": persistence,
                "historical_alignment": alignment,
                "historical_maturity": maturity,
                "state_history": state_history[-8:],
                "assessment": self._assessment(posture, validation_state, trajectory, persistence),
                "scope": {
                    "observational_only": True,
                    "synthetic_backfill": False,
                    "automatic_decision_changes": False,
                    "automatic_permission_changes": False,
                    "automatic_execution_changes": False,
                },
            },
        }

        if persist and evidence_score is not None:
            self.record(
                symbol=symbol,
                period=period,
                interval=interval,
                posture=posture,
                validation_state=validation_state,
                gate_state=gate_state,
                evidence_score=evidence_score,
                live_score=live_score,
                alignment=alignment,
                maturity=maturity,
            )
        return response

    def record(self, *, symbol, period, interval, posture, validation_state,
               gate_state, evidence_score, live_score, alignment, maturity) -> None:
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            conn.execute("""
                INSERT INTO decision_validation_snapshots (
                    symbol, period, interval, decision_posture, validation_state,
                    evidence_gate, evidence_score, live_evidence_score,
                    historical_alignment, historical_maturity, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                symbol.upper(), period, interval, posture, validation_state,
                gate_state, evidence_score, live_score, alignment, maturity, now,
            ))
            conn.commit()

    def latest(self, *, symbol: str, period: str, interval: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("""
                SELECT * FROM decision_validation_snapshots
                WHERE symbol = ? AND period = ? AND interval = ?
                ORDER BY id DESC LIMIT 1
            """, (symbol.upper(), period, interval)).fetchone()
        return dict(row) if row else None

    def history(self, *, symbol: str, period: str, interval: str, limit: int = 12) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute("""
                SELECT * FROM decision_validation_snapshots
                WHERE symbol = ? AND period = ? AND interval = ?
                ORDER BY id DESC LIMIT ?
            """, (symbol.upper(), period, interval, int(limit))).fetchall()
        return [dict(row) for row in rows]

    @staticmethod
    def _validation_state(gate: str, score: float | None) -> str:
        if gate == "PASSED" and score is not None and score >= 90.0:
            return "STRONGLY_VALIDATED"
        if gate == "PASSED":
            return "VALIDATED"
        if gate == "CONDITIONAL":
            return "CONDITIONAL"
        return "UNVALIDATED"

    @staticmethod
    def _trajectory(delta: float | None) -> str:
        if delta is None:
            return "BASELINE"
        if delta >= 2.0:
            return "STRENGTHENING"
        if delta <= -2.0:
            return "WEAKENING"
        return "STABLE"

    @staticmethod
    def _persistence(rows: list[dict[str, Any]], state: str) -> int:
        count = 0
        for row in rows:
            if row.get("validation_state") != state:
                break
            count += 1
        return count

    @staticmethod
    def _assessment(posture: str, state: str, trajectory: str, persistence: int) -> str:
        p = posture.title()
        state_text = state.replace("_", " ").lower()
        trajectory_text = trajectory.lower()
        if trajectory == "BASELINE":
            return f"{p} establishes its first persisted {state_text} validation baseline."
        return f"{p} is {state_text}; evidence is {trajectory_text} across the latest validation cycle ({persistence} persisted snapshot(s) in the current state)."

    @staticmethod
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None
