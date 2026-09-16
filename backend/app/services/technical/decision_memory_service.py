from __future__ import annotations

from math import sqrt
from typing import Any


class DecisionMemoryService:
    """DE-DI-010 — Decision Memory Engine.

    Finds historically persisted technical configurations similar to the current
    configuration. Advisory/contextual only: no weight, threshold, posture or
    execution changes are made by this service.
    """

    ENGINE_ID = "DE-DI-010"
    VERSION = "0.1.1"
    MIN_SIMILARITY = 70.0
    MAX_MATCHES = 5

    STATE_KEYS = (
        "direction_score",
        "transition_readiness_score",
        "next_state_probability",
        "risk_score",
    )
    DRIVER_KEYS = (
        "structure",
        "trend",
        "liquidity",
        "strength",
        "support_resistance",
        "momentum",
        "volume",
    )

    def analyze(
        self,
        *,
        current_state: dict[str, Any] | None,
        current_drivers: list[dict[str, Any]] | None,
        state_history: list[dict[str, Any]] | None,
        driver_history: list[dict[str, Any]] | None,
    ) -> dict[str, Any]:
        current_driver_rows = self._unwrap_drivers(current_drivers)
        current_vector = self._vector(current_state or {}, current_driver_rows)
        if not current_vector:
            return self._empty("Current technical vector is unavailable.")

        states = [x for x in (state_history or []) if x and x.get("id") is not None]
        drivers_by_snapshot = self._drivers_by_snapshot(driver_history or [])
        candidates = []

        current_id = (current_state or {}).get("id")
        for row in states:
            if current_id is not None and row.get("id") == current_id:
                continue
            vector = self._vector(
                row,
                drivers_by_snapshot.get(str(row.get("created_at") or ""), []),
            )
            common = sorted(set(current_vector) & set(vector))
            if len(common) < 4:
                continue

            similarity = self._similarity(current_vector, vector, common)
            if similarity < self.MIN_SIMILARITY:
                continue

            candidates.append({
                "snapshot_id": row.get("id"),
                "created_at": row.get("created_at"),
                "similarity_score": round(similarity, 1),
                "common_dimensions": len(common),
                "state": row.get("state"),
                "decision_posture": row.get("decision_posture"),
                "direction_score": self._num(row.get("direction_score")),
                "risk_score": self._num(row.get("risk_score")),
                "current_price": self._num(row.get("current_price")),
            })

        candidates.sort(key=lambda x: x["similarity_score"], reverse=True)
        matches = candidates[: self.MAX_MATCHES]

        readiness = (
            "INSUFFICIENT_HISTORY" if not matches
            else "EARLY" if len(matches) < 3
            else "DEVELOPING" if len(matches) < 5
            else "MATURE"
        )
        avg_similarity = (
            round(sum(x["similarity_score"] for x in matches) / len(matches), 1)
            if matches else None
        )

        posture_counts: dict[str, int] = {}
        for item in matches:
            posture = str(item.get("decision_posture") or "UNKNOWN").upper()
            posture_counts[posture] = posture_counts.get(posture, 0) + 1
        dominant_posture = (
            max(posture_counts, key=posture_counts.get) if posture_counts else None
        )

        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_memory": {
                "available": bool(matches),
                "readiness": readiness,
                "minimum_similarity": self.MIN_SIMILARITY,
                "matches_found": len(matches),
                "average_similarity": avg_similarity,
                "dominant_historical_posture": dominant_posture,
                "matches": matches,
                "summary": self._summary(matches, avg_similarity, dominant_posture),
                "scope": {
                    "persisted_observations_only": True,
                    "synthetic_backfill": False,
                    "automatic_weight_changes": False,
                    "automatic_decision_changes": False,
                    "automatic_execution_changes": False,
                    "contextual_evidence_only": True,
                },
            },
        }

    def _vector(self, state: dict[str, Any], drivers: list[dict[str, Any]]):
        vector: dict[str, float] = {}
        for key in self.STATE_KEYS:
            value = self._num(state.get(key))
            if value is not None:
                vector[key] = value

        for driver in drivers:
            if not isinstance(driver, dict):
                continue
            name = self._driver_name(driver)
            if name not in self.DRIVER_KEYS:
                continue
            value = self._num(driver.get("score"))
            if value is None:
                value = self._num(driver.get("normalized_score"))
            if value is not None:
                vector[f"driver:{name}"] = value
        return vector

    @staticmethod
    def _similarity(a, b, common):
        # All QMI technical dimensions are approximately normalized to a
        # -100..+100 / 0..100 scale. Convert RMS distance into 0..100 similarity.
        squared = [(a[k] - b[k]) ** 2 for k in common]
        rms = sqrt(sum(squared) / len(squared))
        return max(0.0, min(100.0, 100.0 - (rms / 2.0)))

    def _drivers_by_snapshot(self, rows):
        grouped: dict[str, list[dict[str, Any]]] = {}
        for snapshot in rows:
            if not isinstance(snapshot, dict):
                continue
            created_at = str(snapshot.get("created_at") or "")
            drivers = snapshot.get("drivers") or []
            if created_at and isinstance(drivers, list):
                grouped[created_at] = [d for d in drivers if isinstance(d, dict)]
        return grouped

    @staticmethod
    def _unwrap_drivers(value):
        if isinstance(value, dict):
            drivers = value.get("drivers") or []
            return [d for d in drivers if isinstance(d, dict)] if isinstance(drivers, list) else []
        if isinstance(value, list):
            return [d for d in value if isinstance(d, dict)]
        return []

    @staticmethod
    def _driver_name(row):
        raw = str(row.get("engine") or row.get("driver") or row.get("name") or "")
        name = raw.strip().lower().replace("/", "_").replace(" ", "_").replace("-", "_")
        aliases = {
            "supportresistance": "support_resistance",
            "support_resistance": "support_resistance",
            "support_&_resistance": "support_resistance",
        }
        return aliases.get(name, name)

    @staticmethod
    def _summary(matches, average, posture):
        if not matches:
            return "No sufficiently similar persisted technical configuration is available yet."
        return (
            f"{len(matches)} similar persisted configuration(s) found with "
            f"{average:.1f}% average similarity. "
            f"Dominant historical posture: {posture or 'Unknown'}."
        )

    def _empty(self, reason):
        return {
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "decision_memory": {
                "available": False,
                "readiness": "INSUFFICIENT_HISTORY",
                "minimum_similarity": self.MIN_SIMILARITY,
                "matches_found": 0,
                "average_similarity": None,
                "dominant_historical_posture": None,
                "matches": [],
                "summary": reason,
                "scope": {
                    "persisted_observations_only": True,
                    "synthetic_backfill": False,
                    "automatic_decision_changes": False,
                    "contextual_evidence_only": True,
                },
            },
        }

    @staticmethod
    def _num(value):
        try:
            return None if value is None else float(value)
        except (TypeError, ValueError):
            return None
