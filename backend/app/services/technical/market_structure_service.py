from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class SwingPoint:
    index: int
    date: str
    price: float
    kind: str
    label: str | None = None


class MarketStructureService:
    """
    DE-TA-005.3 — Structural State Machine + Protected Levels

    Core principles:
    - Swings are confirmed only after `pivot_window` bars to the right.
    - No swing is actionable before its confirmation bar.
    - BOS confirms continuation in the active structural direction.
    - CHoCH breaks the protected level against the active structure.
    - Protected Low belongs to bullish structure.
    - Protected High belongs to bearish structure.
    """

    def analyze(
        self,
        history: Iterable[dict[str, Any]],
        pivot_window: int = 3,
        max_swings: int = 20,
    ) -> dict[str, Any]:
        rows = self._normalize_history(history)

        minimum_rows = (pivot_window * 2) + 5
        if len(rows) < minimum_rows:
            raise ValueError(
                f"Not enough historical data. "
                f"Need at least {minimum_rows} observations."
            )

        swings = self._detect_swings(
            rows=rows,
            pivot_window=pivot_window,
        )
        classified = self._classify_swings(swings)

        swing_highs = [
            point for point in classified
            if point.kind == "SWING_HIGH"
        ]
        swing_lows = [
            point for point in classified
            if point.kind == "SWING_LOW"
        ]

        trend = self._classify_trend(
            swing_highs=swing_highs,
            swing_lows=swing_lows,
        )

        state_result = self._run_state_machine(
            rows=rows,
            swings=classified,
            pivot_window=pivot_window,
        )

        events = state_result["events"]
        latest_event = events[-1] if events else None

        validation = self._validate_structure(
            rows=rows,
            trend=trend,
            state_result=state_result,
            swing_highs=swing_highs,
            swing_lows=swing_lows,
            events=events,
            pivot_window=pivot_window,
        )

        latest_high = swing_highs[-1] if swing_highs else None
        previous_high = (
            swing_highs[-2] if len(swing_highs) >= 2 else None
        )
        latest_low = swing_lows[-1] if swing_lows else None
        previous_low = (
            swing_lows[-2] if len(swing_lows) >= 2 else None
        )

        current_close = float(rows[-1]["close"])

        last_bos = next(
            (
                event for event in reversed(events)
                if event["event_family"] == "BOS"
            ),
            None,
        )
        last_choch = next(
            (
                event for event in reversed(events)
                if event["event_family"] == "CHOCH"
            ),
            None,
        )

        return {
            "engine": "QMI Market Structure Engine",
            "engine_id": "DE-TA-005.4",
            "version": "0.4.0",
            "status": "operational",
            "observations": len(rows),
            "pivot_window": pivot_window,
            "confirmation_bars": pivot_window,
            "current_price": round(current_close, 6),
            "trend": trend,
            "structural_state": state_result["state"],
            "protected_levels": {
                "protected_high": self._serialize_point(
                    state_result["protected_high"]
                ),
                "protected_low": self._serialize_point(
                    state_result["protected_low"]
                ),
            },
            "validation": validation,
            "latest_structure": {
                "last_swing_high": self._serialize_point(latest_high),
                "previous_swing_high": self._serialize_point(
                    previous_high
                ),
                "last_swing_low": self._serialize_point(latest_low),
                "previous_swing_low": self._serialize_point(
                    previous_low
                ),
            },
            "counts": {
                "swings": len(classified),
                "swing_highs": len(swing_highs),
                "swing_lows": len(swing_lows),
                "structure_events": len(events),
                "bos": sum(
                    1 for event in events
                    if event["event_family"] == "BOS"
                ),
                "choch": sum(
                    1 for event in events
                    if event["event_family"] == "CHOCH"
                ),
            },
            "latest_event": latest_event,
            "last_bos": last_bos,
            "last_choch": last_choch,
            "events": events[-10:],
            "swings": [
                self._serialize_point(point)
                for point in classified[-max_swings:]
            ],
        }

    def _normalize_history(
        self,
        history: Iterable[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        rows: list[dict[str, Any]] = []

        for item in history:
            if not isinstance(item, dict):
                continue

            date = item.get("date")
            high = item.get("high")
            low = item.get("low")
            close = item.get("close")

            if (
                date is None
                or high is None
                or low is None
                or close is None
            ):
                continue

            try:
                high_value = float(high)
                low_value = float(low)
                close_value = float(close)
            except (TypeError, ValueError):
                continue

            rows.append(
                {
                    "date": str(date),
                    "high": high_value,
                    "low": low_value,
                    "close": close_value,
                }
            )

        rows.sort(key=lambda row: row["date"])

        if not rows:
            raise ValueError("Historical market data is empty.")

        return rows

    def _detect_swings(
        self,
        rows: list[dict[str, Any]],
        pivot_window: int,
    ) -> list[SwingPoint]:
        if pivot_window < 1 or pivot_window > 20:
            raise ValueError(
                "pivot_window must be between 1 and 20."
            )

        swings: list[SwingPoint] = []

        for index in range(
            pivot_window,
            len(rows) - pivot_window,
        ):
            current = rows[index]
            left = rows[index - pivot_window:index]
            right = rows[index + 1:index + pivot_window + 1]

            surrounding_highs = [
                row["high"] for row in left + right
            ]
            surrounding_lows = [
                row["low"] for row in left + right
            ]

            if current["high"] > max(surrounding_highs):
                swings.append(
                    SwingPoint(
                        index=index,
                        date=current["date"],
                        price=current["high"],
                        kind="SWING_HIGH",
                    )
                )

            if current["low"] < min(surrounding_lows):
                swings.append(
                    SwingPoint(
                        index=index,
                        date=current["date"],
                        price=current["low"],
                        kind="SWING_LOW",
                    )
                )

        swings.sort(key=lambda point: point.index)
        return swings

    def _classify_swings(
        self,
        swings: list[SwingPoint],
    ) -> list[SwingPoint]:
        classified: list[SwingPoint] = []
        previous_high: SwingPoint | None = None
        previous_low: SwingPoint | None = None

        for point in swings:
            label: str | None = None

            if point.kind == "SWING_HIGH":
                if previous_high is not None:
                    if point.price > previous_high.price:
                        label = "HH"
                    elif point.price < previous_high.price:
                        label = "LH"
                    else:
                        label = "EH"
                previous_high = point

            elif point.kind == "SWING_LOW":
                if previous_low is not None:
                    if point.price > previous_low.price:
                        label = "HL"
                    elif point.price < previous_low.price:
                        label = "LL"
                    else:
                        label = "EL"
                previous_low = point

            classified.append(
                SwingPoint(
                    index=point.index,
                    date=point.date,
                    price=point.price,
                    kind=point.kind,
                    label=label,
                )
            )

        return classified

    def _classify_trend(
        self,
        swing_highs: list[SwingPoint],
        swing_lows: list[SwingPoint],
    ) -> dict[str, Any]:
        if len(swing_highs) < 2 or len(swing_lows) < 2:
            return {
                "state": "UNDEFINED",
                "bias": "NEUTRAL",
                "confidence": 0,
                "reason": "Insufficient confirmed swing structure.",
            }

        last_high = swing_highs[-1]
        previous_high = swing_highs[-2]
        last_low = swing_lows[-1]
        previous_low = swing_lows[-2]

        high_direction = (
            "HIGHER"
            if last_high.price > previous_high.price
            else "LOWER"
            if last_high.price < previous_high.price
            else "EQUAL"
        )
        low_direction = (
            "HIGHER"
            if last_low.price > previous_low.price
            else "LOWER"
            if last_low.price < previous_low.price
            else "EQUAL"
        )

        if (
            high_direction == "HIGHER"
            and low_direction == "HIGHER"
        ):
            state = "BULLISH"
            bias = "BULLISH"
            confidence = 100
            reason = "Latest confirmed structure is HH + HL."

        elif (
            high_direction == "LOWER"
            and low_direction == "LOWER"
        ):
            state = "BEARISH"
            bias = "BEARISH"
            confidence = 100
            reason = "Latest confirmed structure is LH + LL."

        elif (
            high_direction == "HIGHER"
            and low_direction == "LOWER"
        ):
            state = "EXPANDING_RANGE"
            bias = "NEUTRAL"
            confidence = 60
            reason = (
                "Higher high and lower low indicate "
                "expanding structure."
            )

        elif (
            high_direction == "LOWER"
            and low_direction == "HIGHER"
        ):
            state = "COMPRESSION"
            bias = "NEUTRAL"
            confidence = 60
            reason = (
                "Lower high and higher low indicate "
                "structural compression."
            )

        else:
            state = "RANGE"
            bias = "NEUTRAL"
            confidence = 40
            reason = (
                "Confirmed swings do not define a "
                "directional structure."
            )

        return {
            "state": state,
            "bias": bias,
            "confidence": confidence,
            "high_structure": high_direction,
            "low_structure": low_direction,
            "reason": reason,
        }

    def _run_state_machine(
        self,
        rows: list[dict[str, Any]],
        swings: list[SwingPoint],
        pivot_window: int,
    ) -> dict[str, Any]:
        confirmed_by_index: dict[int, list[SwingPoint]] = {}

        for swing in swings:
            confirmation_index = swing.index + pivot_window

            if confirmation_index >= len(rows):
                continue

            confirmed_by_index.setdefault(
                confirmation_index,
                [],
            ).append(swing)

        confirmed_highs: list[SwingPoint] = []
        confirmed_lows: list[SwingPoint] = []

        latest_high: SwingPoint | None = None
        latest_low: SwingPoint | None = None

        protected_high: SwingPoint | None = None
        protected_low: SwingPoint | None = None

        state = "NEUTRAL"

        broken_highs: set[int] = set()
        broken_lows: set[int] = set()

        events: list[dict[str, Any]] = []

        for index, row in enumerate(rows):
            new_swings = confirmed_by_index.get(index, [])

            for swing in new_swings:
                if swing.kind == "SWING_HIGH":
                    confirmed_highs.append(swing)
                    latest_high = swing

                elif swing.kind == "SWING_LOW":
                    confirmed_lows.append(swing)
                    latest_low = swing

            inferred_state = self._infer_state_from_confirmed_swings(
                confirmed_highs,
                confirmed_lows,
            )

            if state == "NEUTRAL":
                if inferred_state == "BULLISH":
                    state = "BULLISH"
                    protected_low = latest_low

                elif inferred_state == "BEARISH":
                    state = "BEARISH"
                    protected_high = latest_high

            close = float(row["close"])

            # -------------------------------------------------
            # ACTIVE BULLISH STRUCTURE
            # -------------------------------------------------
            if state == "BULLISH":
                if (
                    protected_low is not None
                    and protected_low.index not in broken_lows
                    and index > (
                        protected_low.index + pivot_window
                    )
                    and close < protected_low.price
                ):
                    event = self._build_break_event(
                        event_type="BEARISH_CHOCH",
                        event_family="CHOCH",
                        direction="BEARISH",
                        row=row,
                        index=index,
                        level=protected_low,
                        close=close,
                        prior_state="BULLISH",
                        next_state="BEARISH_TRANSITION",
                    )
                    events.append(event)
                    broken_lows.add(protected_low.index)

                    state = "BEARISH_TRANSITION"
                    protected_high = latest_high
                    protected_low = None
                    continue

                if (
                    latest_high is not None
                    and latest_high.index not in broken_highs
                    and index > (
                        latest_high.index + pivot_window
                    )
                    and close > latest_high.price
                ):
                    event = self._build_break_event(
                        event_type="BULLISH_BOS",
                        event_family="BOS",
                        direction="BULLISH",
                        row=row,
                        index=index,
                        level=latest_high,
                        close=close,
                        prior_state="BULLISH",
                        next_state="BULLISH",
                    )
                    events.append(event)
                    broken_highs.add(latest_high.index)

                    if latest_low is not None:
                        protected_low = latest_low

                    continue

            # -------------------------------------------------
            # ACTIVE BEARISH STRUCTURE
            # -------------------------------------------------
            elif state == "BEARISH":
                if (
                    protected_high is not None
                    and protected_high.index not in broken_highs
                    and index > (
                        protected_high.index + pivot_window
                    )
                    and close > protected_high.price
                ):
                    event = self._build_break_event(
                        event_type="BULLISH_CHOCH",
                        event_family="CHOCH",
                        direction="BULLISH",
                        row=row,
                        index=index,
                        level=protected_high,
                        close=close,
                        prior_state="BEARISH",
                        next_state="BULLISH_TRANSITION",
                    )
                    events.append(event)
                    broken_highs.add(protected_high.index)

                    state = "BULLISH_TRANSITION"
                    protected_low = latest_low
                    protected_high = None
                    continue

                if (
                    latest_low is not None
                    and latest_low.index not in broken_lows
                    and index > (
                        latest_low.index + pivot_window
                    )
                    and close < latest_low.price
                ):
                    event = self._build_break_event(
                        event_type="BEARISH_BOS",
                        event_family="BOS",
                        direction="BEARISH",
                        row=row,
                        index=index,
                        level=latest_low,
                        close=close,
                        prior_state="BEARISH",
                        next_state="BEARISH",
                    )
                    events.append(event)
                    broken_lows.add(latest_low.index)

                    if latest_high is not None:
                        protected_high = latest_high

                    continue

            # -------------------------------------------------
            # BULLISH TRANSITION AFTER BULLISH CHoCH
            # -------------------------------------------------
            elif state == "BULLISH_TRANSITION":
                if (
                    latest_high is not None
                    and latest_high.index not in broken_highs
                    and index > (
                        latest_high.index + pivot_window
                    )
                    and close > latest_high.price
                ):
                    event = self._build_break_event(
                        event_type="BULLISH_BOS",
                        event_family="BOS",
                        direction="BULLISH",
                        row=row,
                        index=index,
                        level=latest_high,
                        close=close,
                        prior_state="BULLISH_TRANSITION",
                        next_state="BULLISH",
                    )
                    events.append(event)
                    broken_highs.add(latest_high.index)

                    state = "BULLISH"
                    protected_low = latest_low
                    protected_high = None
                    continue

                if inferred_state == "BEARISH":
                    state = "BEARISH"
                    protected_high = latest_high

            # -------------------------------------------------
            # BEARISH TRANSITION AFTER BEARISH CHoCH
            # -------------------------------------------------
            elif state == "BEARISH_TRANSITION":
                if (
                    latest_low is not None
                    and latest_low.index not in broken_lows
                    and index > (
                        latest_low.index + pivot_window
                    )
                    and close < latest_low.price
                ):
                    event = self._build_break_event(
                        event_type="BEARISH_BOS",
                        event_family="BOS",
                        direction="BEARISH",
                        row=row,
                        index=index,
                        level=latest_low,
                        close=close,
                        prior_state="BEARISH_TRANSITION",
                        next_state="BEARISH",
                    )
                    events.append(event)
                    broken_lows.add(latest_low.index)

                    state = "BEARISH"
                    protected_high = latest_high
                    protected_low = None
                    continue

                if inferred_state == "BULLISH":
                    state = "BULLISH"
                    protected_low = latest_low

        return {
            "state": state,
            "protected_high": protected_high,
            "protected_low": protected_low,
            "events": events,
        }

    def _infer_state_from_confirmed_swings(
        self,
        highs: list[SwingPoint],
        lows: list[SwingPoint],
    ) -> str:
        if len(highs) < 2 or len(lows) < 2:
            return "NEUTRAL"

        high_up = highs[-1].price > highs[-2].price
        high_down = highs[-1].price < highs[-2].price
        low_up = lows[-1].price > lows[-2].price
        low_down = lows[-1].price < lows[-2].price

        if high_up and low_up:
            return "BULLISH"

        if high_down and low_down:
            return "BEARISH"

        return "NEUTRAL"

    def _validate_structure(
        self,
        rows: list[dict[str, Any]],
        trend: dict[str, Any],
        state_result: dict[str, Any],
        swing_highs: list[SwingPoint],
        swing_lows: list[SwingPoint],
        events: list[dict[str, Any]],
        pivot_window: int,
    ) -> dict[str, Any]:
        """
        DE-TA-005.4 quality layer.

        Produces an explainable 0-100 structural quality score.
        It does not change direction; it measures confidence in the
        market-structure interpretation.
        """
        current_index = len(rows) - 1
        current_price = float(rows[-1]["close"])
        structural_state = state_result["state"]

        protected_high = state_result["protected_high"]
        protected_low = state_result["protected_low"]
        active_protected = (
            protected_low
            if structural_state in {"BULLISH", "BULLISH_TRANSITION"}
            else protected_high
            if structural_state in {"BEARISH", "BEARISH_TRANSITION"}
            else None
        )

        # 1) Structural clarity: HH+HL or LH+LL is stronger than mixed structure.
        trend_state = str(trend.get("state", "UNDEFINED"))
        if trend_state in {"BULLISH", "BEARISH"}:
            clarity_score = 100.0
        elif trend_state in {"COMPRESSION", "EXPANDING_RANGE"}:
            clarity_score = 55.0
        elif trend_state == "RANGE":
            clarity_score = 40.0
        else:
            clarity_score = 20.0

        # 2) Swing recency: stale pivots should reduce confidence.
        latest_swing_index = max(
            [
                point.index
                for point in (
                    (swing_highs[-1:] if swing_highs else [])
                    + (swing_lows[-1:] if swing_lows else [])
                )
            ],
            default=0,
        )
        bars_since_latest_swing = max(
            0,
            current_index - latest_swing_index,
        )
        if bars_since_latest_swing <= pivot_window + 5:
            recency_score = 100.0
        elif bars_since_latest_swing <= 20:
            recency_score = 80.0
        elif bars_since_latest_swing <= 40:
            recency_score = 60.0
        elif bars_since_latest_swing <= 70:
            recency_score = 40.0
        else:
            recency_score = 20.0

        # 3) Protected level quality: active, not excessively stale,
        # and not absurdly far from current price.
        protected_age_bars = None
        protected_distance_pct = None

        if active_protected is None:
            protected_score = 35.0
        else:
            protected_age_bars = max(
                0,
                current_index - active_protected.index,
            )
            protected_distance_pct = (
                abs(current_price - active_protected.price)
                / active_protected.price
                * 100
                if active_protected.price
                else None
            )

            age_score = (
                100.0
                if protected_age_bars <= 20
                else 80.0
                if protected_age_bars <= 40
                else 60.0
                if protected_age_bars <= 70
                else 35.0
            )

            if protected_distance_pct is None:
                distance_score = 50.0
            elif protected_distance_pct <= 8:
                distance_score = 100.0
            elif protected_distance_pct <= 15:
                distance_score = 85.0
            elif protected_distance_pct <= 25:
                distance_score = 65.0
            elif protected_distance_pct <= 40:
                distance_score = 45.0
            else:
                distance_score = 25.0

            protected_score = (
                age_score * 0.55
                + distance_score * 0.45
            )

        # 4) Event consistency: recent BOS should generally agree
        # with the active state; recent CHoCH is acceptable but signals transition.
        recent_events = events[-6:]
        aligned_events = 0
        contradictory_events = 0

        active_direction = (
            "BULLISH"
            if structural_state.startswith("BULLISH")
            else "BEARISH"
            if structural_state.startswith("BEARISH")
            else "NEUTRAL"
        )

        for event in recent_events:
            direction = event.get("direction")
            family = event.get("event_family")

            if active_direction == "NEUTRAL":
                continue

            if direction == active_direction:
                aligned_events += 1
            elif family == "CHOCH":
                contradictory_events += 1

        if not recent_events:
            event_score = 50.0
        else:
            event_score = max(
                20.0,
                min(
                    100.0,
                    65.0
                    + aligned_events * 8.0
                    - contradictory_events * 10.0,
                ),
            )

        # 5) State stability: transition states deliberately carry lower quality.
        if structural_state in {"BULLISH", "BEARISH"}:
            stability_score = 100.0
        elif structural_state in {
            "BULLISH_TRANSITION",
            "BEARISH_TRANSITION",
        }:
            stability_score = 60.0
        else:
            stability_score = 35.0

        score = (
            clarity_score * 0.25
            + recency_score * 0.20
            + protected_score * 0.25
            + event_score * 0.15
            + stability_score * 0.15
        )
        score = round(max(0.0, min(100.0, score)), 1)

        if score >= 85:
            label = "VERY_HIGH"
        elif score >= 70:
            label = "HIGH"
        elif score >= 55:
            label = "MODERATE"
        elif score >= 40:
            label = "LOW"
        else:
            label = "VERY_LOW"

        warnings: list[str] = []

        if active_protected is None:
            warnings.append(
                "No active protected structural level."
            )

        if protected_age_bars is not None and protected_age_bars > 70:
            warnings.append(
                "Protected level is structurally stale."
            )

        if (
            protected_distance_pct is not None
            and protected_distance_pct > 25
        ):
            warnings.append(
                "Protected level is far from current price."
            )

        if structural_state.endswith("TRANSITION"):
            warnings.append(
                "Structure is in transition; directional confidence is reduced."
            )

        if trend_state not in {"BULLISH", "BEARISH"}:
            warnings.append(
                "Latest swing geometry is not fully directional."
            )

        return {
            "score": score,
            "label": label,
            "is_decision_ready": score >= 70
            and structural_state in {"BULLISH", "BEARISH"},
            "components": {
                "clarity": round(clarity_score, 1),
                "swing_recency": round(recency_score, 1),
                "protected_level_quality": round(
                    protected_score,
                    1,
                ),
                "event_consistency": round(event_score, 1),
                "state_stability": round(stability_score, 1),
            },
            "diagnostics": {
                "bars_since_latest_swing": bars_since_latest_swing,
                "protected_level_age_bars": protected_age_bars,
                "protected_level_distance_pct": (
                    round(protected_distance_pct, 2)
                    if protected_distance_pct is not None
                    else None
                ),
                "recent_events_analyzed": len(recent_events),
                "aligned_recent_events": aligned_events,
                "contradictory_recent_events": contradictory_events,
            },
            "warnings": warnings,
        }

    def _build_break_event(
        self,
        event_type: str,
        event_family: str,
        direction: str,
        row: dict[str, Any],
        index: int,
        level: SwingPoint,
        close: float,
        prior_state: str,
        next_state: str,
    ) -> dict[str, Any]:
        distance = abs(close - level.price)
        distance_pct = (
            (distance / level.price) * 100
            if level.price != 0
            else 0.0
        )

        confidence = min(
            95.0,
            72.0 + min(distance_pct * 8.0, 23.0),
        )

        return {
            "index": index,
            "date": row["date"],
            "type": event_type,
            "event_family": event_family,
            "direction": direction,
            "prior_state": prior_state,
            "next_state": next_state,
            "broken_level": round(float(level.price), 6),
            "broken_level_date": level.date,
            "broken_level_kind": level.kind,
            "broken_level_label": level.label,
            "confirmation_price": round(close, 6),
            "break_distance": round(distance, 6),
            "break_distance_pct": round(distance_pct, 3),
            "confirmation": "CLOSE",
            "confidence": round(confidence, 1),
        }

    @staticmethod
    def _serialize_point(
        point: SwingPoint | None,
    ) -> dict[str, Any] | None:
        if point is None:
            return None

        return {
            "index": point.index,
            "date": point.date,
            "price": round(float(point.price), 6),
            "kind": point.kind,
            "label": point.label,
        }
