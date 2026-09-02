from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any

from app.services.qmi_decision_history_service import QMIDecisionHistoryService


class QMIHistoricalReconstructionService:
    """
    DE-CORE-006.3 — Historical State Reconstruction

    Read-only reconstruction of QMI temporal state from persisted snapshots.
    """

    ENGINE = "QMI Historical State Reconstruction"
    ENGINE_ID = "DE-CORE-006.3.1"
    VERSION = "0.1.1"

    ACTION_RANK = {
        "EXIT": 0,
        "REDUCE": 1,
        "WAIT": 2,
        "HOLD": 3,
        "ADD": 4,
    }

    def __init__(self, history_service: QMIDecisionHistoryService | None = None) -> None:
        self.history_service = history_service or QMIDecisionHistoryService()

    def reconstruct(self, symbol: str, *, limit: int = 500) -> dict[str, Any]:
        normalized_symbol = symbol.strip().upper()
        limit = max(1, min(int(limit), 1000))

        raw_history = self.history_service.history(normalized_symbol, limit=limit)
        raw_transitions = self.history_service.transitions(normalized_symbol, limit=limit)

        snapshots = list(reversed(raw_history))
        transitions = list(reversed(raw_transitions))

        episodes = self._build_action_episodes(snapshots)

        return {
            "symbol": normalized_symbol,
            "engine": self.ENGINE,
            "engine_id": self.ENGINE_ID,
            "version": self.VERSION,
            "status": "operational",
            "history_window": {
                "requested_limit": limit,
                "snapshot_count": len(snapshots),
                "transition_count": len(transitions),
                "episode_count": len(episodes),
                "first_snapshot_at": snapshots[0].get("created_at") if snapshots else None,
                "latest_snapshot_at": snapshots[-1].get("created_at") if snapshots else None,
            },
            "current_state": self._current_state(episodes),
            "trajectory": self._trajectory(episodes),
            "state_distribution": self._state_distribution(episodes),
            "episodes": episodes,
            "transitions": self._enrich_transitions(transitions, episodes),
            "transition_intelligence": self._transition_intelligence(
                transitions=self._enrich_transitions(transitions, episodes),
                episodes=episodes,
            ),
        }

    def _build_action_episodes(self, snapshots: list[dict[str, Any]]) -> list[dict[str, Any]]:
        if not snapshots:
            return []

        groups: list[list[dict[str, Any]]] = []
        current: list[dict[str, Any]] = []

        for snapshot in snapshots:
            action = self._upper(snapshot.get("action")) or "WAIT"
            if not current:
                current = [snapshot]
                continue

            current_action = self._upper(current[-1].get("action")) or "WAIT"
            if action == current_action:
                current.append(snapshot)
            else:
                groups.append(current)
                current = [snapshot]

        if current:
            groups.append(current)

        return [
            self._episode_from_group(index, group)
            for index, group in enumerate(groups, start=1)
        ]

    def _episode_from_group(self, episode_number: int, group: list[dict[str, Any]]) -> dict[str, Any]:
        first = group[0]
        last = group[-1]

        start_dt = self._parse_datetime(first.get("created_at"))
        end_dt = self._parse_datetime(last.get("created_at"))

        duration_hours = None
        if start_dt and end_dt:
            duration_hours = round(
                max((end_dt - start_dt).total_seconds(), 0.0) / 3600.0,
                2,
            )

        return {
            "episode": episode_number,
            "action": self._upper(last.get("action")) or "WAIT",
            "snapshot_count": len(group),
            "start_snapshot_id": first.get("id"),
            "end_snapshot_id": last.get("id"),
            "started_at": first.get("created_at"),
            "ended_at": last.get("created_at"),
            "duration_hours_observed": duration_hours,
            "duration_days_observed": round(duration_hours / 24.0, 3) if duration_hours is not None else None,
            "state": {
                "policy_state": self._upper(last.get("policy_state")),
                "strategic_bias": self._upper(last.get("strategic_bias")),
                "integrated_posture": self._upper(last.get("integrated_posture")),
                "timing_gate": self._upper(last.get("timing_gate")),
                "technical_posture": self._upper(last.get("technical_posture")),
                "technical_risk": self._upper(last.get("technical_risk")),
                "technical_timing": self._upper(last.get("technical_timing")),
                "fundamental_stance": self._upper(last.get("fundamental_stance")),
                "business_regime": self._upper(last.get("business_momentum_regime")),
                "business_trend": self._upper(last.get("business_momentum_trend")),
                "divergence_state": self._upper(last.get("business_divergence_state")),
                "divergence_severity": self._upper(last.get("business_divergence_severity")),
                "alignment_state": self._upper(last.get("alignment_state")),
            },
            "score_evolution": {
                "combined": self._metric_evolution(first.get("combined_score"), last.get("combined_score")),
                "business_momentum": self._metric_evolution(first.get("business_momentum_score"), last.get("business_momentum_score")),
                "business_divergence": self._metric_evolution(first.get("business_divergence_spread"), last.get("business_divergence_spread")),
            },
            "internal_changes": self._episode_internal_changes(group),
        }

    def _episode_internal_changes(self, group: list[dict[str, Any]]) -> dict[str, Any]:
        fields = (
            "strategic_bias",
            "policy_state",
            "integrated_posture",
            "timing_gate",
            "technical_posture",
            "technical_risk",
            "technical_timing",
            "fundamental_stance",
            "business_momentum_regime",
            "business_momentum_trend",
            "business_divergence_state",
            "business_divergence_severity",
            "alignment_state",
        )

        changed = []
        for field in fields:
            values = [self._upper(item.get(field)) for item in group]
            values = [v for v in values if v is not None]
            compact = []
            for value in values:
                if not compact or compact[-1] != value:
                    compact.append(value)
            if len(compact) > 1:
                changed.append({"field": field, "sequence": compact})

        return {"count": len(changed), "fields": changed}

    def _enrich_transitions(self, transitions: list[dict[str, Any]], episodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
        boundaries = {}
        for index in range(1, len(episodes)):
            before = episodes[index - 1]
            after = episodes[index]
            boundaries[(before.get("end_snapshot_id"), after.get("start_snapshot_id"))] = {
                "from_episode": before.get("episode"),
                "to_episode": after.get("episode"),
                "from_duration_hours_observed": before.get("duration_hours_observed"),
                "from_snapshot_count": before.get("snapshot_count"),
                "to_snapshot_count": after.get("snapshot_count"),
            }

        result = []
        for transition in transitions:
            item = dict(transition)
            key = (item.get("from_snapshot_id"), item.get("to_snapshot_id"))
            item["episode_context"] = boundaries.get(key)
            item["transition_strength"] = self._transition_strength(item)
            result.append(item)
        return result

    def _transition_strength(self, transition: dict[str, Any]) -> str:
        combined = abs(self._number_or_none(transition.get("combined_score_delta")) or 0.0)
        business = abs(self._number_or_none(transition.get("business_score_delta")) or 0.0)
        divergence = abs(self._number_or_none(transition.get("divergence_spread_delta")) or 0.0) / 2.0
        magnitude = max(combined, business, divergence)

        if magnitude >= 15:
            return "HIGH"
        if magnitude >= 7:
            return "MEDIUM"
        return "LOW"

    def transition_intelligence(
        self,
        symbol: str,
        *,
        limit: int = 500,
    ) -> dict[str, Any]:
        """
        DE-CORE-006.3.1 — State Transition Intelligence

        Dedicated read-only view focused on WHY QMI changed action.
        """
        reconstructed = self.reconstruct(symbol, limit=limit)

        return {
            "symbol": reconstructed.get("symbol"),
            "engine": "QMI State Transition Intelligence",
            "engine_id": "DE-CORE-006.3.1",
            "version": self.VERSION,
            "status": "operational",
            "current_state": reconstructed.get("current_state"),
            "trajectory": reconstructed.get("trajectory"),
            "history_window": reconstructed.get("history_window"),
            "transition_intelligence": reconstructed.get(
                "transition_intelligence"
            ),
        }

    def _transition_intelligence(
        self,
        *,
        transitions: list[dict[str, Any]],
        episodes: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not transitions:
            current = episodes[-1] if episodes else None
            return {
                "available": False,
                "transition_count": 0,
                "latest_transition": None,
                "transition_sequence": [],
                "dominant_driver": None,
                "current_episode": (
                    {
                        "episode": current.get("episode"),
                        "action": current.get("action"),
                        "snapshot_count": current.get("snapshot_count"),
                        "duration_hours_observed": current.get(
                            "duration_hours_observed"
                        ),
                    }
                    if current
                    else None
                ),
                "interpretation": (
                    "No action transition has been recorded yet. "
                    "QMI remains inside the current decision episode."
                    if current
                    else "No historical decision state is available."
                ),
            }

        intelligent = [
            self._transition_analysis(item)
            for item in transitions
        ]

        driver_counts = Counter(
            item.get("primary_driver")
            for item in intelligent
            if item.get("primary_driver")
        )
        dominant_driver = (
            driver_counts.most_common(1)[0][0]
            if driver_counts
            else None
        )

        latest = intelligent[-1]

        return {
            "available": True,
            "transition_count": len(intelligent),
            "latest_transition": latest,
            "transition_sequence": [
                {
                    "from_action": item.get("from_action"),
                    "to_action": item.get("to_action"),
                    "direction": item.get("transition_direction"),
                    "primary_driver": item.get("primary_driver"),
                    "created_at": item.get("created_at"),
                }
                for item in intelligent
            ],
            "dominant_driver": dominant_driver,
            "current_episode": (
                {
                    "episode": episodes[-1].get("episode"),
                    "action": episodes[-1].get("action"),
                    "snapshot_count": episodes[-1].get("snapshot_count"),
                    "duration_hours_observed": episodes[-1].get(
                        "duration_hours_observed"
                    ),
                }
                if episodes
                else None
            ),
            "interpretation": self._latest_transition_interpretation(latest),
        }

    def _transition_analysis(
        self,
        transition: dict[str, Any],
    ) -> dict[str, Any]:
        combined_delta = self._number_or_none(
            transition.get("combined_score_delta")
        )
        business_delta = self._number_or_none(
            transition.get("business_score_delta")
        )
        divergence_delta = self._number_or_none(
            transition.get("divergence_spread_delta")
        )

        technical_change = (
            self._upper(transition.get("technical_posture_before"))
            != self._upper(transition.get("technical_posture_after"))
            or self._upper(transition.get("technical_risk_before"))
            != self._upper(transition.get("technical_risk_after"))
        )

        fundamental_change = (
            self._upper(transition.get("fundamental_stance_before"))
            != self._upper(transition.get("fundamental_stance_after"))
        )

        business_change = bool(
            business_delta is not None and abs(business_delta) >= 5.0
        )

        divergence_change = bool(
            divergence_delta is not None and abs(divergence_delta) >= 10.0
        )

        driver_family = self._driver_family(
            transition.get("primary_driver")
        )

        confirmation = self._confirmation_profile(
            direction=transition.get("transition_direction"),
            technical_change=technical_change,
            fundamental_change=fundamental_change,
            business_change=business_change,
            divergence_change=divergence_change,
            combined_delta=combined_delta,
        )

        return {
            **transition,
            "driver_family": driver_family,
            "metric_changes": {
                "combined_score_delta": combined_delta,
                "business_momentum_delta": business_delta,
                "divergence_spread_delta": divergence_delta,
            },
            "state_changes": {
                "technical_changed": technical_change,
                "fundamental_changed": fundamental_change,
                "business_materially_changed": business_change,
                "divergence_materially_changed": divergence_change,
            },
            "confirmation_profile": confirmation,
            "interpretation": self._build_transition_interpretation(
                transition=transition,
                driver_family=driver_family,
                confirmation=confirmation,
            ),
        }

    @staticmethod
    def _driver_family(primary_driver: Any) -> str:
        value = str(primary_driver or "").upper()

        if value.startswith("TECHNICAL"):
            return "TECHNICAL"
        if value.startswith("FUNDAMENTAL"):
            return "FUNDAMENTAL"
        if value.startswith("BUSINESS"):
            return "BUSINESS"
        if value.startswith("DIVERGENCE"):
            return "BUSINESS_DIVERGENCE"
        if value.startswith("INTEGRATED") or value.startswith("MULTI_FACTOR"):
            return "CROSS_ENGINE"

        return "UNKNOWN"

    def _confirmation_profile(
        self,
        *,
        direction: Any,
        technical_change: bool,
        fundamental_change: bool,
        business_change: bool,
        divergence_change: bool,
        combined_delta: float | None,
    ) -> dict[str, Any]:
        direction_value = self._upper(direction)

        supporting_families = sum(
            1
            for flag in (
                technical_change,
                fundamental_change,
                business_change,
                divergence_change,
            )
            if flag
        )

        if supporting_families >= 3:
            breadth = "BROAD"
        elif supporting_families == 2:
            breadth = "MULTI_FACTOR"
        elif supporting_families == 1:
            breadth = "SINGLE_FACTOR"
        else:
            breadth = "LOW_SIGNAL"

        score_confirmation = "NEUTRAL"
        if combined_delta is not None:
            if combined_delta >= 5:
                score_confirmation = "POSITIVE"
            elif combined_delta <= -5:
                score_confirmation = "NEGATIVE"

        aligned = (
            direction_value == "UPGRADE"
            and score_confirmation == "POSITIVE"
        ) or (
            direction_value == "DOWNGRADE"
            and score_confirmation == "NEGATIVE"
        )

        return {
            "breadth": breadth,
            "supporting_factor_count": supporting_families,
            "score_confirmation": score_confirmation,
            "direction_score_aligned": aligned,
        }

    def _build_transition_interpretation(
        self,
        *,
        transition: dict[str, Any],
        driver_family: str,
        confirmation: dict[str, Any],
    ) -> str:
        from_action = self._upper(transition.get("from_action")) or "UNKNOWN"
        to_action = self._upper(transition.get("to_action")) or "UNKNOWN"
        direction = self._upper(
            transition.get("transition_direction")
        ) or "LATERAL"

        driver = self._upper(
            transition.get("primary_driver")
        ) or "MULTI_FACTOR_REASSESSMENT"

        breadth = confirmation.get("breadth")
        aligned = confirmation.get("direction_score_aligned")

        sentence = (
            f"QMI transitioned from {from_action} to {to_action} "
            f"({direction}). Primary driver: {driver} "
            f"[{driver_family}]. Confirmation breadth: {breadth}."
        )

        if aligned:
            sentence += " Integrated-score movement confirms the transition direction."
        else:
            sentence += " Integrated-score confirmation is limited or mixed."

        return sentence

    @staticmethod
    def _latest_transition_interpretation(
        latest: dict[str, Any],
    ) -> str:
        return (
            latest.get("interpretation")
            or "Latest QMI transition reconstructed successfully."
        )

    def _current_state(self, episodes: list[dict[str, Any]]) -> dict[str, Any] | None:
        if not episodes:
            return None

        latest = episodes[-1]
        return {
            "episode": latest.get("episode"),
            "action": latest.get("action"),
            "started_at": latest.get("started_at"),
            "latest_observation_at": latest.get("ended_at"),
            "snapshot_count": latest.get("snapshot_count"),
            "duration_hours_observed": latest.get("duration_hours_observed"),
            "state": latest.get("state"),
            "score_evolution": latest.get("score_evolution"),
        }

    def _trajectory(self, episodes: list[dict[str, Any]]) -> dict[str, Any]:
        if not episodes:
            return {
                "classification": "NO_HISTORY",
                "episode_actions": [],
                "net_action_change": 0,
            }

        actions = [episode.get("action") for episode in episodes]
        first_rank = self.ACTION_RANK.get(actions[0], 2)
        last_rank = self.ACTION_RANK.get(actions[-1], 2)
        net_change = last_rank - first_rank

        if len(actions) == 1:
            classification = "STABLE"
        elif net_change >= 2:
            classification = "STRONG_IMPROVEMENT"
        elif net_change == 1:
            classification = "IMPROVING"
        elif net_change <= -2:
            classification = "STRONG_DETERIORATION"
        elif net_change == -1:
            classification = "DETERIORATING"
        else:
            classification = "CYCLICAL_OR_STABLE"

        return {
            "classification": classification,
            "episode_actions": actions,
            "net_action_change": net_change,
            "first_action": actions[0],
            "current_action": actions[-1],
        }

    def _state_distribution(self, episodes: list[dict[str, Any]]) -> dict[str, Any]:
        if not episodes:
            return {
                "episode_counts": {},
                "snapshot_counts": {},
                "observed_hours": {},
                "dominant_action_by_snapshots": None,
            }

        episode_counts = Counter(episode.get("action") for episode in episodes)
        snapshot_counts = defaultdict(int)
        observed_hours = defaultdict(float)

        for episode in episodes:
            action = episode.get("action") or "UNKNOWN"
            snapshot_counts[action] += int(episode.get("snapshot_count") or 0)
            observed_hours[action] += float(episode.get("duration_hours_observed") or 0.0)

        dominant_action = max(snapshot_counts.items(), key=lambda item: item[1])[0]

        return {
            "episode_counts": dict(episode_counts),
            "snapshot_counts": dict(snapshot_counts),
            "observed_hours": {k: round(v, 2) for k, v in observed_hours.items()},
            "dominant_action_by_snapshots": dominant_action,
        }

    @classmethod
    def _metric_evolution(cls, start: Any, end: Any) -> dict[str, float | None]:
        start_number = cls._number_or_none(start)
        end_number = cls._number_or_none(end)
        delta = None
        if start_number is not None and end_number is not None:
            delta = round(end_number - start_number, 2)
        return {"start": start_number, "end": end_number, "delta": delta}

    @staticmethod
    def _parse_datetime(value: Any) -> datetime | None:
        if not value:
            return None
        try:
            parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        except ValueError:
            return None
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)

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
