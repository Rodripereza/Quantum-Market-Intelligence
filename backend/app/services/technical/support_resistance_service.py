from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable


@dataclass(frozen=True)
class Pivot:
    index: int
    date: str
    price: float
    kind: str
    reaction_pct: float


class SupportResistanceService:
    """
    DE-TA-006.1 — Support & Resistance Zones

    Detects confirmed pivot highs/lows and clusters them into price zones.
    The engine returns zones, strength/quality, touches, recency and
    distance from current price.

    This phase does NOT generate trading signals. It describes where
    structurally relevant supply/demand areas are located.
    """

    def analyze(
        self,
        history: Iterable[dict[str, Any]],
        pivot_window: int = 3,
        min_touches: int = 2,
        max_zones: int = 6,
    ) -> dict[str, Any]:
        rows = self._normalize_history(history)

        minimum_rows = max(40, (pivot_window * 2) + 10)
        if len(rows) < minimum_rows:
            raise ValueError(
                f"Not enough historical data. Need at least "
                f"{minimum_rows} observations."
            )

        if pivot_window < 1 or pivot_window > 20:
            raise ValueError("pivot_window must be between 1 and 20.")

        if min_touches < 1 or min_touches > 10:
            raise ValueError("min_touches must be between 1 and 10.")

        if max_zones < 2 or max_zones > 20:
            raise ValueError("max_zones must be between 2 and 20.")

        atr = self._atr(rows, period=14)
        current_price = float(rows[-1]["close"])

        pivots = self._detect_confirmed_pivots(
            rows=rows,
            pivot_window=pivot_window,
        )

        supports = [
            pivot for pivot in pivots
            if pivot.kind == "SUPPORT"
        ]
        resistances = [
            pivot for pivot in pivots
            if pivot.kind == "RESISTANCE"
        ]

        support_zones = self._build_zones(
            pivots=supports,
            rows=rows,
            current_price=current_price,
            atr=atr,
            zone_type="SUPPORT",
            min_touches=min_touches,
        )

        resistance_zones = self._build_zones(
            pivots=resistances,
            rows=rows,
            current_price=current_price,
            atr=atr,
            zone_type="RESISTANCE",
            min_touches=min_touches,
        )

        all_zones = support_zones + resistance_zones
        all_zones.sort(
            key=lambda zone: (
                zone["distance_pct"],
                -zone["strength"],
            )
        )

        nearest_support = self._nearest_zone(
            support_zones,
            current_price,
            direction="BELOW",
        )
        nearest_resistance = self._nearest_zone(
            resistance_zones,
            current_price,
            direction="ABOVE",
        )

        active_zone = next(
            (
                zone for zone in all_zones
                if zone["relation"] == "INSIDE"
            ),
            None,
        )

        return {
            "engine": "QMI Support & Resistance Engine",
            "engine_id": "DE-TA-006.1",
            "version": "0.1.0",
            "status": "operational",
            "observations": len(rows),
            "pivot_window": pivot_window,
            "min_touches": min_touches,
            "current_price": round(current_price, 6),
            "atr14": round(atr, 6),
            "summary": {
                "nearest_support": nearest_support,
                "nearest_resistance": nearest_resistance,
                "active_zone": active_zone,
                "support_count": len(support_zones),
                "resistance_count": len(resistance_zones),
            },
            "zones": all_zones[:max_zones],
            "support_zones": support_zones[:max_zones],
            "resistance_zones": resistance_zones[:max_zones],
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
                rows.append(
                    {
                        "date": str(date),
                        "high": float(high),
                        "low": float(low),
                        "close": float(close),
                    }
                )
            except (TypeError, ValueError):
                continue

        rows.sort(key=lambda row: row["date"])

        if not rows:
            raise ValueError("Historical market data is empty.")

        return rows

    def _atr(
        self,
        rows: list[dict[str, Any]],
        period: int = 14,
    ) -> float:
        true_ranges: list[float] = []

        previous_close: float | None = None

        for row in rows:
            high = row["high"]
            low = row["low"]

            if previous_close is None:
                tr = high - low
            else:
                tr = max(
                    high - low,
                    abs(high - previous_close),
                    abs(low - previous_close),
                )

            true_ranges.append(max(0.0, tr))
            previous_close = row["close"]

        window = true_ranges[-period:] if len(true_ranges) >= period else true_ranges

        atr = sum(window) / len(window)
        return max(atr, rows[-1]["close"] * 0.002)

    def _detect_confirmed_pivots(
        self,
        rows: list[dict[str, Any]],
        pivot_window: int,
    ) -> list[Pivot]:
        pivots: list[Pivot] = []

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
                future_lows = [
                    row["low"]
                    for row in rows[
                        index + 1:min(index + 6, len(rows))
                    ]
                ]
                reaction_pct = 0.0

                if future_lows:
                    reaction_pct = (
                        (
                            current["high"]
                            - min(future_lows)
                        )
                        / current["high"]
                        * 100
                    )

                pivots.append(
                    Pivot(
                        index=index,
                        date=current["date"],
                        price=current["high"],
                        kind="RESISTANCE",
                        reaction_pct=max(0.0, reaction_pct),
                    )
                )

            if current["low"] < min(surrounding_lows):
                future_highs = [
                    row["high"]
                    for row in rows[
                        index + 1:min(index + 6, len(rows))
                    ]
                ]
                reaction_pct = 0.0

                if future_highs:
                    reaction_pct = (
                        (
                            max(future_highs)
                            - current["low"]
                        )
                        / current["low"]
                        * 100
                    )

                pivots.append(
                    Pivot(
                        index=index,
                        date=current["date"],
                        price=current["low"],
                        kind="SUPPORT",
                        reaction_pct=max(0.0, reaction_pct),
                    )
                )

        return pivots

    def _build_zones(
        self,
        pivots: list[Pivot],
        rows: list[dict[str, Any]],
        current_price: float,
        atr: float,
        zone_type: str,
        min_touches: int,
    ) -> list[dict[str, Any]]:
        if not pivots:
            return []

        # Clustering tolerance adapts to both volatility and price.
        cluster_tolerance = max(
            atr * 0.75,
            current_price * 0.015,
        )

        sorted_pivots = sorted(
            pivots,
            key=lambda pivot: pivot.price,
        )

        clusters: list[list[Pivot]] = []

        for pivot in sorted_pivots:
            best_cluster: list[Pivot] | None = None
            best_distance: float | None = None

            for cluster in clusters:
                center = sum(
                    item.price for item in cluster
                ) / len(cluster)

                distance = abs(pivot.price - center)

                if distance <= cluster_tolerance:
                    if (
                        best_distance is None
                        or distance < best_distance
                    ):
                        best_cluster = cluster
                        best_distance = distance

            if best_cluster is None:
                clusters.append([pivot])
            else:
                best_cluster.append(pivot)

        zones: list[dict[str, Any]] = []

        for cluster in clusters:
            if len(cluster) < min_touches:
                continue

            prices = [pivot.price for pivot in cluster]
            center = sum(prices) / len(prices)

            # Zone thickness is deliberately narrower than cluster tolerance.
            half_width = max(
                atr * 0.35,
                center * 0.006,
            )

            lower = center - half_width
            upper = center + half_width

            last_touch = max(
                cluster,
                key=lambda pivot: pivot.index,
            )

            age_bars = max(
                0,
                (len(rows) - 1) - last_touch.index,
            )

            average_reaction = (
                sum(
                    pivot.reaction_pct
                    for pivot in cluster
                )
                / len(cluster)
            )

            touch_score = min(
                100.0,
                35.0 + (len(cluster) - 2) * 15.0,
            )

            if age_bars <= 10:
                recency_score = 100.0
            elif age_bars <= 25:
                recency_score = 85.0
            elif age_bars <= 50:
                recency_score = 65.0
            elif age_bars <= 90:
                recency_score = 45.0
            else:
                recency_score = 25.0

            reaction_score = min(
                100.0,
                average_reaction * 12.0,
            )

            dispersion = (
                (max(prices) - min(prices)) / center * 100
                if center
                else 0.0
            )
            compactness_score = max(
                20.0,
                100.0 - dispersion * 20.0,
            )

            strength = (
                touch_score * 0.35
                + recency_score * 0.25
                + reaction_score * 0.25
                + compactness_score * 0.15
            )
            strength = round(
                max(0.0, min(100.0, strength)),
                1,
            )

            if lower <= current_price <= upper:
                relation = "INSIDE"
                distance_pct = 0.0
            elif current_price < lower:
                relation = "ABOVE_PRICE"
                distance_pct = (
                    (lower - current_price)
                    / current_price
                    * 100
                )
            else:
                relation = "BELOW_PRICE"
                distance_pct = (
                    (current_price - upper)
                    / current_price
                    * 100
                )

            zones.append(
                {
                    "type": zone_type,
                    "center": round(center, 6),
                    "lower": round(lower, 6),
                    "upper": round(upper, 6),
                    "touches": len(cluster),
                    "strength": strength,
                    "quality": self._quality_label(strength),
                    "last_touch_date": last_touch.date,
                    "age_bars": age_bars,
                    "average_reaction_pct": round(
                        average_reaction,
                        2,
                    ),
                    "distance_pct": round(
                        max(0.0, distance_pct),
                        2,
                    ),
                    "relation": relation,
                    "pivot_dates": [
                        pivot.date for pivot in cluster[-6:]
                    ],
                }
            )

        zones.sort(
            key=lambda zone: (
                zone["distance_pct"],
                -zone["strength"],
            )
        )

        return zones

    def _nearest_zone(
        self,
        zones: list[dict[str, Any]],
        current_price: float,
        direction: str,
    ) -> dict[str, Any] | None:
        candidates: list[dict[str, Any]] = []

        for zone in zones:
            lower = float(zone["lower"])
            upper = float(zone["upper"])

            if lower <= current_price <= upper:
                candidates.append(zone)
                continue

            if direction == "BELOW" and upper < current_price:
                candidates.append(zone)

            if direction == "ABOVE" and lower > current_price:
                candidates.append(zone)

        if not candidates:
            return None

        return min(
            candidates,
            key=lambda zone: zone["distance_pct"],
        )

    @staticmethod
    def _quality_label(score: float) -> str:
        if score >= 85:
            return "VERY_HIGH"
        if score >= 70:
            return "HIGH"
        if score >= 55:
            return "MODERATE"
        if score >= 40:
            return "LOW"
        return "VERY_LOW"
