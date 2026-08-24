from __future__ import annotations

from typing import Any, Iterable

from app.services.technical.market_structure_service import (
    MarketStructureService,
    SwingPoint,
)


class LiquidityService:
    """
    DE-TA-007.6 — Liquidity Bias Engine

    Detects candidate institutional liquidity pools from confirmed swing
    highs/lows. Nearby highs are grouped as Buy-Side Liquidity (BSL);
    nearby lows are grouped as Sell-Side Liquidity (SSL).

    This first version deliberately does NOT classify sweeps. That belongs
    to DE-TA-007.3. The engine only identifies, ranks and contextualizes
    liquidity pools using confirmed market structure.
    """

    def __init__(self) -> None:
        self.structure_service = MarketStructureService()

    def analyze(
        self,
        history: Iterable[dict[str, Any]],
        pivot_window: int = 3,
        tolerance_pct: float = 0.60,
        min_touches: int = 2,
        max_pools: int = 8,
    ) -> dict[str, Any]:
        rows = self.structure_service._normalize_history(history)

        if not 0.05 <= tolerance_pct <= 5.0:
            raise ValueError("tolerance_pct must be between 0.05 and 5.0.")
        if not 2 <= min_touches <= 10:
            raise ValueError("min_touches must be between 2 and 10.")
        if not 2 <= max_pools <= 30:
            raise ValueError("max_pools must be between 2 and 30.")

        swings = self.structure_service._detect_swings(
            rows=rows,
            pivot_window=pivot_window,
        )
        classified = self.structure_service._classify_swings(swings)

        highs = [p for p in classified if p.kind == "SWING_HIGH"]
        lows = [p for p in classified if p.kind == "SWING_LOW"]

        bsl = self._cluster_points(
            points=highs,
            pool_type="BSL",
            tolerance_pct=tolerance_pct,
            min_touches=min_touches,
            current_index=len(rows) - 1,
            current_price=float(rows[-1]["close"]),
        )
        ssl = self._cluster_points(
            points=lows,
            pool_type="SSL",
            tolerance_pct=tolerance_pct,
            min_touches=min_touches,
            current_index=len(rows) - 1,
            current_price=float(rows[-1]["close"]),
        )

        pools = sorted(
            bsl + ssl,
            key=lambda item: (
                item["status"] != "ACTIVE",
                -item["score"],
                item["distance_pct"],
            ),
        )[:max_pools]

        sweeps = self._detect_sweeps(
            rows=rows,
            pools=pools,
        )

        validated_sweeps = self._validate_sweeps(
            sweeps=sweeps,
            pools=pools,
            current_index=len(rows) - 1,
        )

        institutional_sweeps = [
            sweep
            for sweep in validated_sweeps
            if sweep["institutional_status"] in {
                "CONFIRMED",
                "HIGH_CONVICTION",
            }
        ]

        sweep_clusters = self._cluster_institutional_sweeps(
            institutional_sweeps=institutional_sweeps,
        )

        current_price = float(rows[-1]["close"])

        sweep_clusters = self._evaluate_cluster_states(
            rows=rows,
            clusters=sweep_clusters,
            current_price=current_price,
        )

        active_clusters = [
            cluster
            for cluster in sweep_clusters
            if cluster["state"] in {"ACTIVE", "TESTED"}
        ]

        dominant_cluster = (
            max(
                sweep_clusters,
                key=lambda cluster: (
                    cluster["cluster_score"],
                    cluster["event_count"],
                ),
            )
            if sweep_clusters
            else None
        )

        dominant_active_cluster = (
            max(
                active_clusters,
                key=lambda cluster: (
                    cluster["decision_relevance"],
                    cluster["cluster_score"],
                ),
            )
            if active_clusters
            else None
        )

        nearest_active_cluster = (
            min(
                active_clusters,
                key=lambda cluster: cluster["distance_pct"],
            )
            if active_clusters
            else None
        )

        liquidity_bias = self._calculate_liquidity_bias(
            active_clusters=active_clusters,
            institutional_sweeps=institutional_sweeps,
            pools=pools,
            current_price=current_price,
            current_index=len(rows) - 1,
        )

        latest_sweep = (
            validated_sweeps[-1]
            if validated_sweeps
            else None
        )
        latest_institutional_sweep = (
            institutional_sweeps[-1]
            if institutional_sweeps
            else None
        )

        active_bsl = [
            p for p in pools
            if p["type"] == "BSL" and p["status"] == "ACTIVE"
        ]
        active_ssl = [
            p for p in pools
            if p["type"] == "SSL" and p["status"] == "ACTIVE"
        ]

        nearest_bsl = min(
            active_bsl,
            key=lambda p: p["distance_pct"],
            default=None,
        )
        nearest_ssl = min(
            active_ssl,
            key=lambda p: p["distance_pct"],
            default=None,
        )

        dominant = None
        if nearest_bsl and nearest_ssl:
            dominant = (
                "BSL"
                if nearest_bsl["distance_pct"] < nearest_ssl["distance_pct"]
                else "SSL"
            )
        elif nearest_bsl:
            dominant = "BSL"
        elif nearest_ssl:
            dominant = "SSL"

        return {
            "engine": "QMI Liquidity Engine",
            "engine_id": "DE-TA-007.6",
            "version": "0.6.0",
            "status": "operational",
            "observations": len(rows),
            "current_price": round(current_price, 6),
            "pivot_window": pivot_window,
            "tolerance_pct": tolerance_pct,
            "min_touches": min_touches,
            "summary": {
                "detected_pools": len(pools),
                "active_bsl": len(active_bsl),
                "active_ssl": len(active_ssl),
                "dominant_nearest_side": dominant,
                "nearest_bsl": nearest_bsl,
                "nearest_ssl": nearest_ssl,
                "sweep_count": len(validated_sweeps),
                "institutional_sweep_count": len(
                    institutional_sweeps
                ),
                "sweep_cluster_count": len(sweep_clusters),
                "active_cluster_count": len(active_clusters),
                "latest_sweep": latest_sweep,
                "latest_institutional_sweep": (
                    latest_institutional_sweep
                ),
                "dominant_sweep_cluster": dominant_cluster,
                "dominant_active_cluster": dominant_active_cluster,
                "nearest_active_cluster": nearest_active_cluster,
                "liquidity_bias": liquidity_bias,
            },
            "latest_sweep": latest_sweep,
            "latest_institutional_sweep": (
                latest_institutional_sweep
            ),
            "dominant_sweep_cluster": dominant_cluster,
            "dominant_active_cluster": dominant_active_cluster,
            "nearest_active_cluster": nearest_active_cluster,
            "liquidity_bias": liquidity_bias,
            "active_sweep_clusters": active_clusters,
            "sweep_clusters": sweep_clusters,
            "sweeps": validated_sweeps[-20:],
            "institutional_sweeps": institutional_sweeps[-10:],
            "pools": pools,
        }

    def _detect_sweeps(
        self,
        rows: list[dict[str, Any]],
        pools: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        sweeps: list[dict[str, Any]] = []

        for index, row in enumerate(rows):
            high = float(row["high"])
            low = float(row["low"])
            close = float(row["close"])

            for pool in pools:
                lower = float(pool["lower"])
                upper = float(pool["upper"])
                center = float(pool["center"])

                if pool["type"] == "BSL":
                    if high > upper and close < upper:
                        penetration_pct = ((high - upper) / upper * 100) if upper else 0.0
                        rejection_pct = ((high - close) / high * 100) if high else 0.0
                        score = self._sweep_score(
                            pool_score=float(pool["score"]),
                            penetration_pct=penetration_pct,
                            rejection_pct=rejection_pct,
                        )
                        sweeps.append({
                            "index": index,
                            "date": row["date"],
                            "type": "BSL_SWEEP",
                            "directional_implication": "BEARISH",
                            "pool_type": "BSL",
                            "pool_center": round(center, 6),
                            "pool_lower": round(lower, 6),
                            "pool_upper": round(upper, 6),
                            "extreme_price": round(high, 6),
                            "close_price": round(close, 6),
                            "penetration_pct": round(penetration_pct, 3),
                            "rejection_pct": round(rejection_pct, 3),
                            "score": score,
                            "quality": self._quality_label(score),
                            "confirmation": "WICK_ABOVE_CLOSE_BACK_BELOW",
                        })

                elif pool["type"] == "SSL":
                    if low < lower and close > lower:
                        penetration_pct = ((lower - low) / lower * 100) if lower else 0.0
                        rejection_pct = ((close - low) / close * 100) if close else 0.0
                        score = self._sweep_score(
                            pool_score=float(pool["score"]),
                            penetration_pct=penetration_pct,
                            rejection_pct=rejection_pct,
                        )
                        sweeps.append({
                            "index": index,
                            "date": row["date"],
                            "type": "SSL_SWEEP",
                            "directional_implication": "BULLISH",
                            "pool_type": "SSL",
                            "pool_center": round(center, 6),
                            "pool_lower": round(lower, 6),
                            "pool_upper": round(upper, 6),
                            "extreme_price": round(low, 6),
                            "close_price": round(close, 6),
                            "penetration_pct": round(penetration_pct, 3),
                            "rejection_pct": round(rejection_pct, 3),
                            "score": score,
                            "quality": self._quality_label(score),
                            "confirmation": "WICK_BELOW_CLOSE_BACK_ABOVE",
                        })

        deduplicated: list[dict[str, Any]] = []
        seen: set[tuple[str, str, int]] = set()

        for sweep in sorted(
            sweeps,
            key=lambda item: (
                item["index"],
                item["pool_type"],
                -item["score"],
            ),
        ):
            bucket = round(float(sweep["pool_center"]) * 20)
            key = (sweep["date"], sweep["pool_type"], bucket)

            if key in seen:
                continue

            seen.add(key)
            deduplicated.append(sweep)

        return deduplicated

    def _cluster_institutional_sweeps(
        self,
        institutional_sweeps: list[dict[str, Any]],
        price_tolerance_pct: float = 2.25,
        max_bar_gap: int = 18,
    ) -> list[dict[str, Any]]:
        """
        Groups institutionally validated sweeps that belong to the same
        liquidity battle.

        Two sweeps can join the same cluster when:
        - they are the same pool type (BSL or SSL),
        - their pool centers are spatially close,
        - and their events occur within a limited bar gap.

        Clustering prevents the Decision Engine from over-counting repeated
        sweeps around the same price area.
        """
        if not institutional_sweeps:
            return []

        ordered = sorted(
            institutional_sweeps,
            key=lambda sweep: (
                sweep["pool_type"],
                int(sweep.get("index", 0)),
                float(sweep.get("pool_center", 0.0)),
            ),
        )

        clusters: list[list[dict[str, Any]]] = []

        for sweep in ordered:
            best_cluster = None
            best_distance = None

            for cluster in clusters:
                if cluster[0]["pool_type"] != sweep["pool_type"]:
                    continue

                center = sum(
                    float(item["pool_center"])
                    for item in cluster
                ) / len(cluster)

                price_distance_pct = (
                    abs(float(sweep["pool_center"]) - center)
                    / center
                    * 100
                    if center
                    else 999.0
                )

                last_index = max(
                    int(item.get("index", 0))
                    for item in cluster
                )
                bar_gap = abs(
                    int(sweep.get("index", 0)) - last_index
                )

                if (
                    price_distance_pct <= price_tolerance_pct
                    and bar_gap <= max_bar_gap
                ):
                    if (
                        best_distance is None
                        or price_distance_pct < best_distance
                    ):
                        best_cluster = cluster
                        best_distance = price_distance_pct

            if best_cluster is None:
                clusters.append([sweep])
            else:
                best_cluster.append(sweep)

        results: list[dict[str, Any]] = []

        for cluster_index, cluster in enumerate(clusters, start=1):
            cluster = sorted(
                cluster,
                key=lambda sweep: int(sweep.get("index", 0)),
            )

            centers = [
                float(sweep["pool_center"])
                for sweep in cluster
            ]
            lows = [
                float(sweep["pool_lower"])
                for sweep in cluster
            ]
            highs = [
                float(sweep["pool_upper"])
                for sweep in cluster
            ]
            scores = [
                float(
                    sweep.get(
                        "institutional_score",
                        sweep.get("score", 0.0),
                    )
                )
                for sweep in cluster
            ]

            center = sum(centers) / len(centers)
            lower = min(lows)
            upper = max(highs)

            weighted_score = (
                sum(
                    score * (1.0 + 0.08 * index)
                    for index, score in enumerate(scores)
                )
                / sum(
                    1.0 + 0.08 * index
                    for index in range(len(scores))
                )
            )

            repetition_bonus = min(
                12.0,
                max(0, len(cluster) - 1) * 3.0,
            )

            high_conviction_count = sum(
                1
                for sweep in cluster
                if sweep.get("institutional_status")
                == "HIGH_CONVICTION"
            )

            conviction_bonus = min(
                8.0,
                high_conviction_count * 2.0,
            )

            cluster_score = round(
                max(
                    0.0,
                    min(
                        100.0,
                        weighted_score
                        + repetition_bonus
                        + conviction_bonus,
                    ),
                ),
                1,
            )

            if cluster_score >= 88:
                cluster_quality = "VERY_HIGH"
            elif cluster_score >= 78:
                cluster_quality = "HIGH"
            elif cluster_score >= 68:
                cluster_quality = "MODERATE"
            else:
                cluster_quality = "LOW"

            dominant_event = max(
                cluster,
                key=lambda sweep: float(
                    sweep.get(
                        "institutional_score",
                        sweep.get("score", 0.0),
                    )
                ),
            )

            results.append({
                "cluster_id": (
                    f"{cluster[0]['pool_type']}-"
                    f"{cluster_index:02d}"
                ),
                "type": cluster[0]["pool_type"],
                "side": (
                    "BUY_SIDE_LIQUIDITY"
                    if cluster[0]["pool_type"] == "BSL"
                    else "SELL_SIDE_LIQUIDITY"
                ),
                "directional_implication": (
                    "BEARISH"
                    if cluster[0]["pool_type"] == "BSL"
                    else "BULLISH"
                ),
                "center": round(center, 6),
                "lower": round(lower, 6),
                "upper": round(upper, 6),
                "event_count": len(cluster),
                "first_event_date": cluster[0]["date"],
                "last_event_date": cluster[-1]["date"],
                "first_index": int(cluster[0].get("index", 0)),
                "last_index": int(cluster[-1].get("index", 0)),
                "high_conviction_count": high_conviction_count,
                "cluster_score": cluster_score,
                "cluster_quality": cluster_quality,
                "dominant_event": dominant_event,
                "events": cluster,
            })

        results.sort(
            key=lambda cluster: (
                cluster["last_index"],
                cluster["cluster_score"],
            )
        )

        return results

    def _evaluate_cluster_states(
        self,
        rows: list[dict[str, Any]],
        clusters: list[dict[str, Any]],
        current_price: float,
    ) -> list[dict[str, Any]]:
        """
        Adds lifecycle and decision context to each sweep cluster.

        ACTIVE:
            cluster remains structurally available and has not been
            decisively closed through after its last sweep.

        TESTED:
            price is currently inside / immediately adjacent to the cluster.

        CONSUMED:
            after the cluster's final sweep, price later closed decisively
            beyond the cluster in the liquidity direction.

        STALE:
            still technically available, but the last event is old enough
            to reduce decision relevance.
        """
        evaluated: list[dict[str, Any]] = []
        current_index = len(rows) - 1

        for cluster in clusters:
            lower = float(cluster["lower"])
            upper = float(cluster["upper"])
            center = float(cluster["center"])
            last_index = int(cluster.get("last_index", 0))
            cluster_type = str(cluster["type"])

            post_rows = rows[min(last_index + 1, len(rows)):]

            consumed = False
            consumed_date = None
            consumed_close = None

            for row in post_rows:
                close = float(row["close"])

                if cluster_type == "BSL":
                    # BSL is considered consumed only after a close above
                    # the entire cluster, not by a wick/sweep.
                    if close > upper:
                        consumed = True
                        consumed_date = row["date"]
                        consumed_close = close
                        break
                else:
                    # SSL consumed by a decisive close below the cluster.
                    if close < lower:
                        consumed = True
                        consumed_date = row["date"]
                        consumed_close = close
                        break

            if lower <= current_price <= upper:
                relation = "INSIDE"
                distance_pct = 0.0
            elif current_price < lower:
                relation = "ABOVE_PRICE"
                distance_pct = (
                    (lower - current_price) / current_price * 100
                    if current_price else 0.0
                )
            else:
                relation = "BELOW_PRICE"
                distance_pct = (
                    (current_price - upper) / current_price * 100
                    if current_price else 0.0
                )

            age_bars = max(0, current_index - last_index)

            if consumed:
                state = "CONSUMED"
            elif relation == "INSIDE" or distance_pct <= 1.0:
                state = "TESTED"
            elif age_bars > 90:
                state = "STALE"
            else:
                state = "ACTIVE"

            proximity_score = (
                100.0 if distance_pct <= 1.0
                else 90.0 if distance_pct <= 3.0
                else 75.0 if distance_pct <= 6.0
                else 55.0 if distance_pct <= 12.0
                else 35.0
            )

            recency_score = (
                100.0 if age_bars <= 10
                else 85.0 if age_bars <= 25
                else 70.0 if age_bars <= 50
                else 50.0 if age_bars <= 90
                else 30.0
            )

            state_multiplier = (
                1.00 if state == "TESTED"
                else 0.92 if state == "ACTIVE"
                else 0.55 if state == "STALE"
                else 0.20
            )

            decision_relevance = (
                float(cluster["cluster_score"]) * 0.60
                + proximity_score * 0.25
                + recency_score * 0.15
            ) * state_multiplier

            decision_relevance = round(
                max(0.0, min(100.0, decision_relevance)),
                1,
            )

            evaluated.append({
                **cluster,
                "state": state,
                "relation": relation,
                "distance_pct": round(distance_pct, 2),
                "age_bars": age_bars,
                "decision_relevance": decision_relevance,
                "consumed_date": consumed_date,
                "consumed_close": (
                    round(consumed_close, 6)
                    if consumed_close is not None
                    else None
                ),
            })

        return evaluated

    def _calculate_liquidity_bias(
        self,
        active_clusters: list[dict[str, Any]],
        institutional_sweeps: list[dict[str, Any]],
        pools: list[dict[str, Any]],
        current_price: float,
        current_index: int,
    ) -> dict[str, Any]:
        """
        Aggregates liquidity context into a -100..+100 bias score.

        Positive:
            stronger bullish / SSL reversal context.

        Negative:
            stronger bearish / BSL rejection context.

        This is contextual evidence for the future Decision Engine,
        not a standalone BUY/SELL recommendation.
        """

        def distance_weight(distance_pct: float) -> float:
            d = max(0.25, float(distance_pct))
            if d <= 1:
                return 1.60
            if d <= 3:
                return 1.35
            if d <= 6:
                return 1.10
            if d <= 12:
                return 0.85
            return 0.60

        def recency_weight(age_bars: int) -> float:
            age = max(0, int(age_bars))
            if age <= 10:
                return 1.25
            if age <= 25:
                return 1.10
            if age <= 50:
                return 0.90
            if age <= 90:
                return 0.70
            return 0.50

        # 1) ACTIVE / TESTED CLUSTER PRESSURE
        cluster_bsl = 0.0
        cluster_ssl = 0.0

        for cluster in active_clusters:
            relevance = float(cluster.get("decision_relevance", 0.0))
            distance = float(cluster.get("distance_pct", 999.0))
            age = int(cluster.get("age_bars", 999))

            contribution = (
                relevance
                * distance_weight(distance)
                * recency_weight(age)
            )

            if cluster.get("type") == "BSL":
                cluster_bsl += contribution
            elif cluster.get("type") == "SSL":
                cluster_ssl += contribution

        # 2) ACTIVE POOL PRESSURE
        pool_bsl = 0.0
        pool_ssl = 0.0

        active_bsl_pools = 0
        active_ssl_pools = 0

        for pool in pools:
            if pool.get("status") != "ACTIVE":
                continue

            score = float(pool.get("score", 0.0))
            distance = float(pool.get("distance_pct", 999.0))
            age = int(pool.get("age_bars", 999))

            contribution = (
                score
                * distance_weight(distance)
                * recency_weight(age)
            )

            if pool.get("type") == "BSL":
                pool_bsl += contribution
                active_bsl_pools += 1
            elif pool.get("type") == "SSL":
                pool_ssl += contribution
                active_ssl_pools += 1

        # 3) RECENT INSTITUTIONAL SWEEP PRESSURE
        sweep_bearish = 0.0
        sweep_bullish = 0.0
        recent_bsl_sweeps = 0
        recent_ssl_sweeps = 0

        for sweep in institutional_sweeps:
            event_age = max(
                0,
                current_index - int(sweep.get("index", current_index)),
            )

            # Only sweeps in the last ~60 bars meaningfully influence bias.
            if event_age > 60:
                continue

            score = float(
                sweep.get(
                    "institutional_score",
                    sweep.get("score", 0.0),
                )
            )

            contribution = score * recency_weight(event_age)

            if sweep.get("directional_implication") == "BEARISH":
                sweep_bearish += contribution
                if sweep.get("pool_type") == "BSL":
                    recent_bsl_sweeps += 1
            elif sweep.get("directional_implication") == "BULLISH":
                sweep_bullish += contribution
                if sweep.get("pool_type") == "SSL":
                    recent_ssl_sweeps += 1

        # 4) AGGREGATE SIDES
        #
        # BSL pressure is bearish context:
        # overhead liquidity + bearish BSL sweeps.
        #
        # SSL pressure is bullish context:
        # downside liquidity + bullish SSL sweeps.
        bearish_pressure = (
            cluster_bsl * 0.45
            + pool_bsl * 0.20
            + sweep_bearish * 0.35
        )

        bullish_pressure = (
            cluster_ssl * 0.45
            + pool_ssl * 0.20
            + sweep_bullish * 0.35
        )

        total_pressure = bearish_pressure + bullish_pressure

        if total_pressure <= 0:
            score = 0.0
            confidence = 0.0
        else:
            score = (
                (bullish_pressure - bearish_pressure)
                / total_pressure
                * 100.0
            )

            # Confidence rises with pressure magnitude and agreement.
            agreement = abs(bullish_pressure - bearish_pressure) / total_pressure
            magnitude = min(1.0, total_pressure / 250.0)

            confidence = (
                agreement * 70.0
                + magnitude * 30.0
            )

        score = round(max(-100.0, min(100.0, score)), 1)
        confidence = round(max(0.0, min(100.0, confidence)), 1)

        if score >= 65:
            state = "STRONG_BULLISH"
        elif score >= 30:
            state = "BULLISH"
        elif score <= -65:
            state = "STRONG_BEARISH"
        elif score <= -30:
            state = "BEARISH"
        else:
            state = "BALANCED"

        dominant_liquidity = (
            "SELL_SIDE"
            if bullish_pressure > bearish_pressure
            else "BUY_SIDE"
            if bearish_pressure > bullish_pressure
            else "BALANCED"
        )

        if state in {"STRONG_BEARISH", "BEARISH"}:
            interpretation = (
                "Overhead buy-side liquidity and bearish liquidity-sweep "
                "context dominate the current market structure."
            )
        elif state in {"STRONG_BULLISH", "BULLISH"}:
            interpretation = (
                "Downside sell-side liquidity and bullish liquidity-sweep "
                "context dominate the current market structure."
            )
        else:
            interpretation = (
                "Liquidity pressure is balanced; neither BSL rejection nor "
                "SSL reversal context is clearly dominant."
            )

        return {
            "score": score,
            "state": state,
            "confidence": confidence,
            "dominant_liquidity": dominant_liquidity,
            "bearish_pressure": round(bearish_pressure, 1),
            "bullish_pressure": round(bullish_pressure, 1),
            "components": {
                "cluster_bsl_pressure": round(cluster_bsl, 1),
                "cluster_ssl_pressure": round(cluster_ssl, 1),
                "pool_bsl_pressure": round(pool_bsl, 1),
                "pool_ssl_pressure": round(pool_ssl, 1),
                "bearish_sweep_pressure": round(sweep_bearish, 1),
                "bullish_sweep_pressure": round(sweep_bullish, 1),
            },
            "counts": {
                "active_bsl_pools": active_bsl_pools,
                "active_ssl_pools": active_ssl_pools,
                "recent_bsl_sweeps": recent_bsl_sweeps,
                "recent_ssl_sweeps": recent_ssl_sweeps,
                "active_bsl_clusters": sum(
                    1 for cluster in active_clusters
                    if cluster.get("type") == "BSL"
                ),
                "active_ssl_clusters": sum(
                    1 for cluster in active_clusters
                    if cluster.get("type") == "SSL"
                ),
            },
            "interpretation": interpretation,
            "disclaimer": (
                "Liquidity bias is contextual evidence for QMI's Decision "
                "Engine and is not a standalone trading signal."
            ),
        }

    def _validate_sweeps(
        self,
        sweeps: list[dict[str, Any]],
        pools: list[dict[str, Any]],
        current_index: int,
    ) -> list[dict[str, Any]]:
        """
        Adds institutional validation without deleting raw detections.

        Institutional validation considers:
        - underlying pool quality
        - pool touch count
        - sweep rejection
        - penetration quality
        - pool recency
        - event recency
        - raw sweep score

        Status:
        HIGH_CONVICTION >= 82
        CONFIRMED       >= 70
        WATCH           >= 58
        NOISE           < 58
        """
        pool_lookup: dict[tuple[str, float], dict[str, Any]] = {}

        for pool in pools:
            key = (
                str(pool["type"]),
                round(float(pool["center"]), 3),
            )
            pool_lookup[key] = pool

        validated: list[dict[str, Any]] = []

        for sweep in sweeps:
            pool_key = (
                str(sweep["pool_type"]),
                round(float(sweep["pool_center"]), 3),
            )
            pool = pool_lookup.get(pool_key, {})

            raw_score = float(sweep.get("score", 0.0))
            pool_score = float(pool.get("score", 50.0))
            touches = int(pool.get("touches", 2))
            pool_age = int(pool.get("age_bars", 999))
            event_age = max(
                0,
                current_index - int(sweep.get("index", current_index)),
            )
            penetration = float(
                sweep.get("penetration_pct", 0.0)
            )
            rejection = float(
                sweep.get("rejection_pct", 0.0)
            )

            touch_quality = min(
                100.0,
                45.0 + max(0, touches - 2) * 14.0,
            )

            # Ideal penetration: enough to take liquidity,
            # but not so deep that it resembles a true breakout.
            if 0.10 <= penetration <= 1.50:
                penetration_quality = 100.0
            elif penetration <= 3.00:
                penetration_quality = 82.0
            elif penetration <= 5.00:
                penetration_quality = 60.0
            else:
                penetration_quality = 35.0

            rejection_quality = min(
                100.0,
                30.0 + rejection * 20.0,
            )

            pool_recency = (
                100.0 if pool_age <= 15
                else 85.0 if pool_age <= 35
                else 65.0 if pool_age <= 60
                else 45.0 if pool_age <= 100
                else 25.0
            )

            event_recency = (
                100.0 if event_age <= 10
                else 85.0 if event_age <= 25
                else 65.0 if event_age <= 50
                else 45.0 if event_age <= 90
                else 25.0
            )

            institutional_score = (
                raw_score * 0.25
                + pool_score * 0.20
                + touch_quality * 0.15
                + penetration_quality * 0.15
                + rejection_quality * 0.15
                + pool_recency * 0.05
                + event_recency * 0.05
            )
            institutional_score = round(
                max(
                    0.0,
                    min(100.0, institutional_score),
                ),
                1,
            )

            if institutional_score >= 82:
                institutional_status = "HIGH_CONVICTION"
            elif institutional_score >= 70:
                institutional_status = "CONFIRMED"
            elif institutional_score >= 58:
                institutional_status = "WATCH"
            else:
                institutional_status = "NOISE"

            validated.append({
                **sweep,
                "institutional_score": institutional_score,
                "institutional_status": institutional_status,
                "display_priority": (
                    3 if institutional_status == "HIGH_CONVICTION"
                    else 2 if institutional_status == "CONFIRMED"
                    else 1 if institutional_status == "WATCH"
                    else 0
                ),
                "validation": {
                    "raw_sweep_score": round(raw_score, 1),
                    "pool_score": round(pool_score, 1),
                    "touch_quality": round(touch_quality, 1),
                    "penetration_quality": round(
                        penetration_quality,
                        1,
                    ),
                    "rejection_quality": round(
                        rejection_quality,
                        1,
                    ),
                    "pool_recency": round(pool_recency, 1),
                    "event_recency": round(event_recency, 1),
                    "touches": touches,
                    "pool_age_bars": pool_age,
                    "event_age_bars": event_age,
                },
            })

        return validated

    def _sweep_score(
        self,
        pool_score: float,
        penetration_pct: float,
        rejection_pct: float,
    ) -> float:
        penetration_score = (
            100.0 if 0.10 <= penetration_pct <= 1.50
            else 80.0 if penetration_pct <= 3.0
            else 55.0 if penetration_pct <= 5.0
            else 35.0
        )

        rejection_score = min(
            100.0,
            40.0 + rejection_pct * 18.0,
        )

        score = (
            pool_score * 0.45
            + penetration_score * 0.25
            + rejection_score * 0.30
        )

        return round(max(0.0, min(100.0, score)), 1)

    @staticmethod
    def _quality_label(score: float) -> str:
        if score >= 85:
            return "VERY_HIGH"
        if score >= 70:
            return "HIGH"
        if score >= 55:
            return "MODERATE"
        return "LOW"

    def _cluster_points(
        self,
        points: list[SwingPoint],
        pool_type: str,
        tolerance_pct: float,
        min_touches: int,
        current_index: int,
        current_price: float,
    ) -> list[dict[str, Any]]:
        if len(points) < min_touches:
            return []

        clusters: list[list[SwingPoint]] = []

        for point in points:
            best_cluster = None
            best_distance = None

            for cluster in clusters:
                center = sum(p.price for p in cluster) / len(cluster)
                distance_pct = (
                    abs(point.price - center) / center * 100
                    if center else 999.0
                )
                if distance_pct <= tolerance_pct:
                    if best_distance is None or distance_pct < best_distance:
                        best_cluster = cluster
                        best_distance = distance_pct

            if best_cluster is None:
                clusters.append([point])
            else:
                best_cluster.append(point)

        qualifying = [
            cluster for cluster in clusters
            if len(cluster) >= min_touches
        ]

        results: list[dict[str, Any]] = []
        for cluster in qualifying:
            cluster = sorted(cluster, key=lambda p: p.index)
            prices = [float(p.price) for p in cluster]
            center = sum(prices) / len(prices)
            lower = min(prices)
            upper = max(prices)
            last_touch = cluster[-1]
            age_bars = max(0, current_index - last_touch.index)
            distance_pct = (
                abs(center - current_price) / current_price * 100
                if current_price else 0.0
            )

            if pool_type == "BSL":
                status = "ACTIVE" if current_price < lower else "TRAVERSED"
                relation = "ABOVE_PRICE" if center > current_price else "BELOW_PRICE"
            else:
                status = "ACTIVE" if current_price > upper else "TRAVERSED"
                relation = "BELOW_PRICE" if center < current_price else "ABOVE_PRICE"

            dispersion_pct = (
                (upper - lower) / center * 100
                if center else 0.0
            )

            touch_score = min(100.0, 45.0 + len(cluster) * 12.0)
            precision_score = max(
                20.0,
                100.0 - (dispersion_pct / max(tolerance_pct, 0.01)) * 55.0,
            )
            recency_score = (
                100.0 if age_bars <= 10
                else 85.0 if age_bars <= 25
                else 70.0 if age_bars <= 50
                else 50.0 if age_bars <= 90
                else 30.0
            )
            proximity_score = (
                100.0 if distance_pct <= 2
                else 90.0 if distance_pct <= 5
                else 75.0 if distance_pct <= 10
                else 55.0 if distance_pct <= 20
                else 35.0
            )

            score = (
                touch_score * 0.35
                + precision_score * 0.30
                + recency_score * 0.20
                + proximity_score * 0.15
            )
            if status != "ACTIVE":
                score *= 0.55

            score = round(max(0.0, min(100.0, score)), 1)
            quality = (
                "VERY_HIGH" if score >= 85
                else "HIGH" if score >= 70
                else "MODERATE" if score >= 55
                else "LOW"
            )

            results.append({
                "type": pool_type,
                "side": (
                    "BUY_SIDE_LIQUIDITY"
                    if pool_type == "BSL"
                    else "SELL_SIDE_LIQUIDITY"
                ),
                "center": round(center, 6),
                "lower": round(lower, 6),
                "upper": round(upper, 6),
                "touches": len(cluster),
                "first_touch_date": cluster[0].date,
                "last_touch_date": last_touch.date,
                "age_bars": age_bars,
                "distance_pct": round(distance_pct, 2),
                "dispersion_pct": round(dispersion_pct, 3),
                "relation": relation,
                "status": status,
                "score": score,
                "quality": quality,
                "source_swings": [
                    {
                        "date": p.date,
                        "price": round(float(p.price), 6),
                        "label": p.label,
                        "index": p.index,
                    }
                    for p in cluster
                ],
            })

        return results
